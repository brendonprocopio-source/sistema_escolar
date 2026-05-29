"""
MÓDULO DE CONTROLE DE ACESSO (RBAC - Role Based Access Control)
Sistema de Permissões Hierárquico
"""

from functools import wraps
from flask import session, redirect, flash

class PermissaoManager:
    """Gerenciador de permissões por role"""
    
    PERMISSOES_POR_ROLE = {
        'admin': {
            'nivel': 100,
            'permissoes': [
                'cursos:criar', 'cursos:editar', 'cursos:deletar',
                'turmas:criar', 'turmas:editar', 'turmas:deletar',
                'alunos:criar', 'alunos:editar', 'alunos:deletar',
                'usuarios:criar', 'usuarios:editar', 'usuarios:deletar',
                'financeiro:tudo', 'academico:tudo', 'relatorios:tudo',
                'diretoria:tudo'
            ]
        },
        'diretoria': {
            'nivel': 90,
            'permissoes': [
                'turmas:ler', 'turmas:editar',
                'alunos:ler', 'alunos:editar',
                'financeiro:ler', 'financeiro:relatorios',
                'academico:ler', 'relatorios:tudo',
                'observacao:criar', 'observacao:editar'
            ]
        },
        'comercial': {
            'nivel': 40,
            'permissoes': [
                'alunos:criar', 'alunos:ler', 'alunos:editar',
                'matriculas:criar', 'matriculas:ler',
                'financeiro:ler', 'financeiro:pagamentos', 'financeiro:criar_parcelas',
                'comprovantes:gerar'
            ]
        },
        'pedagogo': {
            'nivel': 60,
            'permissoes': [
                'turmas:ler', 'turmas:editar',
                'alunos:ler', 'alunos:editar',
                'frequencia:tudo', 'notas:ler',
                'observacao:criar', 'observacao:editar',
                'relatorios:academico', 'professores:alocar'
            ]
        },
        'professor': {
            'nivel': 20,
            'permissoes': [
                'turmas:minhas',
                'alunos:minhas_turmas',
                'frequencia:minhas_turmas',
                'notas:minhas_turmas',
                'observacao:minhas_turmas'
            ]
        },
        'aluno': {
            'nivel': 10,
            'permissoes': [
                'turmas:minhas',
                'notas:minhas',
                'frequencia:minhas',
                'financeiro:minhas_parcelas',
                'observacao:minhas'
            ]
        }
    }
    
    @staticmethod
    def tem_permissao(role, permissao):
        """Verifica se uma role tem uma permissão específica"""
        if role not in PermissaoManager.PERMISSOES_POR_ROLE:
            return False
        
        permissoes = PermissaoManager.PERMISSOES_POR_ROLE[role]['permissoes']
        
        # Verificar permissão exata
        if permissao in permissoes:
            return True
        
        # Verificar wildcards (ex: turmas:* permite tudo em turmas)
        modulo = permissao.split(':')[0] if ':' in permissao else permissao
        if f'{modulo}:*' in permissoes:
            return True
        
        # Verificar acesso total
        if '*:*' in permissoes or 'tudo' in permissoes:
            return True
        
        return False
    
    @staticmethod
    def requer_permissao(permissao_necessaria):
        """Decorator para proteger rotas com verificação de permissão"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if 'usuario_role' not in session:
                    flash('Acesso negado. Faça login primeiro.', 'error')
                    return redirect('/login')
                
                role = session.get('usuario_role')
                
                if not PermissaoManager.tem_permissao(role, permissao_necessaria):
                    flash(f'Acesso negado. Você não tem permissão: {permissao_necessaria}', 'error')
                    return redirect('/dashboard')
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    @staticmethod
    def requer_roles(*roles_permitidas):
        """Decorator para proteger rotas permitindo múltiplas roles"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if 'usuario_role' not in session:
                    flash('Acesso negado. Faça login primeiro.', 'error')
                    return redirect('/login')
                
                user_role = session.get('usuario_role')
                
                if user_role not in roles_permitidas:
                    flash(f'Acesso negado. Você não tem permissão para acessar esta área.', 'error')
                    return redirect('/dashboard')
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator


