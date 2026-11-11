"""Cadastros genéricos.

Cada cadastro (cursos, turmas, alunos...) é só uma configuração em CADASTROS:
as telas de listar, criar, editar e ativar/desativar são as mesmas para todos.
Para criar um cadastro novo, basta acrescentar uma entrada no dicionário.
"""
import re
import sqlite3
from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request

import auth
from db import executar, get_db, todos, um, valor

bp = Blueprint("cadastros", __name__)
POR_PAGINA = 25
UFS = ("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO").split()
STATUS_ALUNO = ["Não iniciou", "Frequente", "Trancado", "Desistente", "Concluído"]


def C(nome, rotulo, tipo="text", obrig=False, opcoes=None, largo=False, ajuda=""):
    """Um campo de formulário. tipo: text, email, cpf, tel, date, time, int, money, textarea, select."""
    return dict(nome=nome, rotulo=rotulo, tipo=tipo, obrig=obrig, opcoes=opcoes, largo=largo, ajuda=ajuda)


PESSOA = [C("nome", "Nome completo", obrig=True), C("email", "E-mail", "email", obrig=True),
          C("cpf", "CPF", "cpf", obrig=True)]

CADASTROS = {
    "alunos": dict(
        titulo="Alunos", singular="aluno", tabela="alunos", papeis=auth.GESTAO, ativo="ativo",
        conta="aluno", codigo=("matricula", "ALN"), detalhe="/alunos/{id}",
        select="""SELECT a.*, (SELECT status FROM status_aluno s WHERE s.aluno_id = a.id
                               ORDER BY s.id DESC LIMIT 1) AS status
                  FROM alunos a""",
        busca=("a.nome", "a.email", "a.matricula", "a.cpf"), ordem="a.nome",
        colunas=[("nome", "Nome"), ("matricula", "Matrícula"), ("email", "E-mail"),
                 ("telefone", "Telefone"), ("status", "Situação", "selo")],
        campos=PESSOA + [
            C("data_nascimento", "Nascimento", "date"), C("telefone", "Telefone", "tel"),
            C("responsavel", "Responsável"), C("telefone_responsavel", "Telefone do responsável", "tel"),
            C("endereco", "Endereço", largo=True), C("cidade", "Cidade"),
            C("estado", "UF", "select", opcoes=[(u, u) for u in UFS])]),
    "professores": dict(
        titulo="Professores", singular="professor", tabela="professores", papeis=auth.GESTAO,
        ativo="ativo", conta="professor", codigo=("matricula", "PRF"),
        select="""SELECT p.*, (SELECT COUNT(*) FROM turmas t WHERE t.professor_id = p.id AND t.ativa = 1) AS turmas
                  FROM professores p""",
        busca=("p.nome", "p.email", "p.especialidade"), ordem="p.nome",
        colunas=[("nome", "Nome"), ("email", "E-mail"), ("especialidade", "Especialidade"),
                 ("turmas", "Turmas ativas")],
        campos=PESSOA + [C("formacao", "Formação"), C("especialidade", "Especialidade")]),
    "turmas": dict(
        titulo="Turmas", singular="turma", tabela="turmas", papeis=auth.GESTAO, ativo="ativa",
        detalhe="/turmas/{id}",
        select="""SELECT t.*, c.nome AS curso, p.nome AS professor,
                         (SELECT COUNT(*) FROM matriculas m WHERE m.turma_id = t.id AND m.status = 'ativa')
                         || ' / ' || COALESCE(t.capacidade, '∞') AS vagas
                  FROM turmas t JOIN cursos c ON c.id = t.curso_id
                  JOIN professores p ON p.id = t.professor_id""",
        busca=("t.nome", "t.codigo", "c.nome", "p.nome"), ordem="t.data_inicio DESC, t.nome",
        colunas=[("codigo", "Código"), ("nome", "Turma"), ("curso", "Curso"), ("professor", "Professor"),
                 ("horario", "Horário"), ("vagas", "Alunos / vagas")],
        campos=[
            C("codigo", "Código", obrig=True, ajuda="Ex.: TUR001"), C("nome", "Nome", obrig=True),
            C("curso_id", "Curso", "select", obrig=True,
              opcoes="SELECT id, nome FROM cursos WHERE ativo = 1 ORDER BY nome"),
            C("professor_id", "Professor", "select", obrig=True,
              opcoes="SELECT id, nome FROM professores WHERE ativo = 1 ORDER BY nome"),
            C("semestre", "Semestre", ajuda="Ex.: 2026.2"), C("horario", "Horário", ajuda="Ex.: Seg e Qua, 19h–21h"),
            C("data_inicio", "Início", "date"), C("data_fim", "Término", "date"),
            C("sala", "Sala", opcoes="SELECT nome, nome FROM salas WHERE ativa = 1 ORDER BY nome",
              ajuda="Sugestões vêm do cadastro de Salas"),
            C("capacidade", "Vagas", "int")]),
    "cronograma": dict(
        titulo="Cronograma", singular="evento", tabela="cronograma", papeis=auth.GESTAO,
        select="SELECT e.*, t.nome AS turma FROM cronograma e JOIN turmas t ON t.id = e.turma_id",
        busca=("e.titulo", "t.nome", "e.tipo"), ordem="e.data_evento DESC, e.hora_inicio",
        colunas=[("data_evento", "Data", "data"), ("hora_inicio", "Início"), ("titulo", "Evento"),
                 ("tipo", "Tipo", "selo"), ("turma", "Turma"), ("local", "Local")],
        campos=[
            C("titulo", "Título", obrig=True),
            C("turma_id", "Turma", "select", obrig=True,
              opcoes="SELECT id, nome FROM turmas WHERE ativa = 1 ORDER BY nome"),
            C("tipo", "Tipo", "select", opcoes=[(x, x) for x in ("Aula", "Prova", "Reunião", "Evento", "Feriado")]),
            C("data_evento", "Data", "date", obrig=True),
            C("hora_inicio", "Início", "time"), C("hora_fim", "Fim", "time"),
            C("local", "Local"), C("descricao", "Descrição", "textarea", largo=True)]),
    "salas": dict(
        titulo="Salas", singular="sala", tabela="salas", papeis=auth.GESTAO, ativo="ativa",
        select="SELECT s.* FROM salas s", busca=("s.nome", "s.codigo"), ordem="s.nome",
        colunas=[("codigo", "Código"), ("nome", "Sala"), ("capacidade", "Capacidade"), ("recursos", "Recursos")],
        campos=[C("codigo", "Código", obrig=True), C("nome", "Nome", obrig=True),
                C("capacidade", "Capacidade", "int"),
                C("recursos", "Recursos", ajuda="Ex.: projetor, 20 computadores")]),
    "cursos": dict(
        titulo="Cursos", singular="curso", tabela="cursos", papeis=("admin",), ativo="ativo",
        select="""SELECT c.*, (SELECT COUNT(*) FROM turmas t WHERE t.curso_id = c.id) AS turmas,
                         (SELECT COUNT(*) FROM modulos m WHERE m.curso_id = c.id) AS modulos
                  FROM cursos c""",
        busca=("c.nome",), ordem="c.nome",
        colunas=[("nome", "Curso"), ("duracao_meses", "Duração (meses)"), ("valor", "Valor", "brl"),
                 ("modulos", "Módulos"), ("turmas", "Turmas")],
        campos=[C("nome", "Nome", obrig=True), C("duracao_meses", "Duração (meses)", "int"),
                C("valor", "Valor do curso (R$)", "money"),
                C("descricao", "Descrição", "textarea", largo=True)]),
    "modulos": dict(
        titulo="Módulos", singular="módulo", tabela="modulos", papeis=("admin",),
        select="SELECT m.*, c.nome AS curso FROM modulos m JOIN cursos c ON c.id = m.curso_id",
        busca=("m.nome", "c.nome"), ordem="c.nome, m.ordem, m.nome",
        colunas=[("curso", "Curso"), ("ordem", "Ordem"), ("nome", "Módulo"), ("carga_horaria", "Carga horária (h)")],
        campos=[C("curso_id", "Curso", "select", obrig=True,
                  opcoes="SELECT id, nome FROM cursos WHERE ativo = 1 ORDER BY nome"),
                C("nome", "Nome", obrig=True), C("ordem", "Ordem", "int"),
                C("carga_horaria", "Carga horária (h)", "int"),
                C("descricao", "Descrição", "textarea", largo=True)]),
    "funcionarios": dict(
        titulo="Funcionários", singular="funcionário", tabela="funcionarios", papeis=("admin",),
        ativo="ativo", conta="funcionario",
        select="SELECT f.*, s.nome AS setor FROM funcionarios f LEFT JOIN setores s ON s.id = f.setor_id",
        busca=("f.nome", "f.email", "f.cargo"), ordem="f.nome",
        colunas=[("nome", "Nome"), ("email", "E-mail"), ("cargo", "Cargo"), ("setor", "Setor")],
        campos=PESSOA + [
            C("cargo", "Cargo", obrig=True),
            C("setor_id", "Setor", "select", opcoes="SELECT id, nome FROM setores ORDER BY nome"),
            C("salario", "Salário (R$)", "money"), C("data_admissao", "Admissão", "date")]),
    "setores": dict(
        titulo="Setores", singular="setor", tabela="setores", papeis=("admin",),
        select="""SELECT s.*, (SELECT COUNT(*) FROM funcionarios f WHERE f.setor_id = s.id) AS pessoas
                  FROM setores s""",
        busca=("s.nome",), ordem="s.nome",
        colunas=[("nome", "Setor"), ("descricao", "Descrição"), ("pessoas", "Funcionários")],
        campos=[C("nome", "Nome", obrig=True), C("descricao", "Descrição", largo=True)]),
}


