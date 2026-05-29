"""
CRIAR USUÁRIO ADMIN NO BANCO DE DADOS
"""

import sqlite3
from binascii import hexlify
import hashlib
import secrets

def criar_admin():
    """Cria usuário admin no sistema"""
    
    def hash_senha(senha):
        salt = secrets.token_hex(32)
        hash_obj = hashlib.pbkdf2_hmac(
            'sha256',
            senha.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return f"{salt}${hexlify(hash_obj).decode()}"
    
    conexao = sqlite3.connect('escola.db')
    cursor = conexao.cursor()
    
    try:
        # Verificar se admin já existe
        cursor.execute("SELECT id FROM usuarios WHERE email = 'admin@escola.com'")
        if cursor.fetchone():
            print("[INFO] Admin ja existe no sistema")
            conexao.close()
            return
        
        # Criar funcionário admin
        cursor.execute('''
        INSERT INTO funcionarios (nome, email, cpf, senha, cargo, setor_id, salario)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('Administrador', 'admin@escola.com', '00000000000', 
              hash_senha('Mudar@123'), 'Administrador', 1, 0))
        
        admin_id = cursor.lastrowid
        
        # Criar usuário de login
        cursor.execute('''
        INSERT INTO usuarios (email, senha, tipo_usuario, tabela_referencia, id_referencia)
        VALUES (?, ?, ?, ?, ?)
        ''', ('admin@escola.com', hash_senha('Mudar@123'), 'admin', 'funcionarios', admin_id))
        
        conexao.commit()
        print("[OK] Usuario admin criado com sucesso!")
        print("Email: admin@escola.com")
        print("Senha: Mudar@123")
        
    except Exception as e:
        print(f"[ERRO] {e}")
    finally:
        conexao.close()

if __name__ == "__main__":
    criar_admin()