class ControladorAcesso:
    """Controlador centralizado de acesso"""
    
    @staticmethod
    def pode_criar_aluno(role):
        return PermissaoManager.tem_permissao(role, 'alunos:criar')
    
    @staticmethod
    def pode_editar_aluno(role, aluno_id=None):
        return PermissaoManager.tem_permissao(role, 'alunos:editar')
    
    @staticmethod
    def pode_registrar_frequencia(role, turma_id=None):
        if role == 'professor':
            # Professor só pode registrar em suas próprias turmas
            return PermissaoManager.tem_permissao(role, 'frequencia:minhas_turmas')
        return PermissaoManager.tem_permissao(role, 'frequencia:tudo')
    
    @staticmethod
    def pode_registrar_notas(role, turma_id=None):
        if role == 'professor':
            return PermissaoManager.tem_permissao(role, 'notas:minhas_turmas')
        return PermissaoManager.tem_permissao(role, 'notas:ler')
    
    @staticmethod
    def pode_registrar_pagamento(role):
        return PermissaoManager.tem_permissao(role, 'financeiro:pagamentos')
    
    @staticmethod
    def pode_gerar_parcelas(role):
        return PermissaoManager.tem_permissao(role, 'financeiro:criar_parcelas')
    
    @staticmethod
    def pode_ver_financeiro(role):
        return PermissaoManager.tem_permissao(role, 'financeiro:ler') or \
               PermissaoManager.tem_permissao(role, 'financeiro:tudo')
    
    @staticmethod
    def pode_criar_observacao(role):
        return PermissaoManager.tem_permissao(role, 'observacao:criar')
    
    @staticmethod
    def pode_ver_relatorios(role):
        return PermissaoManager.tem_permissao(role, 'relatorios:tudo') or \
               PermissaoManager.tem_permissao(role, 'relatorios:academico')
    
    @staticmethod
    def turmas_visiveis(role, usuario_id, db_connection):
        """Retorna as turmas que o usuário pode ver baseado em sua role"""
        cursor = db_connection.cursor()
        
        if role == 'professor':
            # Professor vê apenas suas turmas
            cursor.execute('''
            SELECT * FROM turmas WHERE professor_id = ?
            ''', (usuario_id,))
        elif role == 'aluno':
            # Aluno vê apenas suas turmas (via matrícula)
            cursor.execute('''
            SELECT DISTINCT t.* FROM turmas t
            JOIN matriculas m ON t.id = m.turma_id
            JOIN alunos a ON m.aluno_id = a.id
            WHERE a.usuario_id = ?
            ''', (usuario_id,))
        else:
            # Admin, diretoria, comercial e pedagogo veem todas
            cursor.execute('SELECT * FROM turmas')
        
        return cursor.fetchall()
    
    @staticmethod
    def alunos_visiveis(role, usuario_id, db_connection):
        """Retorna os alunos que o usuário pode ver"""
        cursor = db_connection.cursor()
        
        if role == 'aluno':
            # Aluno vê apenas a si mesmo
            cursor.execute('''
            SELECT * FROM alunos WHERE usuario_id = ?
            ''', (usuario_id,))
        elif role == 'professor':
            # Professor vê alunos de suas turmas
            cursor.execute('''
            SELECT DISTINCT a.* FROM alunos a
            JOIN matriculas m ON a.id = m.aluno_id
            JOIN turmas t ON m.turma_id = t.id
            WHERE t.professor_id = ?
            ''', (usuario_id,))
        else:
            # Admin, diretoria, comercial e pedagogo veem todos
            cursor.execute('SELECT * FROM alunos')
        
        return cursor.fetchall()


def requer_autenticacao(f):
    """Decorator básico para requerer autenticação"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Acesso negado. Faça login primeiro.', 'error')
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function
