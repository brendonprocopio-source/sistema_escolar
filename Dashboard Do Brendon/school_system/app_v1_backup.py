"""
APLICAÇÃO FLASK - SISTEMA DE GESTÃO DE ESCOLA - CORRIGIDO
Acesso liberado para Admin em todos os painéis
"""

from flask import Flask, render_template, request, session, redirect, flash
import sqlite3
from datetime import datetime, date
from autenticacao_standalone import Autenticacao, login_requerido
from database import criar_banco_dados

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_super_segura_aqui_123456'

def get_db():
    """Conecta ao banco de dados"""
    conexao = sqlite3.connect('escola.db')
    conexao.row_factory = sqlite3.Row
    return conexao

def executar_query(query, params=(), fetch_one=False):
    """Executa uma query e retorna resultados"""
    try:
        conexao = get_db()
        cursor = conexao.cursor()
        cursor.execute(query, params)
        resultado = cursor.fetchone() if fetch_one else cursor.fetchall()
        conexao.close()
        return resultado
    except Exception as e:
        print(f"Erro na query: {e}")
        return None

def executar_update(query, params=()):
    """Executa UPDATE, INSERT ou DELETE"""
    try:
        conexao = get_db()
        cursor = conexao.cursor()
        cursor.execute(query, params)
        conexao.commit()
        conexao.close()
        return True
    except Exception as e:
        print(f"Erro ao executar: {e}")
        return False

def pode_acessar(*tipos_permitidos):
    """Verifica se usuario pode acessar"""
    tipo = session.get('tipo_usuario')
    return tipo in tipos_permitidos

