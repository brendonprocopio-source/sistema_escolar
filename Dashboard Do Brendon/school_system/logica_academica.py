"""
MÓDULO ACADÊMICO - LÓGICA DE FREQUÊNCIA, NOTAS E OBSERVAÇÕES
"""

from datetime import date
import sqlite3

class GerenciadorFrequencia:
    """Gerencia chamadas e frequência"""
    
    @staticmethod
    def registrar_frequencia_aula(conexao, turma_id, data_aula, presencas_dict, usuario_id):
        """
        Registra a frequência de uma aula completa
        
        Args:
            conexao: conexão com banco de dados
            turma_id: ID da turma
            data_aula: data da aula
            presencas_dict: dicionário {matricula_id: presente (0/1)}
            usuario_id: ID do professor que registrou
        """
        
        cursor = conexao.cursor()
        
        try:
            for matricula_id, presente in presencas_dict.items():
                cursor.execute('''
                INSERT OR REPLACE INTO frequencias
                (matricula_id, turma_id, data_aula, presente, registrado_por)
                VALUES (?, ?, ?, ?, ?)
                ''', (matricula_id, turma_id, data_aula, presente, usuario_id))
            
            conexao.commit()
            return True, "✅ Frequência registrada com sucesso!"
        
        except Exception as e:
            conexao.rollback()
            return False, f"❌ Erro ao registrar frequência: {str(e)}"
    
    @staticmethod
    def obter_frequencia_aluno(conexao, aluno_id, turma_id=None):
        """
        Obtém resumo de frequência do aluno
        
        Args:
            conexao: conexão com banco de dados
            aluno_id: ID do aluno
            turma_id: ID da turma (opcional, para filtrar)
        
        Returns:
            dict: estatísticas de frequência
        """
        
        cursor = conexao.cursor()
        
        query = '''
        SELECT 
            COUNT(*) as total_aulas,
            SUM(CASE WHEN presente = 1 THEN 1 ELSE 0 END) as presentes,
            SUM(CASE WHEN presente = 0 THEN 1 ELSE 0 END) as faltas
        FROM frequencias f
        JOIN matriculas m ON f.matricula_id = m.id
        WHERE m.aluno_id = ?
        '''
        params = [aluno_id]
        
        if turma_id:
            query += " AND f.turma_id = ?"
            params.append(turma_id)
        
        cursor.execute(query, params)
        resultado = cursor.fetchone()
        
        if resultado[0] == 0:  # Sem aulas registradas
            return {
                'total_aulas': 0,
                'presentes': 0,
                'faltas': 0,
                'percentual': 0
            }
        
        percentual = (resultado[1] / resultado[0]) * 100
        
        return {
            'total_aulas': resultado[0],
            'presentes': resultado[1],
            'faltas': resultado[2],
            'percentual': round(percentual, 2)
        }
    
    @staticmethod
    def obter_presencas_turma(conexao, turma_id, data_aula):
        """
        Obtém lista de alunos com suas presenças em uma aula específica
        
        Args:
            conexao: conexão com banco de dados
            turma_id: ID da turma
            data_aula: data da aula
        
        Returns:
            list: alunos com status de presença
        """
        
        cursor = conexao.cursor()
        
        # Primeiro, pega todos os alunos matriculados
        cursor.execute('''
        SELECT m.id as matricula_id, a.id as aluno_id, u.nome, u.email
        FROM matriculas m
        JOIN alunos a ON m.aluno_id = a.id
        JOIN usuarios u ON a.usuario_id = u.id
        WHERE m.turma_id = ? AND m.status = 'ativa'
        ORDER BY u.nome
        ''', (turma_id,))
        
        alunos = cursor.fetchall()
        resultado = []
        
        for matricula_id, aluno_id, nome, email in alunos:
            # Buscar registro de presença
            cursor.execute('''
            SELECT presente FROM frequencias
            WHERE matricula_id = ? AND data_aula = ?
            ''', (matricula_id, data_aula))
            
            freq = cursor.fetchone()
            presente = freq[0] if freq else None
            
            resultado.append({
                'matricula_id': matricula_id,
                'aluno_id': aluno_id,
                'nome': nome,
                'email': email,
                'presente': presente  # None = não registrado, 0 = falta, 1 = presente
            })
        
        return resultado


