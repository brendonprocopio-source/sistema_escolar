"""Login, saída, troca de senha e autocadastro (opcional)."""
from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, session

import auth
from db import executar, get_db, um, valor
from rotas.cadastros import nova_matricula_codigo, validar_pessoa

bp = Blueprint("conta", __name__)


def _nome(usuario):
    tabela = usuario["tabela_referencia"]
    if tabela in ("alunos", "professores", "funcionarios"):
        return valor(f"SELECT nome FROM {tabela} WHERE id = ?", (usuario["id_referencia"],), usuario["email"])
    return usuario["email"]


@bp.route("/login", methods=["GET", "POST"])
def login():
    if g.usuario:
        return redirect("/painel")
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        chave = f"{request.remote_addr}|{email}"
        if auth.login_bloqueado(chave):
            flash("Muitas tentativas. Aguarde alguns minutos e tente de novo.", "error")
            return render_template("login.html", email=email), 429
        usuario = um("SELECT * FROM usuarios WHERE lower(email) = ? AND ativo = 1", (email,))
        if usuario and auth.verificar_senha(request.form.get("senha", ""), usuario["senha"]):
            auth.limpar_falhas(chave)
            session.clear()
            session.permanent = False
            session["uid"] = usuario["id"]
            session["nome"] = _nome(usuario)
            g.usuario = usuario
            auth.auditar("LOGIN", "usuarios", usuario["id"])
            return redirect("/painel")
        auth.registrar_falha(chave)
        flash("E-mail ou senha incorretos.", "error")
        return render_template("login.html", email=email), 401
    return render_template("login.html", email="")


@bp.route("/logout", methods=["POST"], endpoint="sair")
def sair():
    if g.usuario:
        auth.auditar("LOGOUT", "usuarios", g.usuario["id"])
    session.clear()
    return redirect("/login")


@bp.route("/conta/senha", methods=["GET", "POST"], endpoint="senha")
@auth.exige()
def senha():
    if request.method == "POST":
        atual, nova = request.form.get("atual", ""), request.form.get("nova", "")
        erro = None
        if not auth.verificar_senha(atual, g.usuario["senha"]):
            erro = "A senha atual não confere."
        elif nova != request.form.get("confirmar", ""):
            erro = "A confirmação não bate com a nova senha."
        elif nova == atual:
            erro = "Escolha uma senha diferente da atual."
        else:
            erro = auth.senha_fraca(nova)
        if erro:
            flash(erro, "error")
        else:
            executar("UPDATE usuarios SET senha = ?, trocar_senha = 0 WHERE id = ?",
                     (auth.hash_senha(nova), g.usuario["id"]))
            auth.auditar("TROCAR_SENHA", "usuarios", g.usuario["id"])
            flash("Senha alterada.", "success")
            return redirect("/painel")
    return render_template("senha.html", obrigatorio=g.usuario["trocar_senha"])


@bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    """Autocadastro de aluno. Desligado por padrão (AUTOCADASTRO=1 liga)."""
    if not current_app.config["AUTOCADASTRO"]:
        abort(404)
    form = request.form
    if request.method == "POST":
        nome, email = form.get("nome", "").strip(), form.get("email", "").strip().lower()
        cpf = "".join(c for c in form.get("cpf", "") if c.isdigit())
        erro = validar_pessoa(nome, email, cpf) or auth.senha_fraca(form.get("senha", ""))
        if not erro and um("SELECT 1 FROM usuarios WHERE lower(email) = ?", (email,)):
            erro = "Já existe uma conta com este e-mail."
        if not erro and um("SELECT 1 FROM alunos WHERE cpf = ?", (cpf,)):
            erro = "Já existe um aluno com este CPF."
        if erro:
            flash(erro, "error")
        else:
            aluno_id = executar(
                """INSERT INTO alunos (nome, email, cpf, senha, matricula, data_nascimento, telefone)
                   VALUES (?, ?, ?, '', ?, ?, ?)""",
                (nome, email, cpf, nova_matricula_codigo("alunos", "ALN"),
                 form.get("data_nascimento") or None, form.get("telefone", "").strip() or None))
            executar("""INSERT INTO usuarios (email, senha, tipo_usuario, tabela_referencia, id_referencia)
                        VALUES (?, ?, 'aluno', 'alunos', ?)""",
                     (email, auth.hash_senha(form["senha"]), aluno_id))
            executar("INSERT INTO status_aluno (aluno_id, status, data_atualizacao) VALUES (?, 'Não iniciou', date('now', 'localtime'))",
                     (aluno_id,))
            get_db().commit()
            flash("Cadastro feito. Entre com seu e-mail e senha.", "success")
            return redirect("/login")
    return render_template("cadastro.html", f=form)