# ============================================================================
# AUTENTICAÇÃO
# ============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        usuario = Autenticacao.autenticar(email, senha)
        
        if usuario:
            session['usuario_id'] = usuario['id_referencia']
            session['email'] = usuario['email']
            session['tipo_usuario'] = usuario['tipo_usuario']
            session['tabela_referencia'] = usuario['tabela_referencia']
            flash('Login realizado!', 'success')
            return redirect('/dashboard')
        else:
            flash('Email ou senha incorretos!', 'error')
    
    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    """Cadastro de novo aluno"""
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        cpf = request.form.get('cpf')
        senha = request.form.get('senha')
        telefone = request.form.get('telefone')
        data_nascimento = request.form.get('data_nascimento')
        
        try:
            conexao = get_db()
            cursor = conexao.cursor()
            
            cursor.execute('''
            INSERT INTO alunos (nome, email, cpf, senha, matricula, data_nascimento, telefone)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (nome, email, cpf, Autenticacao.hash_senha(senha), 
                  f"ALN{int(datetime.now().timestamp())}", data_nascimento, telefone))
            
            aluno_id = cursor.lastrowid
            
            cursor.execute('''
            INSERT INTO usuarios (email, senha, tipo_usuario, tabela_referencia, id_referencia)
            VALUES (?, ?, ?, ?, ?)
            ''', (email, Autenticacao.hash_senha(senha), 'aluno', 'alunos', aluno_id))
            
            conexao.commit()
            conexao.close()
            
            flash('Cadastro realizado! Faça login.', 'success')
            return redirect('/login')
        except Exception as e:
            flash(f'Erro: {str(e)}', 'error')
    
    return render_template('cadastro.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    flash('Desconectado!', 'info')
    return redirect('/login')

@app.route('/')
def index():
    if 'usuario_id' in session:
        return redirect('/dashboard')
    return redirect('/login')

# ============================================================================
# DASHBOARD
# ============================================================================

@app.route('/dashboard')
@login_requerido()
def dashboard():
    """Dashboard principal"""
    tipo_usuario = session.get('tipo_usuario')
    usuario_id = session.get('usuario_id')
    
    dados = {'tipo_usuario': tipo_usuario, 'usuario_id': usuario_id}
    
    if tipo_usuario == 'aluno':
        aluno = executar_query('SELECT * FROM alunos WHERE id = ?', (usuario_id,), fetch_one=True)
        turmas = executar_query('''
        SELECT t.*, p.nome as professor_nome, c.nome as curso_nome
        FROM turmas t
        JOIN matriculas m ON t.id = m.turma_id
        JOIN professores p ON t.professor_id = p.id
        JOIN cursos c ON t.curso_id = c.id
        WHERE m.aluno_id = ?
        ''', (usuario_id,))
        dados.update({
            'aluno': dict(aluno) if aluno else {},
            'turmas': [dict(t) for t in turmas] if turmas else []
        })
    
    elif tipo_usuario == 'professor':
        turmas = executar_query('''
        SELECT t.*, c.nome as curso_nome, COUNT(m.id) as total_alunos
        FROM turmas t
        JOIN cursos c ON t.curso_id = c.id
        LEFT JOIN matriculas m ON t.id = m.turma_id
        WHERE t.professor_id = ?
        GROUP BY t.id
        ''', (usuario_id,))
        dados['turmas'] = [dict(t) for t in turmas] if turmas else []
    
    return render_template('dashboard.html', **dados)

# ============================================================================
# TURMAS - Acesso: Admin, Funcionario
# ============================================================================

@app.route('/turmas')
@login_requerido()
def listar_turmas():
    """Lista turmas"""
    if not pode_acessar('admin', 'funcionario'):
        flash('Acesso negado!', 'error')
        return redirect('/dashboard')
    
    turmas = executar_query('''
    SELECT t.*, c.nome as curso_nome, p.nome as professor_nome, COUNT(m.id) as total_alunos
    FROM turmas t
    JOIN cursos c ON t.curso_id = c.id
    JOIN professores p ON t.professor_id = p.id
    LEFT JOIN matriculas m ON t.id = m.turma_id
    GROUP BY t.id ORDER BY t.data_inicio DESC
    ''')
    
    return render_template('turmas/listar.html', turmas=[dict(t) for t in turmas] if turmas else [])

@app.route('/turma/nova', methods=['GET', 'POST'])
@login_requerido()
def nova_turma():
    """Nova turma"""
    if not pode_acessar('admin', 'funcionario'):
        flash('Acesso negado!', 'error')
        return redirect('/dashboard')
    
    if request.method == 'POST':
        if executar_update('''
        INSERT INTO turmas (codigo, nome, curso_id, professor_id, data_inicio, data_fim, horario, sala, capacidade)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (request.form.get('codigo'), request.form.get('nome'), request.form.get('curso_id'),
              request.form.get('professor_id'), request.form.get('data_inicio'), request.form.get('data_fim'),
              request.form.get('horario'), request.form.get('sala'), request.form.get('capacidade'))):
            flash('Turma criada!', 'success')
            return redirect('/turmas')
        flash('Erro!', 'error')
    
    cursos = executar_query('SELECT * FROM cursos WHERE ativo = 1')
    professores = executar_query('SELECT * FROM professores WHERE ativo = 1')
    return render_template('turmas/nova.html', 
                         cursos=[dict(c) for c in cursos] if cursos else [],
                         professores=[dict(p) for p in professores] if professores else [])

# ============================================================================
# ALUNOS - Acesso: Admin, Funcionario
# ============================================================================

@app.route('/alunos')
@login_requerido()
def listar_alunos():
    """Lista alunos"""
    if not pode_acessar('admin', 'funcionario'):
        flash('Acesso negado!', 'error')
        return redirect('/dashboard')
    
    alunos = executar_query('SELECT * FROM alunos WHERE ativo = 1 ORDER BY nome')
    return render_template('alunos/listar.html', alunos=[dict(a) for a in alunos] if alunos else [])

