"""
BANCO DE DADOS EXPANDIDO - SCHEMA COMPLETO
"""

import sqlite3
from datetime import datetime

def criar_banco_dados_v2():
    """Cria banco com todas as tabelas necessárias"""
    
    conexao = sqlite3.connect('escola.db')
    cursor = conexao.cursor()
    
    # Tabelas existentes (mantém)
    # ... (todas as tabelas anteriores)
    
    # ========== NOVAS TABELAS ==========
    
    # Status do Aluno
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS status_aluno (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        motivo TEXT,
        data_atualizacao DATE,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (aluno_id) REFERENCES alunos(id)
    )
    ''')
    
    # Relatórios do Aluno
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS relatorios_aluno (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER NOT NULL,
        tipo TEXT,
        titulo TEXT,
        conteudo TEXT,
        criado_por INTEGER,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (aluno_id) REFERENCES alunos(id),
        FOREIGN KEY (criado_por) REFERENCES funcionarios(id)
    )
    ''')
    
    # Anexos (Documentos, fotos, contratos)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS anexos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER NOT NULL,
        tipo TEXT,
        titulo TEXT,
        arquivo TEXT,
        arquivo_nome TEXT,
        arquivo_tamanho INTEGER,
        arquivo_tipo TEXT,
        data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (aluno_id) REFERENCES alunos(id)
    )
    ''')
    
    # Logs e Auditoria
    cursor.execute('''
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
    )
    ''')
    
    # Parcelas de Financeiro
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS parcelas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        financeiro_id INTEGER NOT NULL,
        numero_parcela INTEGER,
        valor_parcela REAL,
        data_vencimento DATE,
        data_pagamento DATE,
        status TEXT DEFAULT 'pendente',
        metodo_pagamento TEXT,
        observacao TEXT,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (financeiro_id) REFERENCES financeiro(id)
    )
    ''')
    
    # Salas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS salas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT NOT NULL UNIQUE,
        nome TEXT NOT NULL,
        capacidade INTEGER,
        recurso s TEXT,
        ativa INTEGER DEFAULT 1,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Cronograma/Calendário
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cronograma (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        turma_id INTEGER NOT NULL,
        titulo TEXT,
        descricao TEXT,
        data_evento DATE,
        hora_inicio TIME,
        hora_fim TIME,
        local TEXT,
        tipo TEXT,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (turma_id) REFERENCES turmas(id)
    )
    ''')
    
    # Histórico de Matrículas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS historico_matriculas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER NOT NULL,
        turma_id INTEGER NOT NULL,
        data_inicio DATE,
        data_fim DATE,
        status TEXT,
        motivo_saida TEXT,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (aluno_id) REFERENCES alunos(id),
        FOREIGN KEY (turma_id) REFERENCES turmas(id)
    )
    ''')
    
    # Permissões por Departamento
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS departamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        descricao TEXT,
        ativo INTEGER DEFAULT 1,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Acesso do Usuário por Departamento
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuario_departamento (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        usuario_tipo TEXT,
        departamento_id INTEGER,
        permissoes TEXT,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (departamento_id) REFERENCES departamentos(id)
    )
    ''')
    
    # Contatos Aluno
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS contatos_aluno (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER NOT NULL,
        tipo_contato TEXT,
        nome_contato TEXT,
        telefone TEXT,
        email TEXT,
        parentesco TEXT,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (aluno_id) REFERENCES alunos(id)
    )
    ''')
    
    # Endereço Aluno
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS endereco_aluno (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER NOT NULL,
        rua TEXT,
        numero TEXT,
        complemento TEXT,
        bairro TEXT,
        cidade TEXT,
        estado TEXT,
        cep TEXT,
        tipo TEXT,
        principal INTEGER DEFAULT 0,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (aluno_id) REFERENCES alunos(id)
    )
    ''')
    
    conexao.commit()
    conexao.close()
    print("[OK] Banco de dados v2 criado com sucesso!")

if __name__ == "__main__":
    criar_banco_dados_v2()
