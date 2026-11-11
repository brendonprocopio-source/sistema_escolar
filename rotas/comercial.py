"""Matrículas e financeiro (parcelas)."""
import calendar
import sqlite3
from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request

import auth
from db import executar, get_db, recalcular_financeiro, todos, um, valor

bp = Blueprint("comercial", __name__)
METODOS = ["Pix", "Dinheiro", "Cartão de débito", "Cartão de crédito", "Boleto", "Transferência"]
POR_PAGINA = 30


def somar_meses(d, meses):
    """Mesma data n meses depois (31/01 + 1 mês = 28 ou 29/02)."""
    m = d.month - 1 + meses
    ano, mes = d.year + m // 12, m % 12 + 1
    return date(ano, mes, min(d.day, calendar.monthrange(ano, mes)[1]))


def gerar_parcelas(financeiro_id, total, quantidade, primeiro_vencimento):
    """Divide em parcelas iguais; a última absorve os centavos da divisão."""
    base = round(total / quantidade, 2)
    for i in range(quantidade):
        v = base if i < quantidade - 1 else round(total - base * (quantidade - 1), 2)
        executar(
            """INSERT INTO parcelas (financeiro_id, numero_parcela, valor_parcela, data_vencimento, status)
               VALUES (?, ?, ?, ?, 'pendente')""",
            (financeiro_id, i + 1, v, somar_meses(primeiro_vencimento, i).isoformat()))


# ---------------------------------------------------------------- matrículas
@bp.route("/matriculas")
@auth.exige(*auth.GESTAO)
def matriculas():
    q = request.args.get("q", "").strip()
    linhas = todos(
        """SELECT m.*, a.nome AS aluno, t.nome AS turma, f.valor_total, f.valor_pago, f.status AS fin_status
           FROM matriculas m JOIN alunos a ON a.id = m.aluno_id JOIN turmas t ON t.id = m.turma_id
           LEFT JOIN financeiro f ON f.id = (SELECT MAX(id) FROM financeiro WHERE matricula_id = m.id)
           WHERE a.nome LIKE ? OR t.nome LIKE ?
           ORDER BY m.data_matricula DESC, m.id DESC LIMIT 200""", (f"%{q}%", f"%{q}%"))
    return render_template("comercial/matriculas.html", linhas=linhas, q=q)