@app.route('/aluno/novo', methods=['GET', 'POST'])
@login_requerido()
def novo_aluno():
    """Novo aluno (Admin/Funcionario)"""
    if not pode_acessar('admin', 'funcionario'):
        flash('Acesso negado!', 'error')
        return redirect('/dashboard')
    
    if request.method == 'POST':
        try:
            conexao = get_db()
            cursor = conexao.cursor()
            
            cursor.execute('''
            INSERT INTO alunos (nome, email, cpf, senha, matricula, data_nascimento, telefone)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (request.form.get('nome'), request.form.get('email'), request.form.get('cpf'),
                  Autenticacao.hash_senha(request.form.get('senha')),
                  f"ALN{int(datetime.now().timestamp())}", request.form.get('data_nascimento'),
                  request.form.get('telefone')))
            
            aluno_id = cursor.lastrowid
            
            cursor.execute('''
            INSERT INTO usuarios (email, senha, tipo_usuario, tabela_referencia, id_referencia)
            VALUES (?, ?, ?, ?, ?)
            ''', (request.form.get('email'), Autenticacao.hash_senha(request.form.get('senha')),
                  'aluno', 'alunos', aluno_id))
            
            conexao.commit()
            conexao.close()
            flash('Aluno criado!', 'success')
            return redirect('/alunos')
        except Exception as e:
            flash(f'Erro: {str(e)}', 'error')
    
    return render_template('alunos/novo.html')

@app.route('/aluno/<int:aluno_id>')
@login_requerido()
def detalhe_aluno(aluno_id):
    """Detalhes aluno"""
    aluno = executar_query('SELECT * FROM alunos WHERE id = ?', (aluno_id,), fetch_one=True)
    if not aluno:
        flash('Aluno não encontrado!', 'error')
        return redirect('/alunos')
    
    turmas = executar_query('''
    SELECT t.*, c.nome as curso_nome, p.nome as professor_nome
    FROM turmas t
    JOIN matriculas m ON t.id = m.turma_id
    JOIN cursos c ON t.curso_id = c.id
    JOIN professores p ON t.professor_id = p.id
    WHERE m.aluno_id = ?
    ''', (aluno_id,))
    
    notas = executar_query('''
    SELECT n.*, m.nome as modulo_nome
    FROM notas n
    JOIN matriculas mat ON n.matricula_id = mat.id
    JOIN modulos m ON n.modulo_id = m.id
    WHERE mat.aluno_id = ?
    ''', (aluno_id,))
    
    frequencia = executar_query('''
    SELECT COUNT(*) as total, SUM(CASE WHEN presente = 1 THEN 1 ELSE 0 END) as presentes
    FROM frequencias f
    JOIN matriculas m ON f.matricula_id = m.id
    WHERE m.aluno_id = ?
    ''', (aluno_id,), fetch_one=True)
    
    return render_template('alunos/detalhe.html',
                         aluno=dict(aluno),
                         turmas=[dict(t) for t in turmas] if turmas else [],
                         notas=[dict(n) for n in notas] if notas else [],
                         frequencia=dict(frequencia) if frequencia else {})

# ============================================================================
# PROFESSORES - Acesso: Admin
# ============================================================================

@app.route('/professores')
@login_requerido()
def listar_professores():
    """Lista professores"""
    if not pode_acessar('admin'):
        flash('Acesso negado!', 'error')
        return redirect('/dashboard')
    
    professores = executar_query('SELECT * FROM professores WHERE ativo = 1 ORDER BY nome')
    return render_template('admin/funcionarios/listar.html', 
                         funcionarios=[dict(p) for p in professores] if professores else [])

@app.route('/professor/novo', methods=['GET', 'POST'])
@login_requerido()
def novo_professor():
    """Novo professor"""
    if not pode_acessar('admin'):
        flash('Acesso negado!', 'error')
        return redirect('/dashboard')
    
    if request.method == 'POST':
        try:
            conexao = get_db()
            cursor = conexao.cursor()
            
            cursor.execute('''
            INSERT INTO professores (nome, email, cpf, senha, matricula, formacao, especialidade)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (request.form.get('nome'), request.form.get('email'), request.form.get('cpf'),
                  Autenticacao.hash_senha(request.form.get('senha')),
                  f"PROF{int(datetime.now().timestamp())}", request.form.get('formacao'),
                  request.form.get('especialidade')))
            
            prof_id = cursor.lastrowid
            
            cursor.execute('''
            INSERT INTO usuarios (email, senha, tipo_usuario, tabela_referencia, id_referencia)
            VALUES (?, ?, ?, ?, ?)
            ''', (request.form.get('email'), Autenticacao.hash_senha(request.form.get('senha')),
                  'professor', 'professores', prof_id))
            
            conexao.commit()
            conexao.close()
            flash('Professor criado!', 'success')
            return redirect('/professores')
        except Exception as e:
            flash(f'Erro: {str(e)}', 'error')
    
    return render_template('admin/funcionarios/novo.html', setores=[])

