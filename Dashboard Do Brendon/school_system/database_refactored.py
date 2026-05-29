"""
ARQUITETURA DE BANCO DE DADOS REFATORADA
Sistema de Gestão Escolar - v3.0
Engenheiro de Software: Sistema Profissional com Hierarquia de Permissões
"""

import sqlite3
from datetime import datetime, date

def criar_banco_refatorado():
    """
    Cria o banco de dados com relacionamentos corretos:
    Curso (1) -> Turma (N)
    Turma (1) -> Matricula (N) -> Aluno (N)
    Turma (1) -> Professor (N)
    Matricula (1) -> Parcela (N)
    Aluno (1) -> Observacao (N)
    """
    
    conexao = sqlite3.connect('escola.db')
    cursor = conexao.cursor()
    
    print("🔄 Criando schema refatorado...")
    
    # ============================================================================
    # TABELAS DE CONFIGURAÇÃO E SEGURANÇA
    # ============================================================================
    
    # Tabela de Setores/Departamentos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS setores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        descricao TEXT,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Tabela de Roles (Permissões)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        nivel_acesso INTEGER NOT NULL,
        descricao TEXT,
        permissoes TEXT,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # ============================================================================
    # TABELAS DE USUÁRIOS (HIERARQUIA UNIFICADA)
    # ============================================================================
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE,
        senha TEXT NOT NULL,
        tipo_usuario TEXT NOT NULL,
        role_id INTEGER,
        setor_id INTEGER,
        nome TEXT,
        cpf TEXT UNIQUE,
        telefone TEXT,
        ativo INTEGER DEFAULT 1,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (role_id) REFERENCES roles(id),
        FOREIGN KEY (setor_id) REFERENCES setores(id)
    )
    ''')
    
    # ============================================================================
    # TABELAS EDUCACIONAIS (ESTRUTURA PRINCIPAL)
    # ============================================================================
    
    # Cursos (Único, não duplicado)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cursos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        descricao TEXT,
        duracao_meses INTEGER NOT NULL,
        valor_mensal REAL NOT NULL,
        valor_total REAL NOT NULL,
        carga_horaria INTEGER,
        ativo INTEGER DEFAULT 1,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Turmas (Múltiplas por Curso)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS turmas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        curso_id INTEGER NOT NULL,
        professor_id INTEGER,
        nome TEXT NOT NULL,
        codigo TEXT NOT NULL UNIQUE,
        semestre TEXT,
        data_inicio DATE NOT NULL,
        data_fim DATE NOT NULL,
        horario TEXT,
        sala TEXT,
        capacidade INTEGER,
        ativa INTEGER DEFAULT 1,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (curso_id) REFERENCES cursos(id),
        FOREIGN KEY (professor_id) REFERENCES usuarios(id)
    )
    ''')
    
    # Professores (vinculado à tabela usuários)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS professores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL UNIQUE,
        formacao TEXT,
        especialidade TEXT,
        ativo INTEGER DEFAULT 1,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    )
    ''')
    
    # Alunos (vinculado à tabela usuários)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS alunos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL UNIQUE,
        data_nascimento DATE,
        endereco TEXT,
        cidade TEXT,
        estado TEXT,
        cep TEXT,
        responsavel_nome TEXT,
        responsavel_telefone TEXT,
        ativo INTEGER DEFAULT 1,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    )
    ''')
    
    # ============================================================================
    # TABELAS DE MATRÍCULA E RELACIONAMENTO
    # ============================================================================
    
    # Matrículas (Conecta Aluno -> Turma)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS matriculas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER NOT NULL,
        turma_id INTEGER NOT NULL,
        data_matricula DATE NOT NULL,
        status TEXT DEFAULT 'ativa',
        valor_total REAL NOT NULL,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (aluno_id) REFERENCES alunos(id),
        FOREIGN KEY (turma_id) REFERENCES turmas(id),
        UNIQUE(aluno_id, turma_id)
    )
    ''')
    
    # ============================================================================
    # TABELAS FINANCEIRAS
    # ============================================================================
    
    # Parcelas/Mensalidades (Geradas automaticamente na matrícula)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS parcelas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matricula_id INTEGER NOT NULL,
        numero_parcela INTEGER NOT NULL,
        valor REAL NOT NULL,
        data_vencimento DATE NOT NULL,
        data_pagamento DATE,
        status TEXT DEFAULT 'pendente',
        metodo_pagamento TEXT,
        comprovante TEXT,
        observacoes TEXT,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        data_atualizacao TIMESTAMP,
        FOREIGN KEY (matricula_id) REFERENCES matriculas(id)
    )
    ''')
    
    # ============================================================================
    # TABELAS PEDAGÓGICAS
    # ============================================================================
    
    # Frequência (Chamada)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS frequencias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matricula_id INTEGER NOT NULL,
        turma_id INTEGER NOT NULL,
        data_aula DATE NOT NULL,
        presente INTEGER DEFAULT 0,
        justificativa TEXT,
        registrado_por INTEGER,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (matricula_id) REFERENCES matriculas(id),
        FOREIGN KEY (turma_id) REFERENCES turmas(id),
        FOREIGN KEY (registrado_por) REFERENCES usuarios(id)
    )
    ''')
    
    # Notas/Avaliações
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matricula_id INTEGER NOT NULL,
        turma_id INTEGER NOT NULL,
        bimestre INTEGER,
        nota_1 REAL,
        nota_2 REAL,
        nota_3 REAL,
        media_final REAL,
        status TEXT,
        registrado_por INTEGER,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        data_atualizacao TIMESTAMP,
        FOREIGN KEY (matricula_id) REFERENCES matriculas(id),
        FOREIGN KEY (turma_id) REFERENCES turmas(id),
        FOREIGN KEY (registrado_por) REFERENCES usuarios(id)
    )
    ''')
    
    # ============================================================================
    # TABELAS DE OBSERVAÇÕES E HISTÓRICO (NOVO)
    # ============================================================================
    
    # Observações/Ocorrências do Aluno
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS observacoes_aluno (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER NOT NULL,
        tipo TEXT,
        titulo TEXT NOT NULL,
        descricao TEXT NOT NULL,
        registrado_por INTEGER NOT NULL,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (aluno_id) REFERENCES alunos(id),
        FOREIGN KEY (registrado_por) REFERENCES usuarios(id)
    )
    ''')
    
    # Histórico de Ações (Auditoria)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        acao TEXT NOT NULL,
        tabela TEXT NOT NULL,
        registro_id INTEGER,
        valores_anteriores TEXT,
        valores_novos TEXT,
        data_acao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conexao.commit()
    print("✅ Banco de dados refatorado criado com sucesso!")
    
    # ============================================================================
    # INSERIR DADOS PADRÃO
    # ============================================================================
    
    # Setores
    setores_padrao = [
        ('Diretoria', 'Diretoria/Administração'),
        ('Comercial', 'Vendas e Matrículas'),
        ('Financeiro', 'Controladoria e Finanças'),
        ('Pedagógico', 'Coordenação Pedagógica'),
    ]
    
    for nome, desc in setores_padrao:
        cursor.execute('''
        INSERT OR IGNORE INTO setores (nome, descricao) VALUES (?, ?)
        ''', (nome, desc))
    
    # Roles com Hierarquia
    roles_padrao = [
        ('admin', 100, 'Administrador - Acesso Total', 'CREATE,READ,UPDATE,DELETE,FINANCIAL,ACADEMIC'),
        ('diretoria', 90, 'Diretoria - Acesso Amplo', 'CREATE,READ,UPDATE,ACADEMIC,FINANCIAL_READ'),
        ('comercial', 40, 'Comercial - Vendas', 'READ,CREATE_ALUNO,MATRICULA,FINANCIAL_PAYMENT'),
        ('pedagogo', 60, 'Coordenador Pedagógico', 'READ,UPDATE_ALUNO,ACADEMIC,OBSERVACAO'),
        ('professor', 20, 'Professor - Acesso Limitado', 'READ_TURMA,FREQUENCIA,NOTAS,OBSERVACAO'),
        ('aluno', 10, 'Aluno - Acesso Pessoal', 'READ_PROPRIO'),
    ]
    
    for nome, nivel, desc, perms in roles_padrao:
        cursor.execute('''
        INSERT OR IGNORE INTO roles (nome, nivel_acesso, descricao, permissoes) 
        VALUES (?, ?, ?, ?)
        ''', (nome, nivel, desc, perms))
    
    conexao.commit()
    conexao.close()
    
    print("📊 Dados padrão inseridos!")
    print("✨ Schema refatorado pronto para uso!")

if __name__ == "__main__":
    criar_banco_refatorado()