@bp.route("/matriculas/nova", methods=["GET", "POST"])
@auth.exige(*auth.GESTAO)
def nova_matricula():
    f = request.form
    if request.method == "POST":
        aluno_id = turma_id = qtd = 0
        total = None
        try:
            aluno_id, turma_id = int(f.get("aluno_id") or 0), int(f.get("turma_id") or 0)
            total = round(float(f.get("valor_total", "").replace(",", ".")), 2)
            qtd = int(f.get("parcelas") or 1)
            vencimento = date.fromisoformat(f.get("vencimento", ""))
        except ValueError:
            total = None
        turma = total is not None and um("SELECT * FROM turmas WHERE id = ? AND ativa = 1", (turma_id,))
        erro = None
        if total is None or total < 0 or not 1 <= qtd <= 36:
            erro = "Confira o valor, o número de parcelas (1 a 36) e a data do primeiro vencimento."
        elif not turma or not um("SELECT 1 FROM alunos WHERE id = ? AND ativo = 1", (aluno_id,)):
            erro = "Escolha um aluno e uma turma ativos."
        else:
            existente = um("SELECT * FROM matriculas WHERE aluno_id = ? AND turma_id = ?", (aluno_id, turma_id))
            ocupadas = valor("SELECT COUNT(*) FROM matriculas WHERE turma_id = ? AND status = 'ativa'", (turma_id,))
            if existente and existente["status"] == "ativa":
                erro = "Este aluno já está matriculado nesta turma."
            elif turma["capacidade"] and ocupadas >= turma["capacidade"]:
                erro = f"A turma está lotada ({ocupadas} de {turma['capacidade']} vagas)."
        if erro:
            flash(erro, "error")
        else:
            if existente:                       # matrícula cancelada antes: reativa
                matricula_id = existente["id"]
                executar("UPDATE matriculas SET status = 'ativa', data_matricula = date('now', 'localtime'), data_conclusao = NULL WHERE id = ?",
                         (matricula_id,))
            else:
                matricula_id = executar(
                    "INSERT INTO matriculas (aluno_id, turma_id, data_matricula, status) VALUES (?, ?, date('now', 'localtime'), 'ativa')",
                    (aluno_id, turma_id))
            if total > 0:
                fin_id = executar(
                    """INSERT INTO financeiro (matricula_id, valor_total, data_vencimento, parcelas, descricao)
                       VALUES (?, ?, ?, ?, ?)""",
                    (matricula_id, total, vencimento.isoformat(), qtd, f"Matrícula — {turma['nome']}"))
                gerar_parcelas(fin_id, total, qtd, vencimento)
                recalcular_financeiro(get_db(), fin_id)
            atual = valor("SELECT status FROM status_aluno WHERE aluno_id = ? ORDER BY id DESC LIMIT 1", (aluno_id,), "")
            if atual in ("", "Não iniciou", "Não Iniciou"):
                executar("INSERT INTO status_aluno (aluno_id, status, motivo, data_atualizacao) "
                         "VALUES (?, 'Frequente', 'Matrícula', date('now', 'localtime'))", (aluno_id,))
            auth.auditar("MATRICULAR", "matriculas", matricula_id, {"aluno": aluno_id, "turma": turma_id, "valor": total})
            flash("Matrícula registrada.", "success")
            return redirect(f"/alunos/{aluno_id}")
    return render_template(
        "comercial/matricula_nova.html", f=f, aluno_sel=request.values.get("aluno_id", type=int),
        alunos=todos("SELECT id, nome, matricula FROM alunos WHERE ativo = 1 ORDER BY nome"),
        turmas=todos(
            """SELECT t.id, t.nome, t.capacidade, c.valor,
                      (SELECT COUNT(*) FROM matriculas m WHERE m.turma_id = t.id AND m.status = 'ativa') AS ocupadas
               FROM turmas t JOIN cursos c ON c.id = t.curso_id WHERE t.ativa = 1 ORDER BY t.nome"""),
        vencimento=somar_meses(date.today(), 1).isoformat())


@bp.route("/matriculas/<int:matricula_id>/cancelar", methods=["POST"])
@auth.exige(*auth.GESTAO)
def cancelar_matricula(matricula_id):
    m = um("SELECT * FROM matriculas WHERE id = ?", (matricula_id,))
    if m is None:
        abort(404)
    executar("UPDATE matriculas SET status = 'cancelada', data_conclusao = date('now', 'localtime') WHERE id = ?", (matricula_id,))
    # Parcelas ainda não pagas deixam de ser cobradas; as pagas ficam no histórico.
    executar("""UPDATE parcelas SET status = 'cancelada' WHERE status = 'pendente'
                AND financeiro_id IN (SELECT id FROM financeiro WHERE matricula_id = ?)""", (matricula_id,))
    for (fid,) in todos("SELECT id FROM financeiro WHERE matricula_id = ?", (matricula_id,)):
        recalcular_financeiro(get_db(), fid)
    auth.auditar("CANCELAR_MATRICULA", "matriculas", matricula_id)
    flash("Matrícula cancelada e parcelas em aberto baixadas.", "success")
    return redirect("/matriculas")


# ---------------------------------------------------------------- financeiro
FILTROS = {
    "abertas": "p.status = 'pendente'",
    "atrasadas": "p.status = 'pendente' AND p.data_vencimento < date('now', 'localtime')",
    "pagas": "p.status = 'pago'",
    "todas": "1=1",
}