# ============================================================================
# FREQUÊNCIA E NOTAS
# ============================================================================

@app.route('/turma/<int:turma_id>/frequencia', methods=['GET', 'POST'])
@login_requerido()
def frequencia_turma(turma_id):
    """Registrar frequência"""
    if not pode_acessar('admin', 'funcionario', 'professor'):
        flash('Acesso negado!', 'error')
        return redirect('/dashboard')
    
    turma = executar_query('SELECT * FROM turmas WHERE id = ?', (turma_id,), fetch_one=True)
    if not turma:
        flash('Turma não encontrada!', 'error')
        return redirect('/dashboard')
    
    if request.method == 'POST':
        data_aula = request.form.get('data_aula')
        matriculas = executar_query('''
        SELECT m.id FROM matriculas m WHERE m.turma_id = ?
        ''', (turma_id,))
        
        for matricula in matriculas:
            presente = request.form.get(f'presente_{matricula["id"]}')
            executar_update('''
            INSERT INTO frequencias (matricula_id, data_aula, presente)
            VALUES (?, ?, ?)
            ''', (matricula['id'], data_aula, 1 if presente else 0))
        
        flash('Frequência registrada!', 'success')
        return redirect(f'/turma/{turma_id}/frequencia')
    
    alunos = executar_query('''
    SELECT m.id, a.id as aluno_id, a.nome
    FROM matriculas m
    JOIN alunos a ON m.aluno_id = a.id
    WHERE m.turma_id = ?
    ''', (turma_id,))
    
    return render_template('frequencia/registrar.html',
                         turma=dict(turma),
                         alunos=[dict(a) for a in alunos] if alunos else [])

