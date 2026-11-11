"""Banco de dados: conexão por requisição, schema e migrações.

O schema mantém os mesmos nomes de tabelas e colunas das versões anteriores,
então um escola.db antigo continua funcionando (as migrações ajustam o resto).
"""
import os
import sqlite3
from datetime import date

from flask import current_app, g

VERSAO_SCHEMA = 3

SCHEMA = """
CREATE TABLE IF NOT EXISTS setores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    descricao TEXT,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS funcionarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    cpf TEXT NOT NULL UNIQUE,
    senha TEXT NOT NULL DEFAULT '',
    cargo TEXT NOT NULL,
    setor_id INTEGER REFERENCES setores(id),
    salario REAL,
    data_admissao DATE,
    ativo INTEGER DEFAULT 1,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS professores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    cpf TEXT NOT NULL UNIQUE,
    senha TEXT NOT NULL DEFAULT '',
    matricula TEXT NOT NULL UNIQUE,
    formacao TEXT,
    especialidade TEXT,
    ativo INTEGER DEFAULT 1,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS cursos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    descricao TEXT,
    duracao_meses INTEGER,
    valor REAL,
    ativo INTEGER DEFAULT 1,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS modulos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    curso_id INTEGER NOT NULL REFERENCES cursos(id),
    nome TEXT NOT NULL,
    descricao TEXT,
    carga_horaria INTEGER,
    ordem INTEGER,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS turmas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,
    nome TEXT NOT NULL,
    curso_id INTEGER NOT NULL REFERENCES cursos(id),
    professor_id INTEGER NOT NULL REFERENCES professores(id),
    semestre TEXT,
    data_inicio DATE,
    data_fim DATE,
    horario TEXT,
    sala TEXT,
    capacidade INTEGER,
    ativa INTEGER DEFAULT 1,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS alunos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    cpf TEXT NOT NULL UNIQUE,
    senha TEXT NOT NULL DEFAULT '',
    matricula TEXT NOT NULL UNIQUE,
    data_nascimento DATE,
    telefone TEXT,
    endereco TEXT,
    cidade TEXT,
    estado TEXT,
    responsavel TEXT,
    telefone_responsavel TEXT,
    ativo INTEGER DEFAULT 1,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS matriculas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aluno_id INTEGER NOT NULL REFERENCES alunos(id),
    turma_id INTEGER NOT NULL REFERENCES turmas(id),
    data_matricula DATE,
    status TEXT DEFAULT 'ativa',
    data_conclusao DATE,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(aluno_id, turma_id)
);
CREATE TABLE IF NOT EXISTS frequencias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    matricula_id INTEGER NOT NULL REFERENCES matriculas(id),
    data_aula DATE,
    presente INTEGER,
    justificativa TEXT,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS notas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    matricula_id INTEGER NOT NULL REFERENCES matriculas(id),
    modulo_id INTEGER NOT NULL REFERENCES modulos(id),
    primeira_nota REAL,
    segunda_nota REAL,
    terceira_nota REAL,
    media_final REAL,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS financeiro (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    matricula_id INTEGER NOT NULL REFERENCES matriculas(id),
    valor_total REAL,
    valor_pago REAL DEFAULT 0,
    data_vencimento DATE,
    status TEXT DEFAULT 'pendente',
    parcelas INTEGER,
    descricao TEXT,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS parcelas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    financeiro_id INTEGER NOT NULL REFERENCES financeiro(id),
    numero_parcela INTEGER,
    valor_parcela REAL,
    data_vencimento DATE,
    data_pagamento DATE,
    status TEXT DEFAULT 'pendente',
    metodo_pagamento TEXT,
    observacao TEXT,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    senha TEXT NOT NULL,
    tipo_usuario TEXT NOT NULL,
    tabela_referencia TEXT,
    id_referencia INTEGER,
    ativo INTEGER DEFAULT 1,
    trocar_senha INTEGER DEFAULT 0,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS status_aluno (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aluno_id INTEGER NOT NULL REFERENCES alunos(id),
    status TEXT NOT NULL,
    motivo TEXT,
    data_atualizacao DATE,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS relatorios_aluno (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aluno_id INTEGER NOT NULL REFERENCES alunos(id),
    tipo TEXT,
    titulo TEXT,
    conteudo TEXT,
    criado_por INTEGER,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS anexos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aluno_id INTEGER NOT NULL REFERENCES alunos(id),
    tipo TEXT,
    titulo TEXT,
    arquivo TEXT,
    arquivo_nome TEXT,
    arquivo_tamanho INTEGER,
    arquivo_tipo TEXT,
    data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    usuario_tipo TEXT,
    acao TEXT,
    tabela_afetada TEXT,
    id_registro INTEGER,
    valores_antigos TEXT,
    valores_novos TEXT,
    data_acao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS salas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,
    nome TEXT NOT NULL,
    capacidade INTEGER,
    recursos TEXT,
    ativa INTEGER DEFAULT 1,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS cronograma (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    turma_id INTEGER NOT NULL REFERENCES turmas(id),
    titulo TEXT,
    descricao TEXT,
    data_evento DATE,
    hora_inicio TIME,
    hora_fim TIME,
    local TEXT,
    tipo TEXT,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_matriculas_turma ON matriculas(turma_id);
CREATE INDEX IF NOT EXISTS ix_parcelas_fin ON parcelas(financeiro_id);
CREATE INDEX IF NOT EXISTS ix_parcelas_venc ON parcelas(status, data_vencimento);
CREATE INDEX IF NOT EXISTS ix_status_aluno ON status_aluno(aluno_id);
CREATE INDEX IF NOT EXISTS ix_audit_data ON audit_log(data_acao);
"""