class GerenciadorNotas:
    """Gerencia notas e avaliações"""
    
    @staticmethod
    def registrar_notas_bimestre(conexao, matricula_id, turma_id, bimestre, 
                                 nota_1, nota_2, nota_3, usuario_id):
        """
        Registra as 3 notas de um bimestre e calcula a média
        
        Args:
            conexao: conexão com banco de dados
            matricula_id: ID da matrícula
            turma_id: ID da turma
            bimestre: número do bimestre (1-4)
            nota_1, nota_2, nota_3: notas do bimestre
            usuario_id: ID do professor
        """
        
        cursor = conexao.cursor()
        
        # Calcular média
        media = (nota_1 + nota_2 + nota_3) / 3
        status = 'aprovado' if media >= 7 else 'recuperacao' if media >= 5 else 'reprovado'
        
        try:
            cursor.execute('''
            INSERT OR REPLACE INTO notas
            (matricula_id, turma_id, bimestre, nota_1, nota_2, nota_3, media_final, status, registrado_por)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (matricula_id, turma_id, bimestre, nota_1, nota_2, nota_3, media, status, usuario_id))
            
            conexao.commit()
            return True, f"✅ Notas registradas! Média: {media:.2f} ({status})"
        
        except Exception as e:
            conexao.rollback()
            return False, f"❌ Erro ao registrar notas: {str(e)}"
    
    @staticmethod
    def obter_notas_aluno(conexao, aluno_id, turma_id=None):
        """
        Obtém todas as notas de um aluno
        
        Args:
            conexao: conexão com banco de dados
            aluno_id: ID do aluno
            turma_id: ID da turma (opcional)
        
        Returns:
            list: notas do aluno
        """
        
        cursor = conexao.cursor()
        
        query = '''
        SELECT n.*, t.nome as turma_nome, c.nome as curso_nome
        FROM notas n
        JOIN matriculas m ON n.matricula_id = m.id
        JOIN turmas t ON n.turma_id = t.id
        JOIN cursos c ON t.curso_id = c.id
        WHERE m.aluno_id = ?
        '''
        params = [aluno_id]
        
        if turma_id:
            query += " AND n.turma_id = ?"
            params.append(turma_id)
        
        query += " ORDER BY n.bimestre DESC"
        
        cursor.execute(query, params)
        
        colunas = [desc[0] for desc in cursor.description]
        notas = []
        for row in cursor.fetchall():
            notas.append(dict(zip(colunas, row)))
        
        return notas
    
    @staticmethod
    def obter_notas_turma(conexao, turma_id, bimestre=None):
        """
        Obtém notas de todos os alunos de uma turma
        
        Args:
            conexao: conexão com banco de dados
            turma_id: ID da turma
            bimestre: número do bimestre (opcional)
        
        Returns:
            list: alunos com suas notas
        """
        
        cursor = conexao.cursor()
        
        query = '''
        SELECT 
            a.id as aluno_id, u.nome as aluno_nome, 
            n.bimestre, n.nota_1, n.nota_2, n.nota_3, n.media_final, n.status
        FROM matriculas m
        JOIN alunos a ON m.aluno_id = a.id
        JOIN usuarios u ON a.usuario_id = u.id
        LEFT JOIN notas n ON m.id = n.matricula_id
        WHERE m.turma_id = ? AND m.status = 'ativa'
        '''
        params = [turma_id]
        
        if bimestre:
            query += " AND n.bimestre = ?"
            params.append(bimestre)
        
        query += " ORDER BY u.nome, n.bimestre"
        
        cursor.execute(query, params)
        
        colunas = [desc[0] for desc in cursor.description]
        notas = []
        for row in cursor.fetchall():
            notas.append(dict(zip(colunas, row)))
        
        return notas


class GerenciadorObservacoes:
    """Gerencia observações e ocorrências do aluno"""
    
    @staticmethod
    def criar_observacao(conexao, aluno_id, titulo, descricao, tipo='geral', usuario_id=None):
        """
        Cria uma observação/ocorrência para um aluno
        
        Args:
            conexao: conexão com banco de dados
            aluno_id: ID do aluno
            titulo: título da observação
            descricao: descrição detalhada
            tipo: tipo de observação (comportamento, academico, saude, etc)
            usuario_id: ID do usuario que registrou
        """
        
        cursor = conexao.cursor()
        
        try:
            cursor.execute('''
            INSERT INTO observacoes_aluno
            (aluno_id, tipo, titulo, descricao, registrado_por)
            VALUES (?, ?, ?, ?, ?)
            ''', (aluno_id, tipo, titulo, descricao, usuario_id))
            
            conexao.commit()
            return True, "✅ Observação registrada com sucesso!"
        
        except Exception as e:
            conexao.rollback()
            return False, f"❌ Erro ao registrar observação: {str(e)}"
    
    @staticmethod
    def obter_observacoes_aluno(conexao, aluno_id, tipo=None):
        """
        Obtém todas as observações de um aluno
        
        Args:
            conexao: conexão com banco de dados
            aluno_id: ID do aluno
            tipo: tipo específico (opcional)
        
        Returns:
            list: observações do aluno
        """
        
        cursor = conexao.cursor()
        
        query = '''
        SELECT o.*, u.nome as registrado_por_nome
        FROM observacoes_aluno o
        LEFT JOIN usuarios u ON o.registrado_por = u.id
        WHERE o.aluno_id = ?
        '''
        params = [aluno_id]
        
        if tipo:
            query += " AND o.tipo = ?"
            params.append(tipo)
        
        query += " ORDER BY o.data_criacao DESC"
        
        cursor.execute(query, params)
        
        colunas = [desc[0] for desc in cursor.description]
        observacoes = []
        for row in cursor.fetchall():
            observacoes.append(dict(zip(colunas, row)))
        
        return observacoes
    
    @staticmethod
    def obter_historico_aluno(conexao, aluno_id):
        """
        Obtém histórico completo de um aluno (consolidado)
        
        Args:
            conexao: conexão com banco de dados
            aluno_id: ID do aluno
        
        Returns:
            dict: histórico consolidado
        """
        
        # Dados básicos
        cursor = conexao.cursor()
        cursor.execute('''
        SELECT a.*, u.nome, u.email, u.telefone
        FROM alunos a
        JOIN usuarios u ON a.usuario_id = u.id
        WHERE a.id = ?
        ''', (aluno_id,))
        
        aluno = cursor.fetchone()
        
        # Frequência consolidada
        freq = GerenciadorFrequencia.obter_frequencia_aluno(conexao, aluno_id)
        
        # Notas
        notas = GerenciadorNotas.obter_notas_aluno(conexao, aluno_id)
        
        # Observações
        observacoes = GerenciadorObservacoes.obter_observacoes_aluno(conexao, aluno_id)
        
        # Matrículas
        cursor.execute('''
        SELECT m.*, t.nome as turma_nome, c.nome as curso_nome
        FROM matriculas m
        JOIN turmas t ON m.turma_id = t.id
        JOIN cursos c ON t.curso_id = c.id
        WHERE m.aluno_id = ?
        ORDER BY m.data_matricula DESC
        ''', (aluno_id,))
        
        matriculas = cursor.fetchall()
        
        return {
            'aluno': aluno,
            'frequencia': freq,
            'notas': notas,
            'observacoes': observacoes,
            'matriculas': matriculas
        }
