"""Ficha do aluno: situação, boletim, frequência, financeiro, observações e anexos."""
import os
import uuid

from flask import (Blueprint, abort, current_app, flash, g, redirect, render_template, request,
                   send_from_directory)

import auth
from db import executar, todos, um
from rotas.cadastros import STATUS_ALUNO

bp = Blueprint("alunos", __name__)
EXTENSOES = {"pdf", "png", "jpg", "jpeg", "webp", "doc", "docx", "odt", "txt"}


def _aluno_ou_404(aluno_id):
    """Carrega o aluno respeitando quem pode vê-lo."""
    aluno = um("SELECT * FROM alunos WHERE id = ?", (aluno_id,))
    if aluno is None:
        abort(404)
    p, ref = auth.papel(), g.usuario["id_referencia"]
    if p == "aluno" and ref != aluno_id:
        abort(403)
    if p == "professor" and not um(
            """SELECT 1 FROM matriculas m JOIN turmas t ON t.id = m.turma_id
               WHERE m.aluno_id = ? AND t.professor_id = ?""", (aluno_id, ref)):
        abort(403)
    return aluno


@bp.route("/alunos/<int:aluno_id>")
@auth.exige()
def ficha(aluno_id):
    aluno = _aluno_ou_404(aluno_id)
    equipe = auth.papel() in auth.EQUIPE
    turmas = todos(
        """SELECT m.id AS matricula_id, m.status, m.data_matricula, t.id, t.nome, t.horario,
                  c.nome AS curso, p.nome AS professor,
                  (SELECT COUNT(*) FROM frequencias f WHERE f.matricula_id = m.id) AS aulas,
                  (SELECT COUNT(*) FROM frequencias f WHERE f.matricula_id = m.id AND f.presente = 1) AS presencas
           FROM matriculas m JOIN turmas t ON t.id = m.turma_id JOIN cursos c ON c.id = t.curso_id
           JOIN professores p ON p.id = t.professor_id
           WHERE m.aluno_id = ? ORDER BY m.data_matricula DESC""", (aluno_id,))
    notas = todos(
        """SELECT n.*, mo.nome AS modulo, t.nome AS turma
           FROM notas n JOIN matriculas m ON m.id = n.matricula_id JOIN modulos mo ON mo.id = n.modulo_id
           JOIN turmas t ON t.id = m.turma_id WHERE m.aluno_id = ? ORDER BY t.nome, mo.ordem""", (aluno_id,))
    parcelas = [] if auth.papel() == "professor" else todos(
        """SELECT p.*, t.nome AS turma FROM parcelas p JOIN financeiro f ON f.id = p.financeiro_id
           JOIN matriculas m ON m.id = f.matricula_id JOIN turmas t ON t.id = m.turma_id
           WHERE m.aluno_id = ? ORDER BY p.data_vencimento""", (aluno_id,))
    return render_template(
        "alunos/ficha.html", aluno=aluno, turmas=turmas, notas=notas, parcelas=parcelas, equipe=equipe,
        situacao=um("SELECT * FROM status_aluno WHERE aluno_id = ? ORDER BY id DESC LIMIT 1", (aluno_id,)),
        historico=todos("SELECT * FROM status_aluno WHERE aluno_id = ? ORDER BY id DESC LIMIT 10", (aluno_id,)) if equipe else [],
        observacoes=todos(
            """SELECT r.*, u.email AS autor FROM relatorios_aluno r LEFT JOIN usuarios u ON u.id = r.criado_por
               WHERE r.aluno_id = ? ORDER BY r.id DESC""", (aluno_id,)) if equipe else [],
        anexos=todos("SELECT * FROM anexos WHERE aluno_id = ? ORDER BY id DESC", (aluno_id,)) if auth.papel() in auth.GESTAO else [],
        status_possiveis=STATUS_ALUNO, minimo=current_app.config["FREQUENCIA_MINIMA"],
        media_min=current_app.config["MEDIA_APROVACAO"])


