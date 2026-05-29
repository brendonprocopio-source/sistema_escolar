"""
SCRIPT DE INICIALIZAÇÃO DO BANCO DE DADOS COM DADOS DE TESTE - COMPLETO
Popula o banco com dados de exemplo incluindo todos os usuários
"""

import sqlite3
from autenticacao_standalone import Autenticacao
from datetime import datetime, date, timedelta

def popular_banco_dados():
    """Popula o banco com dados de teste"""
    
    conexao = sqlite3.connect('escola.db')
    cursor = conexao.cursor()
    
    print("Populando banco de dados com dados de teste completo...")
    
    # ========== SETORES ==========
    setores = [
        ('Administrativo', 'Setor administrativo da escola'),
        ('Pedagogico', 'Setor responsavel pelo ensino'),
        ('Financeiro', 'Setor de financas e cobrancas'),
        ('Comercial', 'Setor de vendas e matrículas'),
    ]
    
    for nome, descricao in setores:
        cursor.execute('''
        INSERT OR IGNORE INTO setores (nome, descricao) VALUES (?, ?)
        ''', (nome, descricao))
    
    # ========== FUNCIONÁRIOS ==========
    # Admin
    cursor.execute('''
    INSERT OR IGNORE INTO funcionarios 
    (nome, email, cpf, senha, cargo, setor_id, salario)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('Admin Sistema', 'admin@escola.com', '00000000000', 
          Autenticacao.hash_senha('Mudar@123'), 'Administrador', 1, 3000))
    
    # Funcionário Comercial
    cursor.execute('''
    INSERT OR IGNORE INTO funcionarios 
    (nome, email, cpf, senha, cargo, setor_id, salario)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('Carlos Comercial', 'comercial@escola.com', '99999999999', 
          Autenticacao.hash_senha('Comercial@123'), 'Vendedor', 4, 2000))
    
    # Funcionário Financeiro
    cursor.execute('''
    INSERT OR IGNORE INTO funcionarios 
    (nome, email, cpf, senha, cargo, setor_id, salario)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('Beatriz Financeiro', 'financeiro@escola.com', '88888888888', 
          Autenticacao.hash_senha('Financeiro@123'), 'Analista Financeiro', 3, 2200))
    
    # Funcionário Pedagógico
    cursor.execute('''
    INSERT OR IGNORE INTO funcionarios 
    (nome, email, cpf, senha, cargo, setor_id, salario)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('Diana Pedagogico', 'pedagogico@escola.com', '77777777777', 
          Autenticacao.hash_senha('Pedagogico@123'), 'Coordenador Pedagógico', 2, 2500))
    
    # ========== USUÁRIOS FUNCIONÁRIOS ==========
    cursor.execute('''
    INSERT OR IGNORE INTO usuarios 
    (email, senha, tipo_usuario, tabela_referencia, id_referencia)
    VALUES (?, ?, ?, ?, ?)
    ''', ('admin@escola.com', Autenticacao.hash_senha('Mudar@123'), 'admin', 'funcionarios', 1))
    
    cursor.execute('''
    INSERT OR IGNORE INTO usuarios 
    (email, senha, tipo_usuario, tabela_referencia, id_referencia)
    VALUES (?, ?, ?, ?, ?)
    ''', ('comercial@escola.com', Autenticacao.hash_senha('Comercial@123'), 'funcionario', 'funcionarios', 2))
    
    cursor.execute('''
    INSERT OR IGNORE INTO usuarios 
    (email, senha, tipo_usuario, tabela_referencia, id_referencia)
    VALUES (?, ?, ?, ?, ?)
    ''', ('financeiro@escola.com', Autenticacao.hash_senha('Financeiro@123'), 'funcionario', 'funcionarios', 3))
    
    cursor.execute('''
    INSERT OR IGNORE INTO usuarios 
    (email, senha, tipo_usuario, tabela_referencia, id_referencia)
    VALUES (?, ?, ?, ?, ?)
    ''', ('pedagogico@escola.com', Autenticacao.hash_senha('Pedagogico@123'), 'funcionario', 'funcionarios', 4))
    
    # ========== PROFESSORES ==========
    professores = [
        ('Ana Silva', 'ana@escola.com', '12345678901', 'PROF001', 'Licenciatura em Matematica', 'Matematica'),
        ('Carlos Santos', 'carlos@escola.com', '12345678902', 'PROF002', 'Licenciatura em Portugues', 'Portugues'),
        ('Maria Oliveira', 'maria@escola.com', '12345678903', 'PROF003', 'Engenharia de Sistemas', 'Programacao'),
    ]
    
    for nome, email, cpf, matricula, formacao, especialidade in professores:
        cursor.execute('''
        INSERT OR IGNORE INTO professores 
        (nome, email, cpf, senha, matricula, formacao, especialidade)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (nome, email, cpf, Autenticacao.hash_senha('Prof@123'), matricula, formacao, especialidade))
    
    # ========== USUÁRIOS PROFESSORES ==========
    prof_ids = [1, 2, 3]
    prof_emails = ['ana@escola.com', 'carlos@escola.com', 'maria@escola.com']
    
    for prof_id, email in zip(prof_ids, prof_emails):
        cursor.execute('''
        INSERT OR IGNORE INTO usuarios 
        (email, senha, tipo_usuario, tabela_referencia, id_referencia)
        VALUES (?, ?, ?, ?, ?)
        ''', (email, Autenticacao.hash_senha('Prof@123'), 'professor', 'professores', prof_id))
    
    # ========== CURSOS ==========
    cursos = [
        ('Matematica Basica', 'Curso de matematica fundamental', 2, 500),
        ('Portugues Avancado', 'Curso de portugues para concursos', 3, 600),
        ('Python para Iniciantes', 'Aprenda programacao com Python', 4, 800),
    ]
    
    for nome, descricao, duracao, valor in cursos:
        cursor.execute('''
        INSERT OR IGNORE INTO cursos (nome, descricao, duracao_meses, valor)
        VALUES (?, ?, ?, ?)
        ''', (nome, descricao, duracao, valor))
    
    # ========== MODULOS ==========
    modulos = [
        (1, 'Operacoes Basicas', 'Adicao, subtracao, multiplicacao e divisao', 20, 1),
        (1, 'Fracoes e Decimais', 'Trabalho com fracoes e numeros decimais', 20, 2),
        (3, 'Variaveis e Tipos', 'Introducao a variaveis em Python', 16, 1),
        (3, 'Estruturas de Controle', 'IF, ELSE, FOR, WHILE', 24, 2),
    ]
    
    for curso_id, nome, descricao, carga_horaria, ordem in modulos:
        cursor.execute('''
        INSERT OR IGNORE INTO modulos 
        (curso_id, nome, descricao, carga_horaria, ordem)
        VALUES (?, ?, ?, ?, ?)
        ''', (curso_id, nome, descricao, carga_horaria, ordem))
    
    # ========== TURMAS ==========
    turmas = [
        ('TUR001', 'Turma A - Matematica', 1, 1, '2024.1', date(2024, 1, 10), date(2024, 3, 10), '19:00-21:00', 'Sala 101', 30),
        ('TUR002', 'Turma B - Portugues', 2, 2, '2024.1', date(2024, 1, 15), date(2024, 4, 15), '19:00-21:00', 'Sala 102', 25),
        ('TUR003', 'Turma A - Python', 3, 3, '2024.1', date(2024, 1, 8), date(2024, 5, 8), '20:00-22:00', 'Lab 01', 20),
    ]
    
    for codigo, nome, curso_id, professor_id, semestre, data_inicio, data_fim, horario, sala, capacidade in turmas:
        cursor.execute('''
        INSERT OR IGNORE INTO turmas 
        (codigo, nome, curso_id, professor_id, semestre, data_inicio, data_fim, horario, sala, capacidade)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (codigo, nome, curso_id, professor_id, semestre, data_inicio, data_fim, horario, sala, capacidade))
    
    # ========== ALUNOS ==========
    alunos = [
        ('Joao Silva', 'joao@escola.com', '11111111111', 'ALN001', date(1995, 5, 15), '(11) 98765-4321'),
        ('Maria Santos', 'maria.santos@escola.com', '22222222222', 'ALN002', date(1998, 8, 22), '(11) 99876-5432'),
        ('Pedro Oliveira', 'pedro@escola.com', '33333333333', 'ALN003', date(2000, 3, 10), '(11) 97654-3210'),
        ('Ana Costa', 'ana.costa@escola.com', '44444444444', 'ALN004', date(1996, 7, 18), '(11) 98765-4321'),
    ]
    
    for nome, email, cpf, matricula, data_nascimento, telefone in alunos:
        cursor.execute('''
        INSERT OR IGNORE INTO alunos 
        (nome, email, cpf, senha, matricula, data_nascimento, telefone)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (nome, email, cpf, Autenticacao.hash_senha('Aluno@123'), matricula, data_nascimento, telefone))
    
    # ========== USUÁRIOS ALUNOS ==========
    aluno_emails = ['joao@escola.com', 'maria.santos@escola.com', 'pedro@escola.com', 'ana.costa@escola.com']
    aluno_ids = [1, 2, 3, 4]
    
    for aluno_id, email in zip(aluno_ids, aluno_emails):
        cursor.execute('''
        INSERT OR IGNORE INTO usuarios 
        (email, senha, tipo_usuario, tabela_referencia, id_referencia)
        VALUES (?, ?, ?, ?, ?)
        ''', (email, Autenticacao.hash_senha('Aluno@123'), 'aluno', 'alunos', aluno_id))
    
    # ========== MATRICULAS ==========
    cursor.execute('SELECT id FROM turmas LIMIT 3')
    turma_ids = [row[0] for row in cursor.fetchall()]
    
    matriculas = [
        (1, turma_ids[0], date(2024, 1, 9)),
        (2, turma_ids[0], date(2024, 1, 9)),
        (3, turma_ids[1], date(2024, 1, 14)),
        (4, turma_ids[2], date(2024, 1, 7)),
    ]
    
    for aluno_id, turma_id, data_matricula in matriculas:
        cursor.execute('''
        INSERT OR IGNORE INTO matriculas 
        (aluno_id, turma_id, data_matricula, status)
        VALUES (?, ?, ?, 'ativa')
        ''', (aluno_id, turma_id, data_matricula))
    
    # ========== STATUS DOS ALUNOS ==========
    for aluno_id in aluno_ids:
        cursor.execute('''
        INSERT OR IGNORE INTO status_aluno (aluno_id, status, data_atualizacao)
        VALUES (?, ?, ?)
        ''', (aluno_id, 'Frequente', date.today()))
    
    # ========== FREQUENCIAS ==========
    cursor.execute('SELECT id FROM matriculas LIMIT 4')
    matricula_ids = [row[0] for row in cursor.fetchall()]
    
    for i, matricula_id in enumerate(matricula_ids):
        for dia in range(1, 16):  # 15 dias de aula
            data_aula = date(2024, 1, 8) + timedelta(days=dia*2)
            presente = 1 if dia % 3 != 0 else 0  # Falta a cada 3 dias
            
            cursor.execute('''
            INSERT OR IGNORE INTO frequencias 
            (matricula_id, data_aula, presente)
            VALUES (?, ?, ?)
            ''', (matricula_id, data_aula, presente))
    
    # ========== NOTAS ==========
    cursor.execute('SELECT id FROM modulos LIMIT 4')
    modulos_ids = [row[0] for row in cursor.fetchall()]
    
    for matricula_id in matricula_ids[:len(modulos_ids)]:
        for idx, modulo_id in enumerate(modulos_ids[:2]):
            primeira = 7.5 + idx
            segunda = 8.0 + idx
            terceira = 8.5 + idx
            media = (primeira + segunda + terceira) / 3
            
            cursor.execute('''
            INSERT OR IGNORE INTO notas 
            (matricula_id, modulo_id, primeira_nota, segunda_nota, terceira_nota, media_final)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (matricula_id, modulo_id, primeira, segunda, terceira, media))
    
    # ========== FINANCEIRO E PARCELAS ==========
    for matricula_id in matricula_ids:
        valor_total = 800
        
        cursor.execute('''
        INSERT OR IGNORE INTO financeiro 
        (matricula_id, valor_total, valor_pago, data_vencimento, status, parcelas, descricao)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (matricula_id, valor_total, 400, date(2024, 2, 10), 'pendente', 2, 'Matrícula'))
        
        # Obter ID do financeiro criado
        cursor.execute('SELECT last_insert_rowid()')
        financeiro_id = cursor.fetchone()[0]
        
        # Criar parcelas
        valor_parcela = valor_total / 2
        for i in range(2):
            data_vencimento = date(2024, 2, 10) + timedelta(days=30 * (i + 1))
            status_parcela = 'pago' if i == 0 else 'pendente'
            data_pagamento = date(2024, 2, 8) if i == 0 else None
            
            cursor.execute('''
            INSERT OR IGNORE INTO parcelas 
            (financeiro_id, numero_parcela, valor_parcela, data_vencimento, status, data_pagamento, metodo_pagamento)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (financeiro_id, i + 1, valor_parcela, data_vencimento, status_parcela, data_pagamento, 'dinheiro' if i == 0 else None))
    
    conexao.commit()
    conexao.close()
    
    print("[OK] Banco de dados populado com sucesso!")
    print("")
    print("=" * 70)
    print("CREDENCIAIS DE ACESSO")
    print("=" * 70)
    print("")
    print("👤 ADMIN:")
    print("   Email: admin@escola.com")
    print("   Senha: Mudar@123")
    print("")
    print("👔 FUNCIONÁRIOS:")
    print("   Comercial: comercial@escola.com / Comercial@123")
    print("   Financeiro: financeiro@escola.com / Financeiro@123")
    print("   Pedagógico: pedagogico@escola.com / Pedagogico@123")
    print("")
    print("👨‍🏫 PROFESSORES:")
    print("   Ana: ana@escola.com / Prof@123")
    print("   Carlos: carlos@escola.com / Prof@123")
    print("   Maria: maria@escola.com / Prof@123")
    print("")
    print("👨‍🎓 ALUNOS:")
    print("   João: joao@escola.com / Aluno@123")
    print("   Maria: maria.santos@escola.com / Aluno@123")
    print("   Pedro: pedro@escola.com / Aluno@123")
    print("   Ana: ana.costa@escola.com / Aluno@123")
    print("")
    print("=" * 70)

if __name__ == "__main__":
    popular_banco_dados()
