"""
ROTAS DE ADMIN - PAINEL DE CONTROLE COMPLETO
Adicione este código ao app.py
"""

# ============================================================================
# ROTAS DE ADMIN - PAINEL DE CONTROLE
# ============================================================================

@app.route('/admin')
@login_requerido('admin')
def admin_dashboard():
    """Dashboard do administrador"""
    
    # Estatísticas
    total_alunos = executar_query('SELECT COUNT(*) FROM alunos WHERE ativo = 1', fetch_one=True)[0]
    total_professores = executar_query('SELECT COUNT(*) FROM professores WHERE ativo = 1', fetch_one=True)[0]
    total_funcionarios = executar_query('SELECT COUNT(*) FROM funcionarios WHERE ativo = 1', fetch_one=True)[0]
    total_turmas = executar_query('SELECT COUNT(*) FROM turmas WHERE ativa = 1', fetch_one=True)[0]
    total_cursos = executar_query('SELECT COUNT(*) FROM cursos WHERE ativo = 1', fetch_one=True)[0]
    
    # Receita total
    receita = executar_query('''
    SELECT SUM(valor_pago) FROM financeiro
    ''', fetch_one=True)[0] or 0
    
    # Últimas matrículas
    ultimas_matriculas = executar_query('''
    SELECT a.nome, t.nome as turma, m.data_matricula
    FROM matriculas m
    JOIN alunos a ON m.aluno_id = a.id
    JOIN turmas t ON m.turma_id = t.id
    ORDER BY m.data_matricula DESC
    LIMIT 5
    ''')
    
    dados = {
        'total_alunos': total_alunos,
        'total_professores': total_professores,
        'total_funcionarios': total_funcionarios,
        'total_turmas': total_turmas,
        'total_cursos': total_cursos,
        'receita_total': receita,
        'ultimas_matriculas': [dict(m) for m in ultimas_matriculas] if ultimas_matriculas else []
    }
    
    return render_template('admin/dashboard.html', **dados)

# ========== GERENCIAR FUNCIONÁRIOS ==========

@app.route('/admin/funcionarios')
@login_requerido('admin')
def listar_funcionarios():
    """Lista todos os funcionários"""
    funcionarios = executar_query('''
    SELECT f.*, s.nome as setor_nome
    FROM funcionarios f
    LEFT JOIN setores s ON f.setor_id = s.id
    ORDER BY f.nome
    ''')
    
    return render_template('admin/funcionarios/listar.html', 
                         funcionarios=[dict(f) for f in funcionarios] if funcionarios else [])

