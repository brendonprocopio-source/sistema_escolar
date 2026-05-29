"""
AUTENTICACAO E CRIPTOGRAFIA
Sistema de login seguro com hash de senhas
"""

import sqlite3
import hashlib
import secrets
import string
from binascii import hexlify
from functools import wraps

class Autenticacao:
    """Gerencia autenticacao e criptografia de senhas"""
    
    @staticmethod
    def hash_senha(senha):
        """
        Criptografa uma senha usando PBKDF2
        Nunca armazena senha em texto plano!
        """
        salt = secrets.token_hex(32)
        
        hash_obj = hashlib.pbkdf2_hmac(
            'sha256',
            senha.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        
        return f"{salt}${hexlify(hash_obj).decode()}"
    
    @staticmethod
    def verificar_senha(senha, senha_hash):
        """
        Verifica se a senha corresponde ao hash armazenado
        """
        try:
            salt, hash_armazenado = senha_hash.split('$')
            
            hash_novo = hashlib.pbkdf2_hmac(
                'sha256',
                senha.encode('utf-8'),
                salt.encode('utf-8'),
                100000
            )
            
            return hexlify(hash_novo).decode() == hash_armazenado
        except:
            return False
    
    @staticmethod
    def autenticar(email, senha):
        """
        Autentica um usuario verificando email e senha
        Retorna dados do usuario se correto, None se incorreto
        """
        conexao = sqlite3.connect('escola.db')
        conexao.row_factory = sqlite3.Row
        cursor = conexao.cursor()
        
        try:
            cursor.execute('SELECT * FROM usuarios WHERE email = ? AND ativo = 1', (email,))
            usuario = cursor.fetchone()
            
            if not usuario:
                return None
            
            if Autenticacao.verificar_senha(senha, usuario['senha']):
                return dict(usuario)
            
            return None
        finally:
            conexao.close()
    
    @staticmethod
    def gerar_senha_temporaria(tamanho=12):
        """Gera uma senha temporaria aleatoria"""
        caracteres = string.ascii_letters + string.digits + "!@#$%"
        return ''.join(secrets.choice(caracteres) for _ in range(tamanho))
    
    @staticmethod
    def registrar_usuario(email, senha, tipo_usuario, tabela_referencia, id_referencia):
        """
        Registra um novo usuario no banco de dados
        """
        conexao = sqlite3.connect('escola.db')
        cursor = conexao.cursor()
        
        try:
            senha_hash = Autenticacao.hash_senha(senha)
            
            cursor.execute('''
            INSERT INTO usuarios (email, senha, tipo_usuario, tabela_referencia, id_referencia)
            VALUES (?, ?, ?, ?, ?)
            ''', (email, senha_hash, tipo_usuario, tabela_referencia, id_referencia))
            
            conexao.commit()
            return True, "Usuario registrado com sucesso!"
        except sqlite3.IntegrityError:
            return False, "Email ja cadastrado!"
        except Exception as e:
            return False, f"Erro ao registrar: {str(e)}"
        finally:
            conexao.close()
    
    @staticmethod
    def obter_dados_usuario(id_usuario, tipo_usuario):
        """Obtem os dados completos do usuario baseado no tipo"""
        conexao = sqlite3.connect('escola.db')
        conexao.row_factory = sqlite3.Row
        cursor = conexao.cursor()
        
        try:
            if tipo_usuario == 'aluno':
                cursor.execute('SELECT * FROM alunos WHERE id = ?', (id_usuario,))
            elif tipo_usuario == 'professor':
                cursor.execute('SELECT * FROM professores WHERE id = ?', (id_usuario,))
            elif tipo_usuario == 'funcionario':
                cursor.execute('SELECT * FROM funcionarios WHERE id = ?', (id_usuario,))
            else:
                return None
            
            resultado = cursor.fetchone()
            return dict(resultado) if resultado else None
        finally:
            conexao.close()


def login_requerido(tipo_usuario=None):
    """
    Decorator para proteger rotas que requerem login
    Se tipo_usuario for especificado, verifica se o usuario eh daquele tipo
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import session, redirect, flash
            if 'usuario_id' not in session:
                flash('Faca login para acessar esta pagina', 'error')
                return redirect('/login')
            
            if tipo_usuario and session.get('tipo_usuario') != tipo_usuario:
                flash('Acesso negado. Tipo de usuario invalido.', 'error')
                return redirect('/dashboard')
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


if __name__ == "__main__":
    print("="*50)
    print("TESTE DE CRIPTOGRAFIA")
    print("="*50)
    
    senha_original = "Senha@Segura123"
    print(f"\nSenha original: {senha_original}")
    
    senha_hash = Autenticacao.hash_senha(senha_original)
    print(f"Hash armazenado: {senha_hash[:50]}...")
    
    resultado1 = Autenticacao.verificar_senha(senha_original, senha_hash)
    print(f"Verificacao com senha correta: {resultado1} OK")
    
    resultado2 = Autenticacao.verificar_senha("SenhaErrada", senha_hash)
    print(f"Verificacao com senha incorreta: {resultado2} OK")
    
    temp_pass = Autenticacao.gerar_senha_temporaria()
    print(f"\nSenha temporaria gerada: {temp_pass}")