@bp.route("/financeiro")
@auth.exige(*auth.GESTAO)
def financeiro():
    filtro = request.args.get("ver", "abertas")
    if filtro not in FILTROS:
        filtro = "abertas"
    q = request.args.get("q", "").strip()
    pagina = max(request.args.get("p", 1, type=int), 1)
    base = f"""FROM parcelas p JOIN financeiro f ON f.id = p.financeiro_id
               JOIN matriculas m ON m.id = f.matricula_id JOIN alunos a ON a.id = m.aluno_id
               JOIN turmas t ON t.id = m.turma_id
               WHERE {FILTROS[filtro]} AND (a.nome LIKE ? OR t.nome LIKE ?)"""
    params = [f"%{q}%", f"%{q}%"]
    total = valor(f"SELECT COUNT(*) {base}", params)
    ordem = "p.data_pagamento DESC, p.id DESC" if filtro == "pagas" else "p.data_vencimento, p.id"
    linhas = todos(
        f"""SELECT p.*, a.nome AS aluno, a.id AS aluno_id, t.nome AS turma, f.parcelas AS de
            {base} ORDER BY {ordem} LIMIT ? OFFSET ?""", params + [POR_PAGINA, (pagina - 1) * POR_PAGINA])
    resumo = dict(
        recebido_mes=valor("""SELECT SUM(valor_parcela) FROM parcelas WHERE status = 'pago'
                              AND strftime('%Y-%m', data_pagamento) = strftime('%Y-%m', 'now', 'localtime')"""),
        a_receber=valor("SELECT SUM(valor_parcela) FROM parcelas WHERE status = 'pendente'"),
        atrasado=valor("SELECT SUM(valor_parcela) FROM parcelas WHERE status = 'pendente' AND data_vencimento < date('now', 'localtime')"),
    )
    return render_template("comercial/financeiro.html", linhas=linhas, filtro=filtro, q=q, resumo=resumo,
                           metodos=METODOS, total=total, pagina=pagina,
                           paginas=max((total + POR_PAGINA - 1) // POR_PAGINA, 1))


def _voltar():
    destino = request.form.get("voltar", "")
    return redirect(destino if destino.startswith("/") and not destino.startswith("//") else "/financeiro")


@bp.route("/parcelas/<int:parcela_id>/pagar", methods=["POST"])
@auth.exige(*auth.GESTAO)
def pagar(parcela_id):
    p = um("SELECT * FROM parcelas WHERE id = ?", (parcela_id,))
    if p is None:
        abort(404)
    metodo = request.form.get("metodo")
    if p["status"] != "pendente":
        flash("Esta parcela não está em aberto.", "error")
    elif metodo not in METODOS:
        flash("Escolha a forma de pagamento.", "error")
    else:
        executar("UPDATE parcelas SET status = 'pago', data_pagamento = date('now', 'localtime'), metodo_pagamento = ? WHERE id = ?",
                 (metodo, parcela_id))
        recalcular_financeiro(get_db(), p["financeiro_id"])
        auth.auditar("RECEBER_PARCELA", "parcelas", parcela_id, {"valor": p["valor_parcela"], "metodo": metodo})
        flash("Pagamento registrado.", "success")
    return _voltar()


@bp.route("/parcelas/<int:parcela_id>/estornar", methods=["POST"])
@auth.exige("admin")
def estornar(parcela_id):
    p = um("SELECT * FROM parcelas WHERE id = ?", (parcela_id,))
    if p is None:
        abort(404)
    if p["status"] != "pago":
        flash("Só é possível estornar parcelas pagas.", "error")
    else:
        executar("UPDATE parcelas SET status = 'pendente', data_pagamento = NULL, metodo_pagamento = NULL WHERE id = ?",
                 (parcela_id,))
        recalcular_financeiro(get_db(), p["financeiro_id"])
        auth.auditar("ESTORNAR_PARCELA", "parcelas", parcela_id, {"valor": p["valor_parcela"]})
        flash("Pagamento estornado.", "success")
    return _voltar()
