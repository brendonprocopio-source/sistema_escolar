# ADICIONAR ESTAS ROTAS AO app.py ANTES DE "if __name__ == '__main__':"

# ============================================================================
# ROTAS PEDAGÓGICAS ADICIONAIS
# ============================================================================

@app.route('/pedagogico/turmas')
@login_requerido()
def pedagogico_turmas():
    if not pode_acessar('admin', 'professor', 'funcionario'):
        flash('Acesso negado!', 'error')
        return redirect('/dashboard')
    
    turmas = executar_query('''
    SELECT t.*, p.nome as professor_nome, c.nome as curso_nome, COUNT(m.id) as total_alunos
    FROM turmas t
    JOIN professores p ON t.professor_id = p.id
    JOIN cursos c ON t.curso_id = c.id
    LEFT JOIN matriculas m ON t.id = m.turma_id
    GROUP BY t.id
    ORDER BY t.data_inicio DESC
    ''')
    
    return render_template('pedagogico/turmas.html',
                         turmas=[dict(t) for t in turmas] if turmas else [])

@app.route('/pedagogico/salas')
@login_requerido()
def pedagogico_salas():
    if not pode_acessar('admin', 'professor', 'funcionario'):
        flash('Acesso negado!', 'error')
        return redirect('/dashboard')
    
    salas = executar_query('SELECT * FROM salas WHERE ativa = 1 ORDER BY nome')
    
    return render_template('pedagogico/salas.html',
                         salas=[dict(s) for s in salas] if salas else [])