@app.route('/admin/funcionario/novo', methods=['GET', 'POST'])
@login_requerido('admin')
def novo_funcionario():
    """Criar novo funcionário"""
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        cpf = request.form.get('cpf')
        cargo = request.form.get('cargo')
        setor_id = request.form.get('setor_id')
        salario = request.form.get('salario')
        
        from autenticacao_standalone import Autenticacao
        senha_temp = Autenticacao.gerar_senha_temporaria()
        
        try:
            conexao = get_db()
            cursor = conexao.cursor()
            
            cursor.execute('''
            INSERT INTO funcionarios (nome, email, cpf, senha, cargo, setor_id, salario)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (nome, email, cpf, Autenticacao.hash_senha(senha_temp), cargo, setor_id, salario))
            
            func_id = cursor.lastrowid
            
            cursor.execute('''
            INSERT INTO usuarios (email, senha, tipo_usuario, tabela_referencia, id_referencia)
            VALUES (?, ?, ?, ?, ?)
            ''', (email, Autenticacao.hash_senha(senha_temp), 'funcionario', 'funcionarios', func_id))
            
            conexao.commit()
            conexao.close()
            
            flash(f'Funcionario criado! Senha temporaria: {senha_temp}', 'success')
            return redirect('/admin/funcionarios')
        except Exception as e:
            flash(f'Erro: {str(e)}', 'error')
    
    setores = executar_query('SELECT * FROM setores')
    return render_template('admin/funcionarios/novo.html', 
                         setores=[dict(s) for s in setores] if setores else [])

@app.route('/admin/funcionario/<int:func_id>/editar', methods=['GET', 'POST'])
@login_requerido('admin')
def editar_funcionario(func_id):
    """Editar funcionário"""
    funcionario = executar_query('SELECT * FROM funcionarios WHERE id = ?', (func_id,), fetch_one=True)
    
    if not funcionario:
        flash('Funcionário não encontrado!', 'error')
        return redirect('/admin/funcionarios')
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        cargo = request.form.get('cargo')
        setor_id = request.form.get('setor_id')
        salario = request.form.get('salario')
        
        if executar_update('''
        UPDATE funcionarios SET nome = ?, cargo = ?, setor_id = ?, salario = ? WHERE id = ?
        ''', (nome, cargo, setor_id, salario, func_id)):
            flash('Funcionário atualizado!', 'success')
            return redirect('/admin/funcionarios')
        else:
            flash('Erro ao atualizar!', 'error')
    
    setores = executar_query('SELECT * FROM setores')
    return render_template('admin/funcionarios/editar.html',
                         funcionario=dict(funcionario),
                         setores=[dict(s) for s in setores] if setores else [])

# ========== GERENCIAR CURSOS ==========

@app.route('/admin/cursos')
@login_requerido('admin')
def listar_cursos():
    """Lista todos os cursos"""
    cursos = executar_query('''
    SELECT c.*, COUNT(DISTINCT t.id) as total_turmas
    FROM cursos c
    LEFT JOIN turmas t ON c.id = t.curso_id
    GROUP BY c.id
    ORDER BY c.nome
    ''')
    
    return render_template('admin/cursos/listar.html', 
                         cursos=[dict(c) for c in cursos] if cursos else [])

@app.route('/admin/curso/novo', methods=['GET', 'POST'])
@login_requerido('admin')
def novo_curso():
    """Criar novo curso"""
    if request.method == 'POST':
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        duracao_meses = request.form.get('duracao_meses')
        valor = request.form.get('valor')
        
        if executar_update('''
        INSERT INTO cursos (nome, descricao, duracao_meses, valor)
        VALUES (?, ?, ?, ?)
        ''', (nome, descricao, duracao_meses, valor)):
            flash('Curso criado com sucesso!', 'success')
            return redirect('/admin/cursos')
        else:
            flash('Erro ao criar curso!', 'error')
    
    return render_template('admin/cursos/novo.html')

@app.route('/admin/curso/<int:curso_id>/editar', methods=['GET', 'POST'])
@login_requerido('admin')
def editar_curso(curso_id):
    """Editar curso"""
    curso = executar_query('SELECT * FROM cursos WHERE id = ?', (curso_id,), fetch_one=True)
    
    if not curso:
        flash('Curso não encontrado!', 'error')
        return redirect('/admin/cursos')
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        duracao_meses = request.form.get('duracao_meses')
        valor = request.form.get('valor')
        ativo = 1 if request.form.get('ativo') else 0
        
        if executar_update('''
        UPDATE cursos SET nome = ?, descricao = ?, duracao_meses = ?, valor = ?, ativo = ?
        WHERE id = ?
        ''', (nome, descricao, duracao_meses, valor, ativo, curso_id)):
            flash('Curso atualizado!', 'success')
            return redirect('/admin/cursos')
        else:
            flash('Erro ao atualizar!', 'error')
    
    return render_template('admin/cursos/editar.html', curso=dict(curso))

# ========== GERENCIAR MÓDULOS ==========

@app.route('/admin/modulos')
@login_requerido('admin')
def listar_modulos():
    """Lista todos os módulos"""
    modulos = executar_query('''
    SELECT m.*, c.nome as curso_nome
    FROM modulos m
    JOIN cursos c ON m.curso_id = c.id
    ORDER BY c.nome, m.ordem
    ''')
    
    return render_template('admin/modulos/listar.html', 
                         modulos=[dict(m) for m in modulos] if modulos else [])

@app.route('/admin/modulo/novo', methods=['GET', 'POST'])
@login_requerido('admin')
def novo_modulo():
    """Criar novo módulo"""
    if request.method == 'POST':
        curso_id = request.form.get('curso_id')
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        carga_horaria = request.form.get('carga_horaria')
        ordem = request.form.get('ordem')
        
        if executar_update('''
        INSERT INTO modulos (curso_id, nome, descricao, carga_horaria, ordem)
        VALUES (?, ?, ?, ?, ?)
        ''', (curso_id, nome, descricao, carga_horaria, ordem)):
            flash('Módulo criado com sucesso!', 'success')
            return redirect('/admin/modulos')
        else:
            flash('Erro ao criar módulo!', 'error')
    
    cursos = executar_query('SELECT * FROM cursos WHERE ativo = 1 ORDER BY nome')
    return render_template('admin/modulos/novo.html', 
                         cursos=[dict(c) for c in cursos] if cursos else [])

# ========== GERENCIAR SETORES ==========

@app.route('/admin/setores')
@login_requerido('admin')
def listar_setores():
    """Lista todos os setores"""
    setores = executar_query('''
    SELECT s.*, COUNT(f.id) as total_funcionarios
    FROM setores s
    LEFT JOIN funcionarios f ON s.id = f.setor_id
    GROUP BY s.id
    ORDER BY s.nome
    ''')
    
    return render_template('admin/setores/listar.html', 
                         setores=[dict(s) for s in setores] if setores else [])

@app.route('/admin/setor/novo', methods=['GET', 'POST'])
@login_requerido('admin')
def novo_setor():
    """Criar novo setor"""
    if request.method == 'POST':
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        
        if executar_update('''
        INSERT INTO setores (nome, descricao)
        VALUES (?, ?)
        ''', (nome, descricao)):
            flash('Setor criado com sucesso!', 'success')
            return redirect('/admin/setores')
        else:
            flash('Erro ao criar setor!', 'error')
    
    return render_template('admin/setores/novo.html')

# ========== GERENCIAR USUÁRIOS ==========

@app.route('/admin/usuarios')
@login_requerido('admin')
def listar_usuarios():
    """Lista todos os usuários"""
    usuarios = executar_query('''
    SELECT * FROM usuarios ORDER BY email
    ''')
    
    return render_template('admin/usuarios/listar.html', 
                         usuarios=[dict(u) for u in usuarios] if usuarios else [])

@app.route('/admin/usuario/<int:user_id>/ativar', methods=['POST'])
@login_requerido('admin')
def ativar_usuario(user_id):
    """Ativar/desativar usuário"""
    if executar_update('UPDATE usuarios SET ativo = 1 WHERE id = ?', (user_id,)):
        flash('Usuário ativado!', 'success')
    else:
        flash('Erro!', 'error')
    return redirect('/admin/usuarios')

@app.route('/admin/usuario/<int:user_id>/desativar', methods=['POST'])
@login_requerido('admin')
def desativar_usuario(user_id):
    """Desativar usuário"""
    if executar_update('UPDATE usuarios SET ativo = 0 WHERE id = ?', (user_id,)):
        flash('Usuário desativado!', 'success')
    else:
        flash('Erro!', 'error')
    return redirect('/admin/usuarios')
