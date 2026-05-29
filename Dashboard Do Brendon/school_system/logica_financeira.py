"""
MÓDULO FINANCEIRO - LÓGICA DE PARCELAS E PAGAMENTOS
Integração: Matrícula -> Gera Parcelas Automáticas
"""

from datetime import date, timedelta
import sqlite3

class GeradorParcelas:
    """Responsável por gerar e gerenciar parcelas de pagamento"""
    
    @staticmethod
    def gerar_parcelas_matricula(conexao, matricula_id, valor_total, quantidade_parcelas, 
                                 data_inicio_vencimento=None):
        """
        Gera automaticamente as parcelas quando uma matrícula é criada
        
        Args:
            conexao: conexão com banco de dados
            matricula_id: ID da matrícula
            valor_total: valor total a ser parcelado
            quantidade_parcelas: quantidade de parcelas
            data_inicio_vencimento: data da primeira parcela (padrão: hoje + 30 dias)
        """
        
        cursor = conexao.cursor()
        
        if not data_inicio_vencimento:
            data_inicio_vencimento = date.today() + timedelta(days=30)
        
        valor_parcela = valor_total / quantidade_parcelas
        
        try:
            for numero in range(1, quantidade_parcelas + 1):
                data_vencimento = data_inicio_vencimento + timedelta(days=30 * (numero - 1))
                
                cursor.execute('''
                INSERT INTO parcelas 
                (matricula_id, numero_parcela, valor, data_vencimento, status)
                VALUES (?, ?, ?, ?, 'pendente')
                ''', (matricula_id, numero, valor_parcela, data_vencimento))
            
            conexao.commit()
            return True, f"✅ {quantidade_parcelas} parcelas criadas com sucesso!"
        
        except Exception as e:
            conexao.rollback()
            return False, f"❌ Erro ao gerar parcelas: {str(e)}"
    
    @staticmethod
    def registrar_pagamento_parcela(conexao, parcela_id, data_pagamento=None, 
                                   metodo_pagamento='dinheiro', comprovante=None):
        """
        Registra o pagamento de uma parcela
        
        Args:
            conexao: conexão com banco de dados
            parcela_id: ID da parcela
            data_pagamento: data do pagamento (padrão: hoje)
            metodo_pagamento: método usado (dinheiro, cartao, boleto, pix)
            comprovante: arquivo/referência de comprovante
        """
        
        cursor = conexao.cursor()
        
        if not data_pagamento:
            data_pagamento = date.today()
        
        try:
            cursor.execute('''
            UPDATE parcelas 
            SET status = 'pago', 
                data_pagamento = ?, 
                metodo_pagamento = ?,
                comprovante = ?,
                data_atualizacao = CURRENT_TIMESTAMP
            WHERE id = ?
            ''', (data_pagamento, metodo_pagamento, comprovante, parcela_id))
            
            conexao.commit()
            return True, "✅ Pagamento registrado com sucesso!"
        
        except Exception as e:
            conexao.rollback()
            return False, f"❌ Erro ao registrar pagamento: {str(e)}"
    
    @staticmethod
    def calcular_receita_mes(conexao, mes=None, ano=None):
        """
        Calcula a receita do mês (soma de parcelas PAGAS no mês)
        
        Args:
            conexao: conexão com banco de dados
            mes: mês (1-12), padrão = mês atual
            ano: ano, padrão = ano atual
        """
        
        cursor = conexao.cursor()
        
        if not mes or not ano:
            hoje = date.today()
            mes = mes or hoje.month
            ano = ano or hoje.year
        
        # Formatar data para query SQLite
        data_inicio = f"{ano}-{mes:02d}-01"
        if mes == 12:
            data_fim = f"{ano+1}-01-01"
        else:
            data_fim = f"{ano}-{mes+1:02d}-01"
        
        cursor.execute('''
        SELECT COALESCE(SUM(valor), 0) as total_receita
        FROM parcelas
        WHERE status = 'pago' 
        AND data_pagamento >= ? 
        AND data_pagamento < ?
        ''', (data_inicio, data_fim))
        
        resultado = cursor.fetchone()
        return resultado[0] if resultado else 0
    
    @staticmethod
    def calcular_pendentes_totais(conexao):
        """
        Calcula o total de parcelas PENDENTES no sistema
        
        Args:
            conexao: conexão com banco de dados
        
        Returns:
            float: soma total de parcelas pendentes
        """
        
        cursor = conexao.cursor()
        
        cursor.execute('''
        SELECT COALESCE(SUM(valor), 0) as total_pendente
        FROM parcelas
        WHERE status = 'pendente'
        ''')
        
        resultado = cursor.fetchone()
        return resultado[0] if resultado else 0
    
    @staticmethod
    def calcular_pendentes_aluno(conexao, aluno_id):
        """
        Calcula o total pendente de um aluno específico
        
        Args:
            conexao: conexão com banco de dados
            aluno_id: ID do aluno
        
        Returns:
            float: soma de parcelas pendentes do aluno
        """
        
        cursor = conexao.cursor()
        
        cursor.execute('''
        SELECT COALESCE(SUM(p.valor), 0) as total_pendente
        FROM parcelas p
        JOIN matriculas m ON p.matricula_id = m.id
        WHERE m.aluno_id = ? AND p.status = 'pendente'
        ''', (aluno_id,))
        
        resultado = cursor.fetchone()
        return resultado[0] if resultado else 0
    
    @staticmethod
    def obter_parcelas_aluno(conexao, aluno_id, filtro_status=None):
        """
        Obtém todas as parcelas de um aluno
        
        Args:
            conexao: conexão com banco de dados
            aluno_id: ID do aluno
            filtro_status: 'pago', 'pendente' ou None (todas)
        
        Returns:
            list: lista de parcelas
        """
        
        cursor = conexao.cursor()
        
        query = '''
        SELECT p.*, m.turma_id, t.nome as turma_nome, c.nome as curso_nome
        FROM parcelas p
        JOIN matriculas m ON p.matricula_id = m.id
        JOIN turmas t ON m.turma_id = t.id
        JOIN cursos c ON t.curso_id = c.id
        WHERE m.aluno_id = ?
        '''
        
        if filtro_status:
            query += f" AND p.status = '{filtro_status}'"
        
        query += " ORDER BY p.data_vencimento DESC"
        
        cursor.execute(query, (aluno_id,))
        
        # Retornar como dicionários
        colunas = [desc[0] for desc in cursor.description]
        parcelas = []
        for row in cursor.fetchall():
            parcelas.append(dict(zip(colunas, row)))
        
        return parcelas
    
    @staticmethod
    def obter_inadimplentes(conexao):
        """
        Obtém alunos com parcelas vencidas não pagas
        
        Args:
            conexao: conexão com banco de dados
        
        Returns:
            list: lista de alunos inadimplentes com detalhes
        """
        
        cursor = conexao.cursor()
        
        cursor.execute('''
        SELECT DISTINCT
            a.id as aluno_id,
            u.nome,
            u.email,
            u.telefone,
            t.nome as turma_nome,
            COUNT(p.id) as parcelas_atraso,
            SUM(p.valor) as total_devido,
            MIN(p.data_vencimento) as primeira_parcela_atrasada
        FROM alunos a
        JOIN usuarios u ON a.usuario_id = u.id
        JOIN matriculas m ON a.id = m.aluno_id
        JOIN turmas t ON m.turma_id = t.id
        JOIN parcelas p ON m.id = p.matricula_id
        WHERE p.status = 'pendente' 
        AND p.data_vencimento < DATE('now')
        GROUP BY a.id
        ORDER BY total_devido DESC
        ''')
        
        colunas = [desc[0] for desc in cursor.description]
        inadimplentes = []
        for row in cursor.fetchall():
            inadimplentes.append(dict(zip(colunas, row)))
        
        return inadimplentes
    
    @staticmethod
    def obter_extrato_financeiro_aluno(conexao, aluno_id):
        """
        Obtém extrato financeiro completo de um aluno
        (todas as parcelas com status)
        
        Args:
            conexao: conexão com banco de dados
            aluno_id: ID do aluno
        
        Returns:
            dict: estrutura com resumo e detalhes
        """
        
        cursor = conexao.cursor()
        
        # Resumo
        cursor.execute('''
        SELECT 
            COALESCE(SUM(p.valor), 0) as total,
            COALESCE(SUM(CASE WHEN p.status = 'pago' THEN p.valor ELSE 0 END), 0) as pago,
            COALESCE(SUM(CASE WHEN p.status = 'pendente' THEN p.valor ELSE 0 END), 0) as pendente
        FROM parcelas p
        JOIN matriculas m ON p.matricula_id = m.id
        WHERE m.aluno_id = ?
        ''', (aluno_id,))
        
        resumo = cursor.fetchone()
        
        # Detalhes
        parcelas = GeradorParcelas.obter_parcelas_aluno(conexao, aluno_id)
        
        return {
            'aluno_id': aluno_id,
            'resumo': {
                'total': resumo[0] if resumo else 0,
                'pago': resumo[1] if resumo else 0,
                'pendente': resumo[2] if resumo else 0,
                'percentual_pago': (resumo[1] / resumo[0] * 100) if resumo and resumo[0] > 0 else 0
            },
            'parcelas': parcelas
        }


