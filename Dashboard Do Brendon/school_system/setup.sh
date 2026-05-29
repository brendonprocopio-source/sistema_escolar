#!/bin/bash
# Script para inicializar o sistema de gestão de escola

echo "================================"
echo "Sistema de Gestão de Escola"
echo "================================"

# Instalar dependências
echo ""
echo "Instalando dependências..."
pip install -r requirements.txt

# Criar banco de dados
echo ""
echo "Criando banco de dados..."
python database.py

echo ""
echo "================================"
echo "Aplicação pronta!"
echo "================================"
echo ""
echo "Para iniciar a aplicação, execute:"
echo "python app.py"
echo ""
echo "Acesse em seu navegador:"
echo "http://localhost:5000"
echo ""
echo "Dados de teste:"
echo "- Login: aluno@escola.com"
echo "- Senha: Aluno@123"
echo ""