@app.route('/turma/<int:turma_id>/notas', methods=['GET', 'POST'])
@login_requerido()
def notas_turma(turma_id):
    """Lançar notas"""
    if not pode_acessar('admin', 'funcionario', 'professor'):
        flash('Acesso negado!', 'error')
        return redirect('/dashboard')
    
    turma = executar_query('SELECT * FROM turmas WHERE id = ?', (turma_id,), fetch_one=True)
    if not turma:
        flash('Turma não encontrada!', 'error')
        return redirect('/dashboard')
    
    if request.method == 'POST':
        matricula_id = request.form.get('matricula_id')
        modulo_id = request.form.get('modulo_id')
        primeira_nota = float(request.form.get('primeira_nota', 0))
        segunda_nota = float(request.form.get('segunda_nota', 0))
        terceira_nota = float(request.form.get('terceira_nota', 0))
        media = (primeira_nota + segunda_nota + terceira_nota) / 3
        
        executar_update('''
        INSERT OR REPLACE INTO notas (matricula_id, modulo_id, primeira_nota, segunda_nota, terceira_nota, media_final)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (matricula_id, modulo_id, primeira_nota, segunda_nota, terceira_nota, media))
        
        flash('Notas registradas!', 'success')
    
    modulos = executar_query('''
    SELECT * FROM modulos WHERE curso_id = (SELECT curso_id FROM turmas WHERE id = ?)
    ''', (turma_id,))
    
    alunos = executar_query('''
    SELECT m.id as matricula_id, a.id as aluno_id, a.nome
    FROM matriculas m
    JOIN alunos a ON m.aluno_id = a.id
    WHERE m.turma_id = ?
    ''', (turma_id,))
    
    return render_template('notas/registrar.html',
                         turma=dict(turma),
                         modulos=[dict(m) for m in modulos] if modulos else [],
                         alunos=[dict(a) for a in alunos] if alunos else [])

# ============================================================================
# RELATÓRIOS - Acesso: Admin, Funcionario
# ============================================================================

@app.route('/relatorios')
@login_requerido()
def relatorios():
    if not pode_acessar('admin', 'funcionario'):
        flash('Acesso negado!', 'error')
        return redirect('/dashboard')
    return render_template('relatorios/index.html')

@app.route('/relatorio/turmas')
@login_requerido()
def relatorio_turmas():
    if not pode_acessar('admin', 'funcionario'):
        flash('Acesso negado!', 'error')
        return redirect('/dashboard')
    
    turmas = executar_query('''
    SELECT t.*, c.nome as curso_nome, p.nome as professor_nome, COUNT(m.id) as total_alunos
    FROM turmas t
    JOIN cursos c ON t.curso_id = c.id
    JOIN professores p ON t.professor_id = p.id
    LEFT JOIN matriculas m ON t.id = m.turma_id
    GROUP BY t.id
    ''')
    
    return render_template('relatorios/turmas.html',
                         turmas=[dict(t) for t in turmas] if turmas else [])

@app.route('/relatorio/frequencia')
@login_requerido()
def relatorio_frequencia():
    if not pode_acessar('admin', 'funcionario'):
        flash('Acesso negado!', 'error')
        return redirect('/dashboard')
    
    dados = executar_query('''
    SELECT a.nome, t.nome as turma, COUNT(*) as total_aulas,
           SUM(CASE WHEN f.presente = 1 THEN 1 ELSE 0 END) as presentes,
           ROUND(SUM(CASE WHEN f.presente = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as percentual
    FROM frequencias f
    JOIN matriculas m ON f.matricula_id = m.id
    JOIN alunos a ON m.aluno_id = a.id
    JOIN turmas t ON m.turma_id = t.id
    GROUP BY m.aluno_id, m.turma_id
    ORDER BY a.nome
    ''')
    
    return render_template('relatorios/frequencia.html',
                         dados=[dict(d) for d in dados] if dados else [])

@app.route('/relatorio/desempenho')
@login_requerido()
def relatorio_desempenho():
    if not pode_acessar('admin', 'funcionario'):
        flash('Acesso negado!', 'error')
        return redirect('/dashboard')
    
    dados = executar_query('''
    SELECT a.nome, t.nome as turma, m.nome as modulo,
           n.primeira_nota, n.segunda_nota, n.terceira_nota, n.media_final
    FROM notas n
    JOIN matriculas mat ON n.matricula_id = mat.id
    JOIN alunos a ON mat.aluno_id = a.id
    JOIN turmas t ON mat.turma_id = t.id
    JOIN modulos m ON n.modulo_id = m.id
    ORDER BY a.nome, m.nome
    ''')
    
    return render_template('relatorios/desempenho.html',
                         dados=[dict(d) for d in dados] if dados else [])

# ============================================================================
# ADMIN - Todos os painéis
# ============================================================================

@app.route('/admin')
@login_requerido()
def admin_dashboard():
    if not pode_acessar('admin'):
        flash('Acesso negado!', 'error')
        return redirect('/dashboard')
    
    total_alunos = executar_query('SELECT COUNT(*) FROM alunos WHERE ativo = 1', fetch_one=True)[0]
    total_professores = executar_query('SELECT COUNT(*) FROM professores WHERE ativo = 1', fetch_one=True)[0]
    total_funcionarios = executar_query('SELECT COUNT(*) FROM funcionarios WHERE ativo = 1', fetch_one=True)[0]
    total_turmas = executar_query('SELECT COUNT(*) FROM turmas WHERE ativa = 1', fetch_one=True)[0]
    total_cursos = executar_query('SELECT COUNT(*) FROM cursos WHERE ativo = 1', fetch_one=True)[0]
    receita = executar_query('SELECT SUM(valor_pago) FROM financeiro', fetch_one=True)[0] or 0
    
    ultimas_matriculas = executar_query('''
    SELECT a.nome, t.nome as turma, m.data_matricula
    FROM matriculas m
    JOIN alunos a ON m.aluno_id = a.id
    JOIN turmas t ON m.turma_id = t.id
    ORDER BY m.data_matricula DESC LIMIT 5
    ''')
    
    return render_template('admin/dashboard.html',
                         total_alunos=total_alunos,
                         total_professores=total_professores,
                         total_funcionarios=total_funcionarios,
                         total_turmas=total_turmas,
                         total_cursos=total_cursos,
                         receita_total=receita,
                         ultimas_matriculas=[dict(m) for m in ultimas_matriculas] if ultimas_matriculas else [])

@app.route('/admin/funcionarios')
@login_requerido()
def listar_funcionarios():
    if not pode_acessar('admin'):
        flash('Acesso negado!', 'error')
        return redirect('/dashboard')
    
    funcionarios = executar_query('''
    SELECT f.*, s.nome as setor_nome
    FROM funcionarios f
    LEFT JOIN setores s ON f.setor_id = s.id
    ORDER BY f.nome
    ''')
    
    return render_template('admin/funcionarios/listar.html', 
                         funcionarios=[dict(f) for f in funcionarios] if funcionarios else [])

@app.route('/admin/funcionario/novo', methods=['GET', 'POST'])
@login_requerido()
def novo_funcionario():
    if not pode_acessar('admin'):
        flash('Acesso negado!', 'error')
        return redirect('/dashboard')
    
    if request.method == 'POST':
        try:
            conexao = get_db()
            cursor = conexao.cursor()
            
            senha_temp = Autenticacao.gerar_senha_temporaria()
            
            cursor.execute('''
            INSERT INTO funcionarios (nome, email, cpf, senha, cargo, setor_id, salario)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (request.form.get('nome'), request.form.get('email'), request.form.get('cpf'),
                  Autenticacao.hash_senha(senha_temp), request.form.get('cargo'),
                  request.form.get('setor_id'), request.form.get('salario')))
            
            func_id = cursor.lastrowid
            
            cursor.execute('''
            INSERT INTO usuarios (email, senha, tipo_usuario, tabela_referencia, id_referencia)
            VALUES (?, ?, ?, ?, ?)
            ''', (request.form.get('email'), Autenticacao.hash_senha(senha_temp), 'funcionario', 'funcionarios', func_id))
            
            conexao.commit()
            conexao.close()
            
            flash(f'Funcionario criado! Senha: {senha_temp}', 'success')
            return redirect('/admin/funcionarios')
        except Exception as e:
            flash(f'Erro: {str(e)}', 'error')
    
    setores = executar_query('SELECT * FROM setores')
    return render_template('admin/funcionarios/novo.html', 
                         setores=[dict(s) for s in setores] if setores else [])

@app.route('/admin/cursos')
@login_requerido()
def listar_cursos():
    if not pode_acessar('admin'):
        flash('Acesso negado!', 'error')
        return redirect('/dashboard')
    
    cursos = executar_query('''
    SELECT c.*, COUNT(DISTINCT t.id) as total_turmas
    FROM cursos c
    LEFT JOIN turmas t ON c.id = t.curso_id
    GROUP BY c.id ORDER BY c.nome
    ''')
    
    return render_template('admin/cursos/listar.html', 
                         cursos=[dict(c) for c in cursos] if cursos else [])

@app.route('/admin/curso/novo', methods=['GET', 'POST'])
@login_requerido()
def novo_curso():
    if not pode_acessar('admin'):
        flash('Acesso negado!', 'error')
        return redirect('/dashboard')
    
    if request.method == 'POST':
        if executar_update('''
        INSERT INTO cursos (nome, descricao, duracao_meses, valor)
        VALUES (?, ?, ?, ?)
        ''', (request.form.get('nome'), request.form.get('descricao'),
              request.form.get('duracao_meses'), request.form.get('valor'))):
            flash('Curso criado!', 'success')
            return redirect('/admin/cursos')
        flash('Erro!', 'error')
    
    return render_template('admin/cursos/novo.html')

@app.route('/admin/modulos')
@login_requerido()
def listar_modulos():
    if not pode_acessar('admin'):
        flash('Acesso negado!', 'error')
        return redirect('/dashboard')
    
    modulos = executar_query('''
    SELECT m.*, c.nome as curso_nome
    FROM modulos m
    JOIN cursos c ON m.curso_id = c.id
    ORDER BY c.nome, m.ordem
    ''')
    
    return render_template('admin/modulos/listar.html', 
                         modulos=[dict(m) for m in modulos] if modulos else [])

@app.route('/admin/modulo/novo', methods=['GET', 'POST'])
@login_requerido()
def novo_modulo():
    if not pode_acessar('admin'):
        flash('Acesso negado!', 'error')
        return redirect('/dashboard')
    
    if request.method == 'POST':
        if executar_update('''
        INSERT INTO modulos (curso_id, nome, descricao, carga_horaria, ordem)
        VALUES (?, ?, ?, ?, ?)
        ''', (request.form.get('curso_id'), request.form.get('nome'),
              request.form.get('descricao'), request.form.get('carga_horaria'),
              request.form.get('ordem'))):
            flash('Modulo criado!', 'success')
            return redirect('/admin/modulos')
        flash('Erro!', 'error')
    
    cursos = executar_query('SELECT * FROM cursos WHERE ativo = 1 ORDER BY nome')
    return render_template('admin/modulos/novo.html', 
                         cursos=[dict(c) for c in cursos] if cursos else [])

@app.route('/admin/setores')
@login_requerido()
def listar_setores():
    if not pode_acessar('admin'):
        flash('Acesso negado!', 'error')
        return redirect('/dashboard')
    
    setores = executar_query('''
    SELECT s.*, COUNT(f.id) as total_funcionarios
    FROM setores s
    LEFT JOIN funcionarios f ON s.id = f.setor_id
    GROUP BY s.id ORDER BY s.nome
    ''')
    
    return render_template('admin/setores/listar.html', 
                         setores=[dict(s) for s in setores] if setores else [])

@app.route('/admin/setor/novo', methods=['GET', 'POST'])
@login_requerido()
def novo_setor():
    if not pode_acessar('admin'):
        flash('Acesso negado!', 'error')
        return redirect('/dashboard')
    
    if request.method == 'POST':
        if executar_update('''
        INSERT INTO setores (nome, descricao)
        VALUES (?, ?)
        ''', (request.form.get('nome'), request.form.get('descricao'))):
            flash('Setor criado!', 'success')
            return redirect('/admin/setores')
        flash('Erro!', 'error')
    
    return render_template('admin/setores/novo.html')

@app.route('/admin/usuarios')
@login_requerido()
def listar_usuarios():
    if not pode_acessar('admin'):
        flash('Acesso negado!', 'error')
        return redirect('/dashboard')
    
    usuarios = executar_query('SELECT * FROM usuarios ORDER BY email')
    return render_template('admin/usuarios/listar.html', 
                         usuarios=[dict(u) for u in usuarios] if usuarios else [])

@app.route('/admin/usuario/<int:user_id>/ativar', methods=['POST'])
@login_requerido()
def ativar_usuario(user_id):
    if executar_update('UPDATE usuarios SET ativo = 1 WHERE id = ?', (user_id,)):
        flash('Usuario ativado!', 'success')
    else:
        flash('Erro!', 'error')
    return redirect('/admin/usuarios')

@app.route('/admin/usuario/<int:user_id>/desativar', methods=['POST'])
@login_requerido()
def desativar_usuario(user_id):
    if executar_update('UPDATE usuarios SET ativo = 0 WHERE id = ?', (user_id,)):
        flash('Usuario desativado!', 'success')
    else:
        flash('Erro!', 'error')
    return redirect('/admin/usuarios')

# ============================================================================
# INICIAR
# ============================================================================

if __name__ == '__main__':
    try:
        criar_banco_dados()
    except:
        pass
    
    print("\n" + "="*70)
    print("Sistema de Gestao de Escola")
    print("="*70)
    print("\nAcesse: http://localhost:5000")
    print("\nAdmin: admin@escola.com / Mudar@123")
    print("Aluno: joao@escola.com / Aluno@123")
    print("Professor: ana@escola.com / Prof@123")
    print("\n" + "="*70 + "\n")
    
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
