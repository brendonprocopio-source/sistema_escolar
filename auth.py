"""Autenticação, permissões, CSRF e auditoria."""
import hashlib
import hmac
import json
import os
import secrets
import string
import time
from functools import wraps

from flask import abort, flash, g, redirect, request, session
from markupsafe import Markup
from werkzeug.security import check_password_hash, generate_password_hash

from db import executar, um

GESTAO = ("admin", "funcionario")          # secretaria / administração
EQUIPE = ("admin", "funcionario", "professor")


# ---------------------------------------------------------------- senhas
def hash_senha(senha):
    return generate_password_hash(senha)


def verificar_senha(senha, guardada):
    """Aceita o formato novo (werkzeug) e o antigo 'salt$hash' (PBKDF2)."""
    if not senha or not guardada:
        return False
    if guardada.startswith(("scrypt:", "pbkdf2:")):
        return check_password_hash(guardada, senha)
    try:
        salt, antigo = guardada.split("$")
        novo = hashlib.pbkdf2_hmac("sha256", senha.encode(), salt.encode(), 100000).hex()
        return hmac.compare_digest(novo, antigo)
    except ValueError:
        return False


def senha_temporaria(tamanho=10):
    alfabeto = string.ascii_letters + string.digits
    return "".join(secrets.choice(alfabeto) for _ in range(tamanho))


def senha_fraca(senha):
    """Devolve a mensagem de erro, ou None se a senha serve."""
    if len(senha) < 8:
        return "A senha precisa ter pelo menos 8 caracteres."
    if senha.isdigit() or senha.isalpha():
        return "Misture letras e números na senha."
    return None


def criar_admin_inicial(con):
    if con.execute("SELECT 1 FROM usuarios WHERE tipo_usuario = 'admin'").fetchone():
        return
    email = os.environ.get("ADMIN_EMAIL", "admin@escola.com")
    senha = os.environ.get("ADMIN_SENHA") or senha_temporaria(12)
    cur = con.execute(
        """INSERT INTO funcionarios (nome, email, cpf, senha, cargo)
           VALUES ('Administrador', ?, '00000000000', '', 'Administrador')""", (email,))
    con.execute(
        """INSERT INTO usuarios (email, senha, tipo_usuario, tabela_referencia, id_referencia, trocar_senha)
           VALUES (?, ?, 'admin', 'funcionarios', ?, 1)""", (email, hash_senha(senha), cur.lastrowid))
    print(f"\n  Administrador criado: {email}  |  senha inicial: {senha}"
          "\n  (será pedido para trocar no primeiro acesso)\n")


# ---------------------------------------------------------------- tentativas de login
_tentativas = {}
LIMITE, JANELA = 5, 300


def login_bloqueado(chave):
    agora = time.time()
    recentes = [t for t in _tentativas.get(chave, []) if agora - t < JANELA]
    _tentativas[chave] = recentes
    return len(recentes) >= LIMITE


def registrar_falha(chave):
    _tentativas.setdefault(chave, []).append(time.time())


def limpar_falhas(chave):
    _tentativas.pop(chave, None)


# ---------------------------------------------------------------- sessão e permissões
def carregar_usuario():
    """Roda antes de cada requisição: popula g.usuario e valida a sessão."""
    g.usuario = None
    uid = session.get("uid")
    if uid:
        g.usuario = um("SELECT * FROM usuarios WHERE id = ? AND ativo = 1", (uid,))
        if g.usuario is None:
            session.clear()


def papel():
    return g.usuario["tipo_usuario"] if g.usuario else None


def exige(*papeis):
    """Protege uma rota. Sem argumentos: basta estar logado."""
    def decorador(f):
        @wraps(f)
        def interno(*args, **kwargs):
            if g.usuario is None:
                flash("Entre com sua conta para continuar.", "info")
                return redirect("/login")
            if papeis and papel() not in papeis:
                abort(403)
            return f(*args, **kwargs)
        return interno
    return decorador


# ---------------------------------------------------------------- CSRF
def token_csrf():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(32)
    return session["_csrf"]


def campo_csrf():
    return Markup(f'<input type="hidden" name="_csrf" value="{token_csrf()}">')


def validar_csrf():
    if request.method == "POST":
        enviado = request.form.get("_csrf", "")
        esperado = session.get("_csrf", "")
        if not esperado or not hmac.compare_digest(enviado, esperado):
            abort(400, "Formulário expirado. Recarregue a página e tente de novo.")


# ---------------------------------------------------------------- auditoria
def auditar(acao, tabela="", id_registro=None, dados=None):
    executar(
        """INSERT INTO audit_log (usuario_id, usuario_tipo, acao, tabela_afetada, id_registro, valores_novos)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (g.usuario["id"] if g.usuario else None, papel(), acao, tabela, id_registro,
         json.dumps(dados, ensure_ascii=False, default=str) if dados else None))
