@echo off
REM Script para Exportar Dados do Banco de Dados SQLite
REM Cria CSVs de todas as tabelas

echo ========================================
echo Exportando dados do banco...
echo ========================================
echo.

cd tmp\school_system

REM Exporte cada tabela como CSV
echo Exportando tabela: usuarios
sqlite3 escola.db ".mode csv" ".output export_usuarios.csv" "SELECT * FROM usuarios;"

echo Exportando tabela: alunos
sqlite3 escola.db ".mode csv" ".output export_alunos.csv" "SELECT * FROM alunos;"

echo Exportando tabela: professores
sqlite3 escola.db ".mode csv" ".output export_professores.csv" "SELECT * FROM professores;"

echo Exportando tabela: funcionarios
sqlite3 escola.db ".mode csv" ".output export_funcionarios.csv" "SELECT * FROM funcionarios;"

echo Exportando tabela: cursos
sqlite3 escola.db ".mode csv" ".output export_cursos.csv" "SELECT * FROM cursos;"

echo Exportando tabela: modulos
sqlite3 escola.db ".mode csv" ".output export_modulos.csv" "SELECT * FROM modulos;"

echo Exportando tabela: turmas
sqlite3 escola.db ".mode csv" ".output export_turmas.csv" "SELECT * FROM turmas;"

echo Exportando tabela: matriculas
sqlite3 escola.db ".mode csv" ".output export_matriculas.csv" "SELECT * FROM matriculas;"

echo Exportando tabela: frequencias
sqlite3 escola.db ".mode csv" ".output export_frequencias.csv" "SELECT * FROM frequencias;"

echo Exportando tabela: notas
sqlite3 escola.db ".mode csv" ".output export_notas.csv" "SELECT * FROM notas;"

echo.
echo ========================================
echo Exportacao concluida!
echo Arquivos criados:
echo - export_*.csv
echo ========================================
echo.

cd ..\..
pause
