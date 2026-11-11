"""Relatórios em tela, para impressão e em CSV (abre no Excel)."""
import csv
import io

from flask import Blueprint, Response, abort, render_template, request

import auth
from db import todos

bp = Blueprint("relatorios", __name__)

# nome -> (título, descrição, [(coluna, rótulo, formato)], SQL)
RELATORIOS = {
    "turmas": ("Turmas", "Ocupação e dados de cada turma ativa.",
               [("codigo", "Código", None), ("nome", "Turma", None), ("curso", "Curso", None),
                ("professor", "Professor", None), ("horario", "Horário", None),
                ("alunos", "Alunos", None), ("capacidade", "Vagas", None)],
               """SELECT t.codigo, t.nome, c.nome AS curso, p.nome AS professor, t.horario, t.capacidade,
                         (SELECT COUNT(*) FROM matriculas m WHERE m.turma_id = t.id AND m.status = 'ativa') AS alunos
                  FROM turmas t JOIN cursos c ON c.id = t.curso_id JOIN professores p ON p.id = t.professor_id
                  WHERE t.ativa = 1 ORDER BY t.nome"""),
    "frequencia": ("Frequência", "Percentual de presença por aluno e turma.",
                   [("aluno", "Aluno", None), ("turma", "Turma", None), ("aulas", "Aulas", None),
                    ("presencas", "Presenças", None), ("percentual", "Frequência (%)", None)],
                   """SELECT a.nome AS aluno, t.nome AS turma, COUNT(*) AS aulas, SUM(f.presente) AS presencas,
                             ROUND(SUM(f.presente) * 100.0 / COUNT(*), 1) AS percentual
                      FROM frequencias f JOIN matriculas m ON m.id = f.matricula_id
                      JOIN alunos a ON a.id = m.aluno_id JOIN turmas t ON t.id = m.turma_id
                      GROUP BY m.id ORDER BY percentual, a.nome"""),
    "desempenho": ("Desempenho", "Notas e média por aluno e módulo.",
                   [("aluno", "Aluno", None), ("turma", "Turma", None), ("modulo", "Módulo", None),
                    ("primeira_nota", "1ª", None), ("segunda_nota", "2ª", None),
                    ("terceira_nota", "3ª", None), ("media_final", "Média", None)],
                   """SELECT a.nome AS aluno, t.nome AS turma, mo.nome AS modulo, n.primeira_nota,
                             n.segunda_nota, n.terceira_nota, n.media_final
                      FROM notas n JOIN matriculas m ON m.id = n.matricula_id JOIN alunos a ON a.id = m.aluno_id
                      JOIN turmas t ON t.id = m.turma_id JOIN modulos mo ON mo.id = n.modulo_id
                      ORDER BY a.nome, t.nome, mo.ordem"""),
    "inadimplencia": ("Inadimplência", "Parcelas vencidas e não pagas.",
                      [("aluno", "Aluno", None), ("telefone", "Telefone", None), ("turma", "Turma", None),
                       ("numero_parcela", "Parcela", None), ("data_vencimento", "Vencimento", "data"),
                       ("dias", "Dias em atraso", None), ("valor_parcela", "Valor", "brl")],
                      """SELECT a.nome AS aluno, a.telefone, t.nome AS turma, p.numero_parcela, p.data_vencimento,
                                CAST(julianday('now', 'localtime') - julianday(p.data_vencimento) AS INTEGER) AS dias, p.valor_parcela
                         FROM parcelas p JOIN financeiro f ON f.id = p.financeiro_id
                         JOIN matriculas m ON m.id = f.matricula_id JOIN alunos a ON a.id = m.aluno_id
                         JOIN turmas t ON t.id = m.turma_id
                         WHERE p.status = 'pendente' AND p.data_vencimento < date('now', 'localtime')
                         ORDER BY p.data_vencimento"""),
    "recebimentos": ("Recebimentos", "Pagamentos recebidos, do mais recente ao mais antigo.",
                     [("data_pagamento", "Data", "data"), ("aluno", "Aluno", None), ("turma", "Turma", None),
                      ("numero_parcela", "Parcela", None), ("metodo_pagamento", "Forma", None),
                      ("valor_parcela", "Valor", "brl")],
                     """SELECT p.data_pagamento, a.nome AS aluno, t.nome AS turma, p.numero_parcela,
                               p.metodo_pagamento, p.valor_parcela
                        FROM parcelas p JOIN financeiro f ON f.id = p.financeiro_id
                        JOIN matriculas m ON m.id = f.matricula_id JOIN alunos a ON a.id = m.aluno_id
                        JOIN turmas t ON t.id = m.turma_id
                        WHERE p.status = 'pago' ORDER BY p.data_pagamento DESC, p.id DESC LIMIT 1000"""),
}


@bp.route("/relatorios")
@auth.exige(*auth.GESTAO)
def indice():
    return render_template("relatorios/indice.html", relatorios=RELATORIOS)


@bp.route("/relatorios/<nome>")
@auth.exige(*auth.GESTAO)
def relatorio(nome):
    if nome not in RELATORIOS:
        abort(404)
    titulo, descricao, colunas, sql = RELATORIOS[nome]
    linhas = todos(sql)
    if request.args.get("formato") == "csv":
        saida = io.StringIO()
        w = csv.writer(saida, delimiter=";")
        w.writerow([c[1] for c in colunas])
        for l in linhas:
            w.writerow([str(l[c[0]]).replace(".", ",") if isinstance(l[c[0]], float) else l[c[0]] for c in colunas])
        auth.auditar("EXPORTAR", nome)
        return Response("﻿" + saida.getvalue(), mimetype="text/csv; charset=utf-8",
                        headers={"Content-Disposition": f"attachment; filename={nome}.csv"})
    soma = sum(l["valor_parcela"] or 0 for l in linhas) if any(c[0] == "valor_parcela" for c in colunas) else None
    return render_template("relatorios/tabela.html", nome=nome, titulo=titulo, descricao=descricao,
                           colunas=colunas, linhas=linhas, soma=soma)
