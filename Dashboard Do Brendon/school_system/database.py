"""
BANCO DE DADOS - SCHEMA DO SISTEMA DE GESTÃO DE ESCOLA
Cria todas as tabelas necessárias para o sistema funcionar
"""

import sqlite3
from datetime import datetime

def criar_banco_dados():
    """Cria o banco de dados e todas as tabelas"""
    
    conexao = sqlite3.connect('escola.db')
    cursor = conexao.cursor()
    
    # ========== TABELA DE SETORES ==========
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS setores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        descricao TEXT,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # ========== TABELA DE FUNCIONÁRIOS ==========
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS funcionarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        cpf TEXT NOT NULL UNIQUE,
        senha TEXT NOT NULL,
        cargo TEXT NOT NULL,
        setor_id INTEGER,
        salario REAL,
        data_admissao DATE,
        ativo INTEGER DEFAULT 1,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (setor_id) REFERENCES setores(id)
    )
    ''')
    
    # ========== TABELA DE PROFESSORES ==========
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS professores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        cpf TEXT NOT NULL UNIQUE,
        senha TEXT NOT NULL,
        matricula TEXT NOT NULL UNIQUE,
        formacao TEXT,
        especialidade TEXT,
        ativo INTEGER DEFAULT 1,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # ========== TABELA DE CURSOS ==========
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cursos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        descricao TEXT,
        duracao_meses INTEGER,
        valor REAL,
        ativo INTEGER DEFAULT 1,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # ========== TABELA DE MÓDULOS ==========
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS modulos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        curso_id INTEGER NOT NULL,
        nome TEXT NOT NULL,
        descricao TEXT,
        carga_horaria INTEGER,
        ordem INTEGER,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (curso_id) REFERENCES cursos(id)
    )
    ''')
    
    # ========== TABELA DE TURMAS ==========
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS turmas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT NOT NULL UNIQUE,
        nome TEXT NOT NULL,
        curso_id INTEGER NOT NULL,
        professor_id INTEGER NOT NULL,
        semestre TEXT,
        data_inicio DATE,
        data_fim DATE,
        horario TEXT,
        sala TEXT,
        capacidade INTEGER,
        ativa INTEGER DEFAULT 1,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (curso_id) REFERENCES cursos(id),
        FOREIGN KEY (professor_id) REFERENCES professores(id)
    )
    ''')
    
    # ========== TABELA DE ALUNOS ==========
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS alunos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        cpf TEXT NOT NULL UNIQUE,
        senha TEXT NOT NULL,
        matricula TEXT NOT NULL UNIQUE,
        data_nascimento DATE,
        telefone TEXT,
        endereco TEXT,
        cidade TEXT,
        estado TEXT,
        ativo INTEGER DEFAULT 1,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # ========== TABELA DE MATRÍCULAS ==========
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS matriculas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER NOT NULL,
        turma_id INTEGER NOT NULL,
        data_matricula DATE,
        status TEXT DEFAULT 'ativa',
        data_conclusao DATE,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (aluno_id) REFERENCES alunos(id),
        FOREIGN KEY (turma_id) REFERENCES turmas(id),
        UNIQUE(aluno_id, turma_id)
    )
    ''')
    
    # ========== TABELA DE FREQUÊNCIA ==========
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS frequencias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matricula_id INTEGER NOT NULL,
        data_aula DATE,
        presente INTEGER,
        justificativa TEXT,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (matricula_id) REFERENCES matriculas(id)
    )
    ''')
    
    # ========== TABELA DE NOTAS ==========
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matricula_id INTEGER NOT NULL,
        modulo_id INTEGER NOT NULL,
        primeira_nota REAL,
        segunda_nota REAL,
        terceira_nota REAL,
        media_final REAL,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (matricula_id) REFERENCES matriculas(id),
        FOREIGN KEY (modulo_id) REFERENCES modulos(id)
    )
    ''')
    
    # ========== TABELA DE OBSERVAÇÕES PEDAGÓGICAS ==========
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS observacoes_pedagogicas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matricula_id INTEGER NOT NULL,
        professor_id INTEGER NOT NULL,
        texto TEXT,
        data_observacao DATE,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (matricula_id) REFERENCES matriculas(id),
        FOREIGN KEY (professor_id) REFERENCES professores(id)
    )
    ''')
    
    # ========== TABELA DE MATERIAL DIDÁTICO ==========
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS materiais (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        modulo_id INTEGER NOT NULL,
        nome TEXT NOT NULL,
        descricao TEXT,
        tipo TEXT,
        arquivo TEXT,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (modulo_id) REFERENCES modulos(id)
    )
    ''')
    
    # ========== TABELA DE FINANCEIRO ==========
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS financeiro (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matricula_id INTEGER NOT NULL,
        valor_total REAL,
        valor_pago REAL DEFAULT 0,
        data_vencimento DATE,
        status TEXT DEFAULT 'pendente',
        parcelas INTEGER,
        descricao TEXT,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (matricula_id) REFERENCES matriculas(id)
    )
    ''')
    
    # ========== TABELA DE PAGAMENTOS ==========
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pagamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        financeiro_id INTEGER NOT NULL,
        valor REAL,
        data_pagamento DATE,
        metodo_pagamento TEXT,
        observacao TEXT,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (financeiro_id) REFERENCES financeiro(id)
    )
    ''')
    
    # ========== TABELA DE CONTROLE COMERCIAL ==========
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS controle_comercial (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        turma_id INTEGER NOT NULL,
        total_vagas INTEGER,
        vagas_preenchidas INTEGER,
        vagas_disponiveis INTEGER,
        valor_aula REAL,
        descontos_aplicados TEXT,
        faturamento_previsto REAL,
        faturamento_realizado REAL,
        mes_ano TEXT,
        data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (turma_id) REFERENCES turmas(id)
    )
    ''')
    
    # ========== TABELA DE USUÁRIOS (Para login) ==========
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE,
        senha TEXT NOT NULL,
        tipo_usuario TEXT NOT NULL,
        tabela_referencia TEXT,
        id_referencia INTEGER,
        ativo INTEGER DEFAULT 1,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conexao.commit()
    conexao.close()
    print("[OK] Banco de dados criado com sucesso!")

if __name__ == "__main__":
    criar_banco_dados()
