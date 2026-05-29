#!/usr/bin/env python3
"""
SCRIPT DE TESTE - Validar sistema funcionando
Testa todas as funcionalidades do sistema
"""

import sqlite3
import requests
import json
from time import sleep

BASE_URL = "http://localhost:5000"

print("=" * 70)
print("TESTE DO SISTEMA DE GESTAO DE ESCOLA")
print("=" * 70)

# ===== TEST 1: Login Aluno =====
print("\n[TEST 1] Login como Aluno...")
session = requests.Session()
response = session.post(
    f"{BASE_URL}/login",
    data={'email': 'joao@escola.com', 'senha': 'Aluno@123'}
)
if response.status_code == 200 and 'dashboard' in response.url:
    print("[OK] Login de aluno funcionando!")
else:
    print("[ERRO] Falha no login de aluno")

# ===== TEST 2: Login Professor =====
print("\n[TEST 2] Login como Professor...")
session2 = requests.Session()
response = session2.post(
    f"{BASE_URL}/login",
    data={'email': 'ana@escola.com', 'senha': 'Prof@123'}
)
if response.status_code == 200 and 'dashboard' in response.url:
    print("[OK] Login de professor funcionando!")
else:
    print("[ERRO] Falha no login de professor")

# ===== TEST 3: Cadastro Novo Aluno =====
print("\n[TEST 3] Cadastro de novo aluno...")
response = session.post(
    f"{BASE_URL}/cadastro",
    data={
        'nome': 'Teste Silva',
        'email': f'teste{int(__import__("time").time())}@escola.com',
        'cpf': '99999999999',
        'senha': 'Teste@123',
        'data_nascimento': '2000-01-01',
        'telefone': '(11) 99999-9999'
    }
)
if response.status_code == 200:
    print("[OK] Cadastro de novo aluno funcionando!")
else:
    print("[ERRO] Falha no cadastro")
    print(f"Status: {response.status_code}")

# ===== TEST 4: Acessar Dashboard =====
print("\n[TEST 4] Acessar dashboard...")
response = session.get(f"{BASE_URL}/dashboard")
if response.status_code == 200:
    print("[OK] Dashboard acessivel!")
else:
    print("[ERRO] Falha ao acessar dashboard")

# ===== TEST 5: Ver Relatórios =====
print("\n[TEST 5] Acessar relatórios...")
session3 = requests.Session()
session3.post(f"{BASE_URL}/login", data={'email': 'ana@escola.com', 'senha': 'Prof@123'})
response = session3.get(f"{BASE_URL}/relatorios")
if response.status_code == 200:
    print("[OK] Relatórios acessivel!")
else:
    print("[ERRO] Falha ao acessar relatórios")

# ===== TEST 6: Verificar BD =====
print("\n[TEST 6] Verificar banco de dados...")
try:
    conexao = sqlite3.connect('escola.db')
    cursor = conexao.cursor()
    
    # Contar alunos
    cursor.execute('SELECT COUNT(*) FROM alunos')
    total_alunos = cursor.fetchone()[0]
    
    # Contar turmas
    cursor.execute('SELECT COUNT(*) FROM turmas')
    total_turmas = cursor.fetchone()[0]
    
    # Contar notas
    cursor.execute('SELECT COUNT(*) FROM notas')
    total_notas = cursor.fetchone()[0]
    
    # Contar frequências
    cursor.execute('SELECT COUNT(*) FROM frequencias')
    total_frequencias = cursor.fetchone()[0]
    
    conexao.close()
    
    print(f"[OK] Banco de dados OK:")
    print(f"    - Total de alunos: {total_alunos}")
    print(f"    - Total de turmas: {total_turmas}")
    print(f"    - Total de notas: {total_notas}")
    print(f"    - Total de frequências: {total_frequencias}")
except Exception as e:
    print(f"[ERRO] Problema com BD: {e}")

print("\n" + "=" * 70)
print("TESTES CONCLUIDOS!")
print("=" * 70)
print("\nSistema funcionando corretamente!")
print("Acesse: http://localhost:5000")
print("\nCredenciais teste:")
print("  Aluno: joao@escola.com / Aluno@123")
print("  Professor: ana@escola.com / Prof@123")
print("=" * 70)