# ---------------------------------------------------------------- conexão
def conectar(caminho):
    con = sqlite3.connect(caminho)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def get_db():
    if "db" not in g:
        g.db = conectar(current_app.config["DATABASE"])
    return g.db


def fechar_db(exc=None):
    """Uma transação por requisição: grava se deu certo, desfaz se deu erro."""
    con = g.pop("db", None)
    if con is not None:
        if exc is None:
            con.commit()
        else:
            con.rollback()
        con.close()


def todos(sql, params=()):
    return get_db().execute(sql, params).fetchall()


def um(sql, params=()):
    return get_db().execute(sql, params).fetchone()


def valor(sql, params=(), padrao=0):
    linha = get_db().execute(sql, params).fetchone()
    return padrao if linha is None or linha[0] is None else linha[0]


def executar(sql, params=()):
    """Executa INSERT/UPDATE/DELETE e devolve o id gerado."""
    return get_db().execute(sql, params).lastrowid


# ---------------------------------------------------------------- regras
def recalcular_financeiro(con, financeiro_id):
    """Mantém financeiro.valor_pago/status coerentes com as parcelas."""
    total, pago, abertas = con.execute(
        """SELECT COALESCE(SUM(CASE WHEN status != 'cancelada' THEN valor_parcela END), 0),
                  COALESCE(SUM(CASE WHEN status = 'pago' THEN valor_parcela END), 0),
                  COALESCE(SUM(status = 'pendente'), 0)
           FROM parcelas WHERE financeiro_id = ?""", (financeiro_id,)).fetchone()
    if abertas == 0 and pago > 0:
        status = "pago"
    elif abertas == 0:
        status = "cancelado"
    else:
        status = "parcial" if pago > 0 else "pendente"
    con.execute("UPDATE financeiro SET valor_pago = ?, status = ? WHERE id = ?",
                (round(pago, 2), status, financeiro_id))


# ---------------------------------------------------------------- migrações
def _colunas(con, tabela):
    return {l[1] for l in con.execute(f"PRAGMA table_info({tabela})")}


def _migrar(con):
    novas = [
        ("usuarios", "trocar_senha", "INTEGER DEFAULT 0"),
        ("alunos", "responsavel", "TEXT"),
        ("alunos", "telefone_responsavel", "TEXT"),
        ("salas", "recursos", "TEXT"),
    ]
    for tabela, coluna, ddl in novas:
        if coluna not in _colunas(con, tabela):
            con.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {ddl}")

    # Remove duplicados antigos antes de criar os índices únicos.
    con.execute("""DELETE FROM frequencias WHERE id NOT IN
                   (SELECT MAX(id) FROM frequencias GROUP BY matricula_id, data_aula)""")
    con.execute("""DELETE FROM notas WHERE id NOT IN
                   (SELECT MAX(id) FROM notas GROUP BY matricula_id, modulo_id)""")
    con.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_freq ON frequencias(matricula_id, data_aula)")
    con.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_notas ON notas(matricula_id, modulo_id)")

    # Lançamentos antigos sem parcelas ganham parcelas equivalentes.
    sem_parcelas = con.execute(
        """SELECT * FROM financeiro f
           WHERE NOT EXISTS (SELECT 1 FROM parcelas p WHERE p.financeiro_id = f.id)""").fetchall()
    for f in sem_parcelas:
        total, pago = f["valor_total"] or 0, min(f["valor_pago"] or 0, f["valor_total"] or 0)
        venc = f["data_vencimento"] or date.today().isoformat()
        n = 0
        if pago > 0:
            n += 1
            con.execute("""INSERT INTO parcelas (financeiro_id, numero_parcela, valor_parcela,
                           data_vencimento, data_pagamento, status) VALUES (?,?,?,?,?, 'pago')""",
                        (f["id"], n, pago, venc, venc))
        if total - pago > 0.004:
            n += 1
            con.execute("""INSERT INTO parcelas (financeiro_id, numero_parcela, valor_parcela,
                           data_vencimento, status) VALUES (?,?,?,?, 'pendente')""",
                        (f["id"], n, round(total - pago, 2), venc))
    for (fid,) in con.execute("SELECT id FROM financeiro").fetchall():
        recalcular_financeiro(con, fid)


def iniciar_banco(app):
    """Cria as tabelas, aplica migrações e garante um administrador."""
    from auth import criar_admin_inicial

    os.makedirs(os.path.dirname(app.config["DATABASE"]), exist_ok=True)
    con = conectar(app.config["DATABASE"])
    try:
        con.executescript(SCHEMA)
        if con.execute("PRAGMA user_version").fetchone()[0] < VERSAO_SCHEMA:
            _migrar(con)
            con.execute(f"PRAGMA user_version = {VERSAO_SCHEMA}")
        criar_admin_inicial(con)
        con.commit()
    finally:
        con.close()