# ---------------------------------------------------------------- validação
def cpf_valido(cpf):
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for n in (9, 10):
        soma = sum(int(cpf[i]) * (n + 1 - i) for i in range(n))
        if (soma * 10 % 11) % 10 != int(cpf[n]):
            return False
    return True


def validar_pessoa(nome, email, cpf):
    if len(nome) < 3:
        return "Informe o nome completo."
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return "E-mail inválido."
    if not cpf_valido(cpf):
        return "CPF inválido."
    return None


def nova_matricula_codigo(tabela, prefixo):
    seq = valor(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {tabela}")
    return f"{prefixo}{date.today().year}{seq:04d}"


def _ler(campo, bruto):
    """Converte o texto do formulário no valor a gravar. Levanta ValueError com a mensagem."""
    v = (bruto or "").strip()
    rot, tipo = campo["rotulo"], campo["tipo"]
    if not v:
        if campo["obrig"]:
            raise ValueError(f"Preencha o campo “{rot}”.")
        return None
    if tipo == "email":
        v = v.lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", v):
            raise ValueError("E-mail inválido.")
    elif tipo == "cpf":
        v = re.sub(r"\D", "", v)
        if len(v) != 11:
            raise ValueError("O CPF precisa ter 11 dígitos.")
    elif tipo in ("int", "money"):
        try:
            v = int(v) if tipo == "int" else round(float(v.replace(".", "").replace(",", ".") if "," in v else v), 2)
        except ValueError:
            raise ValueError(f"“{rot}” precisa ser um número.") from None
        if v < 0:
            raise ValueError(f"“{rot}” não pode ser negativo.")
    elif tipo in ("date", "time"):
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}" if tipo == "date" else r"\d{2}:\d{2}(:\d{2})?", v):
            raise ValueError(f"“{rot}” está em formato inválido.")
    elif tipo == "select":
        validas = {str(o[0]) for o in _opcoes(campo)}
        if v not in validas:
            raise ValueError(f"Opção inválida em “{rot}”.")
    return v