class RangerFinanceiro:
    """Serviço para gerar e exportar rangers/relatórios financeiros"""
    
    @staticmethod
    def ranger_diario(conexao, data=None):
        """Ranger de pagamentos do dia"""
        if not data:
            data = date.today()
        
        cursor = conexao.cursor()
        cursor.execute('''
        SELECT 
            COUNT(*) as total_pagamentos,
            SUM(valor) as total_arrecadado,
            metodo_pagamento
        FROM parcelas
        WHERE data_pagamento = ? AND status = 'pago'
        GROUP BY metodo_pagamento
        ''', (data,))
        
        return cursor.fetchall()
    
    @staticmethod
    def ranger_mensal(conexao, mes, ano):
        """Ranger de pagamentos do mês"""
        cursor = conexao.cursor()
        
        data_inicio = f"{ano}-{mes:02d}-01"
        if mes == 12:
            data_fim = f"{ano+1}-01-01"
        else:
            data_fim = f"{ano}-{mes+1:02d}-01"
        
        cursor.execute('''
        SELECT 
            SUM(valor) as total_pago,
            COUNT(*) as quantidade_pagamentos
        FROM parcelas
        WHERE status = 'pago'
        AND data_pagamento >= ?
        AND data_pagamento < ?
        ''', (data_inicio, data_fim))
        
        return cursor.fetchone()
