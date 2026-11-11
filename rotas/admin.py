"""Administração: contas de acesso, auditoria e backup."""
import io
import os
import sqlite3
import tempfile
from datetime import datetime

from flask import Blueprint, abort, flash, g, redirect, render_template, request, send_file

import auth
from db import executar, get_db, todos, um, valor

bp = Blueprint("admin", __name__)
POR_PAGINA = 50


@bp.route("/usuarios")
@auth.exige("admin")
def usuarios():
    linhas = todos(
        """SELECT u.*, COALESCE(a.nome, p.nome, f.nome) AS nome FROM usuarios u
           LEFT JOIN alunos a ON u.tabela_referencia = 'alunos' AND a.id = u.id_referencia
           LEFT JOIN professores p ON u.tabela_referencia = 'professores' AND p.id = u.id_referencia
           LEFT JOIN funcionarios f ON u.tabela_referencia = 'funcionarios' AND f.id = u.id_referencia
           ORDER BY u.tipo_usuario, nome""")
    return render_template("admin/usuarios.html", linhas=linhas)


@bp.route("/usuarios/<int:uid>/<acao>", methods=["POST"])
@auth.exige("admin")
def acao_usuario(uid, acao):
    u = um("SELECT * FROM usuarios WHERE id = ?", (uid,))
    if u is None:
        abort(404)
    eu = uid == g.usuario["id"]
    if acao == "senha":
        nova = auth.senha_temporaria()
        executar("UPDATE usuarios SET senha = ?, trocar_senha = 1 WHERE id = ?", (auth.hash_senha(nova), uid))
        flash(f"Senha provisória de {u['email']}: {nova} (anote agora — não será mostrada de novo).", "success")
    elif acao == "alternar" and not eu:
        executar("UPDATE usuarios SET ativo = ? WHERE id = ?", (0 if u["ativo"] else 1, uid))
        flash("Acesso bloqueado." if u["ativo"] else "Acesso liberado.", "success")
    elif acao == "admin" and not eu and u["tabela_referencia"] == "funcionarios":
        novo = "funcionario" if u["tipo_usuario"] == "admin" else "admin"
        executar("UPDATE usuarios SET tipo_usuario = ? WHERE id = ?", (novo, uid))
        flash(f"{u['email']} agora é {'administrador' if novo == 'admin' else 'funcionário'}.", "success")
    else:
        abort(400, "Ação não permitida (você não pode bloquear nem rebaixar a própria conta).")
    auth.auditar(f"USUARIO_{acao.upper()}", "usuarios", uid)
    return redirect("/usuarios")


@bp.route("/auditoria")
@auth.exige("admin")
def auditoria():
    pagina = max(request.args.get("p", 1, type=int), 1)
    total = valor("SELECT COUNT(*) FROM audit_log")
    linhas = todos(
        """SELECT l.*, u.email FROM audit_log l LEFT JOIN usuarios u ON u.id = l.usuario_id
           ORDER BY l.id DESC LIMIT ? OFFSET ?""", (POR_PAGINA, (pagina - 1) * POR_PAGINA))
    return render_template("admin/auditoria.html", linhas=linhas, pagina=pagina,
                           paginas=max((total + POR_PAGINA - 1) // POR_PAGINA, 1))


@bp.route("/backup", methods=["POST"])
@auth.exige("admin")
def backup():
    """Baixa uma cópia consistente do banco (não inclui os arquivos anexados)."""
    auth.auditar("BACKUP")
    get_db().commit()
    fd, caminho = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        destino = sqlite3.connect(caminho)
        get_db().backup(destino)
        destino.close()
        with open(caminho, "rb") as f:
            conteudo = io.BytesIO(f.read())
    finally:
        os.remove(caminho)
    return send_file(conteudo, as_attachment=True, mimetype="application/octet-stream",
                     download_name=f"escola-backup-{datetime.now():%Y%m%d-%H%M}.db")
