"""Painel inicial: um resumo diferente para cada tipo de usuário."""
from datetime import date

from flask import Blueprint, g, redirect, render_template

import auth
from db import todos, um, valor

bp = Blueprint("painel", __name__)
MESES = "jan fev mar abr mai jun jul ago set out nov dez".split()


def _ultimos_meses(n=6):
    hoje = date.today()
    chaves = []
    for i in range(n - 1, -1, -1):
        m = hoje.month - i
        ano = hoje.year + (m - 1) // 12
        chaves.append(f"{ano}-{(m - 1) % 12 + 1:02d}")
    return chaves


def _serie(sql):
    """Devolve [(rótulo, valor, percentual da maior barra)] dos últimos 6 meses."""
    achados = {l[0]: l[1] or 0 for l in todos(sql)}
    chaves = _ultimos_meses()
    maior = max([achados.get(k, 0) for k in chaves] + [1])
    return [(MESES[int(k[5:]) - 1], achados.get(k, 0), round(achados.get(k, 0) * 100 / maior)) for k in chaves]


@bp.route("/")
def raiz():
    return redirect("/painel" if g.usuario else "/login")


@bp.route("/painel")
@auth.exige()
def painel():
    p, ref = auth.papel(), g.usuario["id_referencia"]

    if p == "aluno":
        return redirect(f"/alunos/{ref}")

    if p == "professor":
        turmas = todos(
            """SELECT t.*, c.nome AS curso,
                      (SELECT COUNT(*) FROM matriculas m WHERE m.turma_id = t.id AND m.status = 'ativa') AS alunos
               FROM turmas t JOIN cursos c ON c.id = t.curso_id
               WHERE t.professor_id = ? AND t.ativa = 1 ORDER BY t.nome""", (ref,))
        agenda = todos(
            """SELECT e.*, t.nome AS turma FROM cronograma e JOIN turmas t ON t.id = e.turma_id
               WHERE t.professor_id = ? AND e.data_evento >= date('now', 'localtime')
               ORDER BY e.data_evento, e.hora_inicio LIMIT 8""", (ref,))
        return render_template("painel.html", turmas=turmas, agenda=agenda)

    mes = "strftime('%Y-%m', {}) = strftime('%Y-%m', 'now', 'localtime')"
    numeros = dict(
        alunos=valor("SELECT COUNT(*) FROM alunos WHERE ativo = 1"),
        turmas=valor("SELECT COUNT(*) FROM turmas WHERE ativa = 1"),
        professores=valor("SELECT COUNT(*) FROM professores WHERE ativo = 1"),
        matriculas_mes=valor(f"SELECT COUNT(*) FROM matriculas WHERE {mes.format('data_matricula')}"),
        recebido_mes=valor(f"SELECT SUM(valor_parcela) FROM parcelas WHERE status = 'pago' AND {mes.format('data_pagamento')}"),
        a_receber=valor("SELECT SUM(valor_parcela) FROM parcelas WHERE status = 'pendente'"),
        atrasado=valor("SELECT SUM(valor_parcela) FROM parcelas WHERE status = 'pendente' AND data_vencimento < date('now', 'localtime')"),
        n_atrasadas=valor("SELECT COUNT(*) FROM parcelas WHERE status = 'pendente' AND data_vencimento < date('now', 'localtime')"),
    )
    situacoes = todos(
        """SELECT status, COUNT(*) AS total FROM (
               SELECT (SELECT status FROM status_aluno s WHERE s.aluno_id = a.id ORDER BY s.id DESC LIMIT 1) AS status
               FROM alunos a WHERE a.ativo = 1) GROUP BY status ORDER BY total DESC""")
    maior = max([s["total"] for s in situacoes] + [1])
    return render_template(
        "painel.html", n=numeros,
        situacoes=[(s["status"] or "Sem situação", s["total"], round(s["total"] * 100 / maior)) for s in situacoes],
        matriculas=_serie("SELECT strftime('%Y-%m', data_matricula), COUNT(*) FROM matriculas GROUP BY 1"),
        receita=_serie("""SELECT strftime('%Y-%m', data_pagamento), SUM(valor_parcela) FROM parcelas
                          WHERE status = 'pago' GROUP BY 1"""),
        vencendo=todos(
            """SELECT p.*, a.nome AS aluno, a.id AS aluno_id FROM parcelas p
               JOIN financeiro f ON f.id = p.financeiro_id JOIN matriculas m ON m.id = f.matricula_id
               JOIN alunos a ON a.id = m.aluno_id
               WHERE p.status = 'pendente' AND p.data_vencimento <= date('now', 'localtime', '+7 day')
               ORDER BY p.data_vencimento LIMIT 6"""),
        agenda=todos(
            """SELECT e.*, t.nome AS turma FROM cronograma e JOIN turmas t ON t.id = e.turma_id
               WHERE e.data_evento >= date('now', 'localtime') ORDER BY e.data_evento, e.hora_inicio LIMIT 6"""))
