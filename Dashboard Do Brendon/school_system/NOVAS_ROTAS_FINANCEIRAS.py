"""
NOVAS ROTAS FINANCEIRAS E DE ALUNOS - ADD AO app.py
Expandir sistema financeiro com checkins, comprovantes, etc
"""

# ADICIONAR ESTAS ROTAS ANTES DE: if __name__ == '__main__':

# ============================================================================
# NOVO ALUNO COM FINANCEIRO AUTOMÁTICO
# ============================================================================

@app.route('/aluno/novo/completo', methods=['GET', 'POST'])
@login_requerido()
def novo_aluno_completo():
    """Novo aluno com curso, parcelas e financeiro automático"""
    if not pode_acessar('admin', 'funcionario'):
        flash('Acesso negado!', 'error')
        return redirect('/dashboard')
    
    if request.method == 'POST':
        try:
            # Dados do aluno
            nome = request.form.get('nome')
            email = request.form.get('email')
            cpf = request.form.get('cpf')
            senha = request.form.get('senha')
            telefone = request.form.get('telefone')
            data_nascimento = request.form.get('data_nascimento')
            
            # Dados financeiros
            curso_id = request.form.get('curso_id')
            parcelas = int(request.form.get('parcelas', 1))
            valor_custom = request.form.get('valor_custom')
            turma_id = request.form.get('turma_id')
            
            conexao = get_db()
            cursor = conexao.cursor()
            
            # 1. Criar aluno
            cursor.execute('''
            INSERT INTO alunos (nome, email, cpf, senha, matricula, data_nascimento, telefone)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (nome, email, cpf, Autenticacao.hash_senha(senha),
                  f"ALN{int(datetime.now().timestamp())}", data_nascimento, telefone))
            
            aluno_id = cursor.lastrowid
            
            # 2. Criar usuário
            cursor.execute('''
            INSERT INTO usuarios (email, senha, tipo_usuario, tabela_referencia, id_referencia)
            VALUES (?, ?, ?, ?, ?)
            ''', (email, Autenticacao.hash_senha(senha), 'aluno', 'alunos', aluno_id))
            
            # 3. Criar status inicial
            cursor.execute('''
            INSERT INTO status_aluno (aluno_id, status, data_atualizacao)
            VALUES (?, ?, ?)
            ''', (aluno_id, 'Não Iniciou', date.today()))
            
            # 4. Se selecionou curso, criar matrícula e financeiro
            if curso_id and turma_id:
                cursor.execute('''
                INSERT INTO matriculas (aluno_id, turma_id, data_matricula, status)
                VALUES (?, ?, ?, ?)
                ''', (aluno_id, turma_id, date.today(), 'ativa'))
                
                matricula_id = cursor.lastrowid
                
                # Buscar valor do curso ou usar valor customizado
                if valor_custom:
                    valor_total = float(valor_custom)
                else:
                    cursor.execute('SELECT valor FROM cursos WHERE id = ?', (curso_id,))
                    result = cursor.fetchone()
                    valor_total = result[0] if result else 0
                
                # Criar financeiro
                cursor.execute('''
                INSERT INTO financeiro (matricula_id, valor_total, data_vencimento, status, parcelas, descricao)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (matricula_id, valor_total, date.today() + timedelta(days=30), 'pendente', parcelas, 'Matrícula'))
                
                # Criar parcelas
                valor_parcela = valor_total / parcelas
                for i in range(parcelas):
                    data_vencimento = date.today() + timedelta(days=30 * (i + 1))
                    cursor.execute('''
                    INSERT INTO parcelas (financeiro_id, numero_parcela, valor_parcela, data_vencimento, status)
                    VALUES (?, ?, ?, ?, ?)
                    ''', (matricula_id, i + 1, valor_parcela, data_vencimento, 'pendente'))
            
            conexao.commit()
            conexao.close()
            
            flash(f'Aluno criado com sucesso! Email: {email} | Senha: {senha}', 'success')
            registrar_audit(session.get('usuario_id'), session.get('tipo_usuario'), 'CRIAR_ALUNO_COMPLETO', 'alunos', aluno_id, {})
            return redirect('/alunos')
        
        except Exception as e:
            flash(f'Erro: {str(e)}', 'error')
    
    cursos = executar_query('SELECT id, nome, valor FROM cursos WHERE ativo = 1')
    turmas = executar_query('SELECT id, nome FROM turmas WHERE ativa = 1')
    
    return render_template('alunos/novo_completo.html',
                         cursos=[dict(c) for c in cursos] if cursos else [],
                         turmas=[dict(t) for t in turmas] if turmas else [])

