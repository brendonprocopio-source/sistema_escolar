"""Diário da turma: alunos, chamada (frequência) e notas."""
import re
from datetime import date

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request

import auth
from db import executar, todos, um

bp = Blueprint("turmas", __name__)


def _turma_ou_404(turma_id):
    turma = um(
        """SELECT t.*, c.nome AS curso, p.nome AS professor FROM turmas t
           JOIN cursos c ON c.id = t.curso_id JOIN professores p ON p.id = t.professor_id
           WHERE t.id = ?""", (turma_id,))
    if turma is None:
        abort(404)
    if auth.papel() == "professor" and turma["professor_id"] != g.usuario["id_referencia"]:
        abort(403)
    return turma


def _matriculados(turma_id):
    return todos(
        """SELECT m.id AS matricula_id, a.id AS aluno_id, a.nome, a.matricula FROM matriculas m
           JOIN alunos a ON a.id = m.aluno_id
           WHERE m.turma_id = ? AND m.status = 'ativa' ORDER BY a.nome""", (turma_id,))


@bp.route("/turmas/<int:turma_id>")
@auth.exige(*auth.EQUIPE)
def detalhe(turma_id):
    turma = _turma_ou_404(turma_id)
    alunos = todos(
        """SELECT m.id AS matricula_id, a.id AS aluno_id, a.nome, a.matricula,
                  (SELECT COUNT(*) FROM frequencias f WHERE f.matricula_id = m.id) AS aulas,
                  (SELECT COUNT(*) FROM frequencias f WHERE f.matricula_id = m.id AND f.presente = 1) AS presencas,
                  (SELECT ROUND(AVG(n.media_final), 1) FROM notas n WHERE n.matricula_id = m.id) AS media
           FROM matriculas m JOIN alunos a ON a.id = m.aluno_id
           WHERE m.turma_id = ? AND m.status = 'ativa' ORDER BY a.nome""", (turma_id,))
    aulas = todos(
        """SELECT f.data_aula, SUM(f.presente) AS presentes, COUNT(*) AS total FROM frequencias f
           JOIN matriculas m ON m.id = f.matricula_id WHERE m.turma_id = ?
           GROUP BY f.data_aula ORDER BY f.data_aula DESC LIMIT 8""", (turma_id,))
    return render_template("turmas/detalhe.html", turma=turma, alunos=alunos, aulas=aulas,
                           minimo=current_app.config["FREQUENCIA_MINIMA"],
                           media_min=current_app.config["MEDIA_APROVACAO"])


@bp.route("/turmas/<int:turma_id>/frequencia", methods=["GET", "POST"])
@auth.exige(*auth.EQUIPE)
def frequencia(turma_id):
    turma = _turma_ou_404(turma_id)
    dia = request.values.get("data") or date.today().isoformat()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", dia):
        abort(400, "Data inválida.")
    alunos = _matriculados(turma_id)

    if request.method == "POST":
        if dia > date.today().isoformat():
            flash("Não é possível lançar chamada em data futura.", "error")
        else:
            for a in alunos:
                mid = a["matricula_id"]
                executar(
                    """INSERT INTO frequencias (matricula_id, data_aula, presente, justificativa)
                       VALUES (?, ?, ?, ?)
                       ON CONFLICT(matricula_id, data_aula)
                       DO UPDATE SET presente = excluded.presente, justificativa = excluded.justificativa""",
                    (mid, dia, 1 if request.form.get(f"p_{mid}") else 0,
                     request.form.get(f"j_{mid}", "").strip() or None))
            auth.auditar("CHAMADA", "turmas", turma_id, {"data": dia})
            flash("Chamada salva.", "success")
            return redirect(f"/turmas/{turma_id}")

    lancado = {f["matricula_id"]: f for f in todos(
        """SELECT f.* FROM frequencias f JOIN matriculas m ON m.id = f.matricula_id
           WHERE m.turma_id = ? AND f.data_aula = ?""", (turma_id, dia))}
    return render_template("turmas/frequencia.html", turma=turma, alunos=alunos, dia=dia, lancado=lancado)


def _nota(texto):
    texto = (texto or "").strip().replace(",", ".")
    if not texto:
        return None
    n = float(texto)                     # ValueError se não for número
    if not 0 <= n <= 10:
        raise ValueError
    return round(n, 2)


@bp.route("/turmas/<int:turma_id>/notas", methods=["GET", "POST"])
@auth.exige(*auth.EQUIPE)
def notas(turma_id):
    turma = _turma_ou_404(turma_id)
    modulos = todos("SELECT * FROM modulos WHERE curso_id = ? ORDER BY ordem, nome", (turma["curso_id"],))
    modulo_id = request.values.get("modulo", type=int) or (modulos[0]["id"] if modulos else None)
    if modulo_id and modulo_id not in [m["id"] for m in modulos]:
        abort(404)
    alunos = _matriculados(turma_id)

    if request.method == "POST" and modulo_id:
        try:
            for a in alunos:
                mid = a["matricula_id"]
                n = [_nota(request.form.get(f"n{i}_{mid}")) for i in (1, 2, 3)]
                dadas = [x for x in n if x is not None]
                media = round(sum(dadas) / len(dadas), 2) if dadas else None
                executar(
                    """INSERT INTO notas (matricula_id, modulo_id, primeira_nota, segunda_nota, terceira_nota, media_final)
                       VALUES (?, ?, ?, ?, ?, ?)
                       ON CONFLICT(matricula_id, modulo_id) DO UPDATE SET
                         primeira_nota = excluded.primeira_nota, segunda_nota = excluded.segunda_nota,
                         terceira_nota = excluded.terceira_nota, media_final = excluded.media_final""",
                    (mid, modulo_id, *n, media))
            auth.auditar("NOTAS", "turmas", turma_id, {"modulo": modulo_id})
            flash("Notas salvas.", "success")
            return redirect(f"/turmas/{turma_id}/notas?modulo={modulo_id}")
        except ValueError:
            from db import get_db
            get_db().rollback()
            flash("As notas devem ser números de 0 a 10.", "error")

    lancado = {n["matricula_id"]: n for n in todos(
        """SELECT n.* FROM notas n JOIN matriculas m ON m.id = n.matricula_id
           WHERE m.turma_id = ? AND n.modulo_id = ?""", (turma_id, modulo_id))}
    return render_template("turmas/notas.html", turma=turma, modulos=modulos, modulo_id=modulo_id,
                           alunos=alunos, lancado=lancado, media_min=current_app.config["MEDIA_APROVACAO"])