@bp.route("/alunos/<int:aluno_id>/situacao", methods=["POST"])
@auth.exige(*auth.GESTAO)
def situacao(aluno_id):
    _aluno_ou_404(aluno_id)
    status = request.form.get("status")
    if status not in STATUS_ALUNO:
        abort(400, "Situação inválida.")
    executar("INSERT INTO status_aluno (aluno_id, status, motivo, data_atualizacao) VALUES (?, ?, ?, date('now', 'localtime'))",
             (aluno_id, status, request.form.get("motivo", "").strip() or None))
    auth.auditar("ALTERAR_SITUACAO", "alunos", aluno_id, {"status": status})
    flash(f"Situação alterada para “{status}”.", "success")
    return redirect(f"/alunos/{aluno_id}")


@bp.route("/alunos/<int:aluno_id>/observacao", methods=["POST"])
@auth.exige(*auth.EQUIPE)
def observacao(aluno_id):
    _aluno_ou_404(aluno_id)
    titulo, texto = request.form.get("titulo", "").strip(), request.form.get("conteudo", "").strip()
    if not titulo or not texto:
        flash("Preencha o título e o texto da observação.", "error")
    else:
        executar("INSERT INTO relatorios_aluno (aluno_id, tipo, titulo, conteudo, criado_por) VALUES (?, 'pedagogico', ?, ?, ?)",
                 (aluno_id, titulo, texto, g.usuario["id"]))
        auth.auditar("OBSERVACAO", "alunos", aluno_id, {"titulo": titulo})
        flash("Observação registrada.", "success")
    return redirect(f"/alunos/{aluno_id}#observacoes")


@bp.route("/alunos/<int:aluno_id>/anexos", methods=["POST"])
@auth.exige(*auth.GESTAO)
def anexar(aluno_id):
    _aluno_ou_404(aluno_id)
    arquivo = request.files.get("arquivo")
    ext = arquivo.filename.rsplit(".", 1)[-1].lower() if arquivo and "." in arquivo.filename else ""
    if not arquivo or not arquivo.filename:
        flash("Escolha um arquivo.", "error")
    elif ext not in EXTENSOES:
        flash("Tipo de arquivo não permitido. Use: " + ", ".join(sorted(EXTENSOES)) + ".", "error")
    else:
        guardado = f"{uuid.uuid4().hex}.{ext}"          # nunca usa o nome enviado como caminho
        caminho = os.path.join(current_app.config["UPLOADS"], guardado)
        arquivo.save(caminho)
        executar(
            """INSERT INTO anexos (aluno_id, tipo, titulo, arquivo, arquivo_nome, arquivo_tamanho, arquivo_tipo)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (aluno_id, request.form.get("tipo") or "Documento",
             request.form.get("titulo", "").strip() or arquivo.filename, guardado,
             arquivo.filename[-120:], os.path.getsize(caminho), arquivo.mimetype))
        auth.auditar("ANEXAR", "alunos", aluno_id, {"arquivo": arquivo.filename})
        flash("Arquivo anexado.", "success")
    return redirect(f"/alunos/{aluno_id}#anexos")


@bp.route("/anexos/<int:anexo_id>")
@auth.exige(*auth.GESTAO)
def baixar(anexo_id):
    anexo = um("SELECT * FROM anexos WHERE id = ?", (anexo_id,))
    if anexo is None:
        abort(404)
    return send_from_directory(current_app.config["UPLOADS"], os.path.basename(anexo["arquivo"]),
                               as_attachment=True, download_name=anexo["arquivo_nome"] or "anexo")


@bp.route("/anexos/<int:anexo_id>/excluir", methods=["POST"])
@auth.exige(*auth.GESTAO)
def excluir_anexo(anexo_id):
    anexo = um("SELECT * FROM anexos WHERE id = ?", (anexo_id,))
    if anexo is None:
        abort(404)
    executar("DELETE FROM anexos WHERE id = ?", (anexo_id,))
    caminho = os.path.join(current_app.config["UPLOADS"], os.path.basename(anexo["arquivo"]))
    if os.path.exists(caminho):
        os.remove(caminho)
    auth.auditar("EXCLUIR_ANEXO", "alunos", anexo["aluno_id"], {"arquivo": anexo["arquivo_nome"]})
    flash("Anexo excluído.", "success")
    return redirect(f"/alunos/{anexo['aluno_id']}#anexos")
