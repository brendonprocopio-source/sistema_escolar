"""Sistema de Gestão Escolar — ponto de entrada.

Rodar:  python app.py        (http://localhost:5000)
"""
import os
import secrets
from datetime import date, datetime, timezone

from flask import Flask, g, redirect, render_template, request, session

import auth
import db

BASE = os.path.dirname(os.path.abspath(__file__))

MENU = [  # (rótulo, url, ícone, papéis)
    ("Painel", "/painel", "home", auth.EQUIPE + ("aluno",)),
    ("Alunos", "/alunos", "users", auth.GESTAO),
    ("Professores", "/professores", "cap", auth.GESTAO),
    ("Turmas", "/turmas", "grid", auth.GESTAO),
    ("Matrículas", "/matriculas", "clipboard", auth.GESTAO),
    ("Financeiro", "/financeiro", "money", auth.GESTAO),
    ("Cronograma", "/cronograma", "calendar", auth.GESTAO),
    ("Salas", "/salas", "door", auth.GESTAO),
    ("Relatórios", "/relatorios", "chart", auth.GESTAO),
    ("Cursos", "/cursos", "book", ("admin",)),
    ("Módulos", "/modulos", "layers", ("admin",)),
    ("Funcionários", "/funcionarios", "briefcase", ("admin",)),
    ("Setores", "/setores", "building", ("admin",)),
    ("Usuários", "/usuarios", "shield", ("admin",)),
    ("Auditoria", "/auditoria", "list", ("admin",)),
]


def _chave_secreta(pasta):
    """Usa SECRET_KEY do ambiente ou gera uma chave e guarda na pasta de dados."""
    if os.environ.get("SECRET_KEY"):
        return os.environ["SECRET_KEY"]
    caminho = os.path.join(pasta, "secret_key")
    if not os.path.exists(caminho):
        with open(caminho, "w") as f:
            f.write(secrets.token_hex(32))
    with open(caminho) as f:
        return f.read().strip()


def _data(v, fmt="%d/%m/%Y"):
    if not v:
        return "—"
    try:
        return datetime.fromisoformat(str(v)).strftime(fmt)
    except ValueError:
        return v


def _datahora(v):
    """O SQLite grava CURRENT_TIMESTAMP em UTC; aqui convertemos para a hora local."""
    try:
        utc = datetime.fromisoformat(str(v)).replace(tzinfo=timezone.utc)
        return utc.astimezone().strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return v or "—"


def _brl(v):
    return "R$ " + f"{float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def criar_app(config=None):
    app = Flask(__name__)
    dados = os.environ.get("DADOS_DIR", os.path.join(BASE, "dados"))
    app.config.update(
        DATABASE=os.path.join(dados, "escola.db"),
        UPLOADS=os.path.join(dados, "uploads"),
        MAX_CONTENT_LENGTH=8 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        AUTOCADASTRO=os.environ.get("AUTOCADASTRO") == "1",
        NOME_ESCOLA=os.environ.get("NOME_ESCOLA", "Gestão Escolar"),
        MEDIA_APROVACAO=6.0,
        FREQUENCIA_MINIMA=75,
    )
    app.config.update(config or {})
    os.makedirs(app.config["UPLOADS"], exist_ok=True)
    app.secret_key = app.config.get("SECRET_KEY") or _chave_secreta(dados)

    db.iniciar_banco(app)
    app.teardown_appcontext(db.fechar_db)

    @app.before_request
    def antes():
        if request.endpoint == "static":
            return None
        auth.carregar_usuario()
        auth.validar_csrf()
        livres = ("conta.senha", "conta.sair")
        if g.usuario and g.usuario["trocar_senha"] and request.endpoint not in livres:
            return redirect("/conta/senha")
        return None

    @app.after_request
    def cabecalhos(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "same-origin")
        return resp

    @app.context_processor
    def contexto():
        p = auth.papel()
        return dict(
            csrf=auth.campo_csrf, papel=p, hoje=date.today().isoformat(),
            menu=[m for m in MENU if p in m[3]],
            nome_usuario=session.get("nome", ""), escola=app.config["NOME_ESCOLA"],
            gestao=p in auth.GESTAO,
        )

    app.jinja_env.filters.update(
        brl=_brl, data=_data, datahora=_datahora,
        nota=lambda v: f"{v:.1f}".replace(".", ","),
        cpf=lambda v: f"{v[:3]}.{v[3:6]}.{v[6:9]}-{v[9:]}" if v and len(v) == 11 and v.isdigit() else v)

    for codigo, titulo, msg in [
        (400, "Não foi possível processar", None),
        (403, "Acesso negado", "Sua conta não tem permissão para ver esta página."),
        (404, "Página não encontrada", "O endereço não existe ou o registro foi removido."),
        (413, "Arquivo grande demais", "O limite por arquivo é de 8 MB."),
        (500, "Erro interno", "Algo deu errado do nosso lado. Tente novamente."),
    ]:
        def tratar(e, codigo=codigo, titulo=titulo, msg=msg):
            return render_template("erro.html", codigo=codigo, titulo=titulo,
                                   msg=msg or getattr(e, "description", "")), codigo
        app.register_error_handler(codigo, tratar)

    from rotas import admin, alunos, cadastros, comercial, conta, painel, relatorios, turmas
    for modulo in (conta, painel, cadastros, alunos, turmas, comercial, relatorios, admin):
        app.register_blueprint(modulo.bp)
    return app


if __name__ == "__main__":
    app = criar_app()
    porta = int(os.environ.get("PORT", 5000))
    print(f"  Sistema no ar: http://localhost:{porta}\n")
    try:
        from waitress import serve          # servidor de produção, se instalado
        serve(app, host="0.0.0.0", port=porta, threads=8)
    except ImportError:
        app.run(host="0.0.0.0", port=porta, debug=os.environ.get("FLASK_DEBUG") == "1")