def _opcoes(campo):
    op = campo["opcoes"]
    return [tuple(l) for l in todos(op)] if isinstance(op, str) else (op or [])


def _mensagem_integridade(erro, cfg):
    texto = str(erro)
    if "UNIQUE" in texto:
        col = texto.rsplit(".", 1)[-1]
        nomes = {c["nome"]: c["rotulo"] for c in cfg["campos"]}
        return f"Já existe um cadastro com este valor em “{nomes.get(col, col)}”."
    return "Não foi possível salvar: há registros ligados a este cadastro."


def _sem_sensiveis(dados):
    """O log de auditoria não guarda CPF, salário nem senha."""
    return {k: v for k, v in dados.items() if k not in ("cpf", "salario", "senha")}


# ---------------------------------------------------------------- telas
def _cfg(slug):
    cfg = CADASTROS[slug]
    if auth.papel() not in cfg["papeis"]:
        abort(403)
    return cfg


@auth.exige()
def listar(slug):
    cfg = _cfg(slug)
    q = request.args.get("q", "").strip()
    inativos = request.args.get("ver") == "inativos" and cfg.get("ativo")
    pagina = max(request.args.get("p", 1, type=int), 1)
    alias = cfg["busca"][0].split(".")[0]
    conds, params = ["1=1"], []
    if cfg.get("ativo"):
        conds.append(f"{alias}.{cfg['ativo']} = {0 if inativos else 1}")
    if q:
        conds.append("(" + " OR ".join(f"{c} LIKE ?" for c in cfg["busca"]) + ")")
        params += [f"%{q}%"] * len(cfg["busca"])
    base = f"{cfg['select']} WHERE {' AND '.join(conds)}"
    total = valor(f"SELECT COUNT(*) FROM ({base})", params)
    linhas = todos(f"{base} ORDER BY {cfg['ordem']} LIMIT ? OFFSET ?",
                   params + [POR_PAGINA, (pagina - 1) * POR_PAGINA])
    return render_template("cadastros/lista.html", cfg=cfg, slug=slug, linhas=linhas, q=q,
                           inativos=inativos, total=total, pagina=pagina,
                           paginas=max((total + POR_PAGINA - 1) // POR_PAGINA, 1))


@auth.exige()
def editar(slug, id=None):
    cfg = _cfg(slug)
    tabela = cfg["tabela"]
    atual = um(f"SELECT * FROM {tabela} WHERE id = ?", (id,)) if id else None
    if id and atual is None:
        abort(404)
    valores = dict(atual) if atual else {}

    if request.method == "POST":
        valores = {c["nome"]: request.form.get(c["nome"], "") for c in cfg["campos"]}
        try:
            dados = {c["nome"]: _ler(c, valores[c["nome"]]) for c in cfg["campos"]}
            if "data_inicio" in dados and dados.get("data_fim") and dados["data_inicio"] \
                    and dados["data_fim"] < dados["data_inicio"]:
                raise ValueError("O término não pode ser antes do início.")
            # Dígitos verificadores só são cobrados em CPF novo ou alterado (dados antigos seguem editáveis).
            if dados.get("cpf") and dados["cpf"] != re.sub(r"\D", "", (atual["cpf"] if atual else "") or "") \
                    and not cpf_valido(dados["cpf"]):
                raise ValueError("CPF inválido.")
            if cfg.get("conta") and um("SELECT 1 FROM usuarios WHERE lower(email) = ? AND NOT "
                                       "(tabela_referencia = ? AND id_referencia = ?)",
                                       (dados["email"], tabela, id or 0)):
                raise ValueError("Já existe uma conta de acesso com este e-mail.")
            if id:
                sets = ", ".join(f"{k} = ?" for k in dados)
                executar(f"UPDATE {tabela} SET {sets} WHERE id = ?", [*dados.values(), id])
                if cfg.get("conta"):
                    executar("UPDATE usuarios SET email = ? WHERE tabela_referencia = ? AND id_referencia = ?",
                             (dados["email"], tabela, id))
                auth.auditar("EDITAR", tabela, id, _sem_sensiveis(dados))
                flash("Alterações salvas.", "success")
            else:
                if cfg.get("codigo"):
                    col, prefixo = cfg["codigo"]
                    dados[col] = nova_matricula_codigo(tabela, prefixo)
                if cfg.get("conta"):
                    dados["senha"] = ""            # a senha fica só na tabela usuarios
                cols = ", ".join(dados)
                id = executar(f"INSERT INTO {tabela} ({cols}) VALUES ({', '.join('?' * len(dados))})",
                              list(dados.values()))
                auth.auditar("CRIAR", tabela, id, _sem_sensiveis(dados))
                if cfg.get("conta"):
                    senha = auth.senha_temporaria()
                    executar("""INSERT INTO usuarios (email, senha, tipo_usuario, tabela_referencia,
                                id_referencia, trocar_senha) VALUES (?, ?, ?, ?, ?, 1)""",
                             (dados["email"], auth.hash_senha(senha), cfg["conta"], tabela, id))
                    flash(f"Cadastro criado. Senha provisória de acesso: {senha} "
                          "(anote agora — ela não será mostrada de novo).", "success")
                else:
                    flash("Cadastro criado.", "success")
                if tabela == "alunos":
                    executar("INSERT INTO status_aluno (aluno_id, status, data_atualizacao) "
                             "VALUES (?, 'Não iniciou', date('now', 'localtime'))", (id,))
            destino = cfg.get("detalhe", "").format(id=id) or f"/{slug}"
            return redirect(destino)
        except ValueError as e:
            flash(str(e), "error")
        except sqlite3.IntegrityError as e:
            get_db().rollback()
            flash(_mensagem_integridade(e, cfg), "error")

    opcoes = {c["nome"]: _opcoes(c) for c in cfg["campos"] if c["opcoes"]}
    return render_template("cadastros/form.html", cfg=cfg, slug=slug, id=id if atual else None,
                           v=valores, opcoes=opcoes)


@auth.exige()
def alternar(slug, id):
    """Desativa/reativa (quando há coluna 'ativo') ou exclui o registro."""
    cfg = _cfg(slug)
    tabela, col = cfg["tabela"], cfg.get("ativo")
    reg = um(f"SELECT * FROM {tabela} WHERE id = ?", (id,))
    if reg is None:
        abort(404)
    if col:
        novo = 0 if reg[col] else 1
        executar(f"UPDATE {tabela} SET {col} = ? WHERE id = ?", (novo, id))
        if cfg.get("conta"):
            executar("UPDATE usuarios SET ativo = ? WHERE tabela_referencia = ? AND id_referencia = ? "
                     "AND tipo_usuario != 'admin'", (novo, tabela, id))
        auth.auditar("REATIVAR" if novo else "DESATIVAR", tabela, id)
        flash("Cadastro reativado." if novo else "Cadastro desativado.", "success")
    else:
        try:
            executar(f"DELETE FROM {tabela} WHERE id = ?", (id,))
            auth.auditar("EXCLUIR", tabela, id, _sem_sensiveis(dict(reg)))
            flash("Registro excluído.", "success")
        except sqlite3.IntegrityError:
            get_db().rollback()
            flash("Não dá para excluir: existem registros ligados a este cadastro.", "error")
    voltar = request.form.get("voltar", "")
    return redirect(voltar if voltar.startswith("/") and not voltar.startswith("//") else f"/{slug}")


for _slug in CADASTROS:
    bp.add_url_rule(f"/{_slug}", f"{_slug}_listar", listar, defaults={"slug": _slug})
    bp.add_url_rule(f"/{_slug}/novo", f"{_slug}_novo", editar, defaults={"slug": _slug}, methods=["GET", "POST"])
    bp.add_url_rule(f"/{_slug}/<int:id>/editar", f"{_slug}_editar", editar, defaults={"slug": _slug},
                    methods=["GET", "POST"])
    bp.add_url_rule(f"/{_slug}/<int:id>/alternar", f"{_slug}_alternar", alternar, defaults={"slug": _slug},
                    methods=["POST"])