# ============================================================================
# SISTEMA DE COMPROVANTE DE PAGAMENTO
# ============================================================================

@app.route('/comercial/comprovante/<int:parcela_id>')
@login_requerido()
def gerar_comprovante_pagamento(parcela_id):
    """Gera comprovante de pagamento da parcela"""
    if not pode_acessar('admin', 'funcionario'):
        flash('Acesso negado!', 'error')
        return redirect('/comercial/financeiro')
    
    parcela = executar_query('''
    SELECT p.*, f.id as financeiro_id, f.parcelas as total_parcelas
    FROM parcelas p
    JOIN financeiro f ON p.financeiro_id = f.id
    WHERE p.id = ?
    ''', (parcela_id,), fetch_one=True)
    
    if not parcela:
        flash('Parcela não encontrada!', 'error')
        return redirect('/comercial/financeiro')
    
    financeiro = executar_query('''
    SELECT f.*, m.aluno_id, a.nome as aluno_nome, t.nome as turma_nome, c.nome as curso_nome
    FROM financeiro f
    JOIN matriculas m ON f.matricula_id = m.id
    JOIN alunos a ON m.aluno_id = a.id
    JOIN turmas t ON m.turma_id = t.id
    JOIN cursos c ON t.curso_id = c.id
    WHERE f.id = ?
    ''', (parcela['financeiro_id'],), fetch_one=True)
    
    return render_template('comercial/comprovante.html',
                         parcela=dict(parcela),
                         financeiro=dict(financeiro) if financeiro else {})

# ============================================================================
# CHECKOUT/CARRINHO DE MATRÍCULA
# ============================================================================

@app.route('/comercial/checkout/<int:aluno_id>', methods=['GET', 'POST'])
@login_requerido()
def checkout_matricula(aluno_id):
    """Checkout de matrícula com review de dados"""
    if not pode_acessar('admin', 'funcionario'):
        flash('Acesso negado!', 'error')
        return redirect('/dashboard')
    
    aluno = executar_query('SELECT * FROM alunos WHERE id = ?', (aluno_id,), fetch_one=True)
    if not aluno:
        flash('Aluno não encontrado!', 'error')
        return redirect('/alunos')
    
    if request.method == 'POST':
        turma_id = request.form.get('turma_id')
        valor = float(request.form.get('valor'))
        parcelas = int(request.form.get('parcelas'))
        
        try:
            conexao = get_db()
            cursor = conexao.cursor()
            
            # Criar matrícula
            cursor.execute('''
            INSERT INTO matriculas (aluno_id, turma_id, data_matricula, status)
            VALUES (?, ?, ?, ?)
            ''', (aluno_id, turma_id, date.today(), 'ativa'))
            
            matricula_id = cursor.lastrowid
            
            # Criar financeiro
            cursor.execute('''
            INSERT INTO financeiro (matricula_id, valor_total, data_vencimento, status, parcelas, descricao)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (matricula_id, valor, date.today() + timedelta(days=30), 'pendente', parcelas, 'Matrícula'))
            
            # Criar parcelas
            valor_parcela = valor / parcelas
            for i in range(parcelas):
                data_vencimento = date.today() + timedelta(days=30 * (i + 1))
                cursor.execute('''
                INSERT INTO parcelas (financeiro_id, numero_parcela, valor_parcela, data_vencimento, status)
                VALUES (?, ?, ?, ?, ?)
                ''', (matricula_id, i + 1, valor_parcela, data_vencimento, 'pendente'))
            
            # Atualizar status do aluno
            cursor.execute('''
            INSERT INTO status_aluno (aluno_id, status, data_atualizacao)
            VALUES (?, ?, ?)
            ''', (aluno_id, 'Não Iniciou', date.today()))
            
            conexao.commit()
            conexao.close()
            
            registrar_audit(session.get('usuario_id'), session.get('tipo_usuario'), 'CHECKOUT_MATRICULA', 'matriculas', matricula_id, {})
            flash('Matrícula confirmada com sucesso!', 'success')
            return redirect(f'/comercial/parcelas/{matricula_id}')
        
        except Exception as e:
            flash(f'Erro: {str(e)}', 'error')
    
    turmas = executar_query('''
    SELECT t.id, t.nome, c.valor, c.nome as curso_nome
    FROM turmas t
    JOIN cursos c ON t.curso_id = c.id
    WHERE t.ativa = 1
    ''')
    
    return render_template('comercial/checkout.html',
                         aluno=dict(aluno),
                         turmas=[dict(t) for t in turmas] if turmas else [])

# ============================================================================
# HISTÓRICO DE PAGAMENTOS
# ============================================================================

@app.route('/comercial/historico/<int:aluno_id>')
@login_requerido()
def historico_financeiro_aluno(aluno_id):
    """Histórico financeiro completo do aluno"""
    if not pode_acessar('admin', 'funcionario'):
        flash('Acesso negado!', 'error')
        return redirect('/dashboard')
    
    aluno = executar_query('SELECT * FROM alunos WHERE id = ?', (aluno_id,), fetch_one=True)
    if not aluno:
        flash('Aluno não encontrado!', 'error')
        return redirect('/alunos')
    
    # Histórico de matrículas e financeiro
    financeiros = executar_query('''
    SELECT f.*, t.nome as turma_nome, c.nome as curso_nome,
           SUM(CASE WHEN p.status = 'pago' THEN p.valor_parcela ELSE 0 END) as total_pago
    FROM financeiro f
    JOIN matriculas m ON f.matricula_id = m.id
    JOIN turmas t ON m.turma_id = t.id
    JOIN cursos c ON t.curso_id = c.id
    LEFT JOIN parcelas p ON f.id = p.financeiro_id
    WHERE m.aluno_id = ?
    GROUP BY f.id
    ORDER BY f.data_criacao DESC
    ''', (aluno_id,))
    
    return render_template('comercial/historico_financeiro.html',
                         aluno=dict(aluno),
                         financeiros=[dict(f) for f in financeiros] if financeiros else [])

# ============================================================================
# RELATÓRIO DE INADIMPLÊNCIA
# ============================================================================

@app.route('/comercial/inadimplentes')
@login_requerido()
def relatorio_inadimplentes():
    """Relatório de alunos com parcelas em atraso"""
    if not pode_acessar('admin', 'funcionario'):
        flash('Acesso negado!', 'error')
        return redirect('/dashboard')
    
    inadimplentes = executar_query('''
    SELECT a.id, a.nome, a.email, a.telefone, t.nome as turma_nome,
           COUNT(p.id) as parcelas_atraso,
           SUM(p.valor_parcela) as total_devido
    FROM alunos a
    JOIN matriculas m ON a.id = m.aluno_id
    JOIN turmas t ON m.turma_id = t.id
    JOIN financeiro f ON m.id = f.matricula_id
    JOIN parcelas p ON f.id = p.financeiro_id
    WHERE p.status = 'pendente' AND p.data_vencimento < date('now')
    GROUP BY a.id
    ORDER BY total_devido DESC
    ''')
    
    return render_template('comercial/inadimplentes.html',
                         inadimplentes=[dict(i) for i in inadimplentes] if inadimplentes else [])

# ============================================================================
# CONTROLE DE BOLETO/NOTA FISCAL
# ============================================================================

@app.route('/comercial/boleto/<int:parcela_id>')
@login_requerido()
def gerar_boleto(parcela_id):
    """Gera referência de boleto para a parcela"""
    if not pode_acessar('admin', 'funcionario'):
        flash('Acesso negado!', 'error')
        return redirect('/comercial/financeiro')
    
    parcela = executar_query('''
    SELECT p.*, f.id as financeiro_id
    FROM parcelas p
    JOIN financeiro f ON p.financeiro_id = f.id
    WHERE p.id = ?
    ''', (parcela_id,), fetch_one=True)
    
    if not parcela:
        flash('Parcela não encontrado!', 'error')
        return redirect('/comercial/financeiro')
    
    # Gerar código de boleto simulado
    codigo_boleto = f"{parcela['financeiro_id']}{parcela['numero_parcela']}{int(datetime.now().timestamp())}"
    
    return render_template('comercial/boleto.html',
                         parcela=dict(parcela),
                         codigo_boleto=codigo_boleto)
