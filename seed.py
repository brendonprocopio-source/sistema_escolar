"""Dados de DEMONSTRAÇÃO para testar o sistema ou usar em aula.

    python seed.py

Só roda em banco sem alunos. As contas criadas usam uma senha de demonstração
conhecida — não use estes dados em uma instalação real.
"""
import random
import unicodedata
from datetime import date, timedelta

import auth
from app import criar_app
from db import executar, get_db, recalcular_financeiro, valor
from rotas.comercial import gerar_parcelas, somar_meses

SENHA_DEMO = "Demo@2026"


def cpf_falso(rng):
    """Gera um CPF matematicamente válido, mas fictício."""
    d = [rng.randint(0, 9) for _ in range(9)]
    for n in (9, 10):
        d.append((sum(d[i] * (n + 1 - i) for i in range(n)) * 10 % 11) % 10)
    return "".join(map(str, d))


def sem_acento(texto):
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()


def conta(email, tipo, tabela, ref):
    executar("""INSERT INTO usuarios (email, senha, tipo_usuario, tabela_referencia, id_referencia)
                VALUES (?, ?, ?, ?, ?)""", (email, auth.hash_senha(SENHA_DEMO), tipo, tabela, ref))


def semear():
    rng = random.Random(2026)
    hoje = date.today()
    if valor("SELECT COUNT(*) FROM alunos"):
        raise SystemExit("O banco já tem alunos. O seed só roda em banco vazio.")

    setores = {n: executar("INSERT OR IGNORE INTO setores (nome, descricao) VALUES (?, ?)", (n, d))
               for n, d in [("Secretaria", "Atendimento e matrículas"), ("Financeiro", "Cobrança e pagamentos"),
                            ("Pedagógico", "Coordenação de ensino")]}
    fid = executar("""INSERT INTO funcionarios (nome, email, cpf, senha, cargo, setor_id, data_admissao)
                      VALUES ('Marina Lopes', 'secretaria@demo.escola', ?, '', 'Secretária', ?, ?)""",
                   (cpf_falso(rng), setores["Secretaria"], (hoje - timedelta(days=700)).isoformat()))
    conta("secretaria@demo.escola", "funcionario", "funcionarios", fid)

    for cod, nome, cap, rec in [("S101", "Sala 101", 30, "Projetor"), ("LAB1", "Laboratório 1", 20, "20 computadores, projetor")]:
        executar("INSERT INTO salas (codigo, nome, capacidade, recursos) VALUES (?, ?, ?, ?)", (cod, nome, cap, rec))

    cursos = {}
    for nome, meses, preco, modulos in [
        ("Python para Iniciantes", 4, 960.0, ["Lógica de programação", "Estruturas de dados", "Projeto final"]),
        ("Desenvolvimento Web", 6, 1440.0, ["HTML e CSS", "JavaScript", "Back-end com Flask"]),
        ("Inglês Instrumental", 3, 600.0, ["Leitura técnica", "Vocabulário de TI"]),
    ]:
        cid = executar("INSERT INTO cursos (nome, descricao, duracao_meses, valor) VALUES (?, ?, ?, ?)",
                       (nome, f"Curso de {nome.lower()}.", meses, preco))
        cursos[nome] = (cid, preco, [executar(
            "INSERT INTO modulos (curso_id, nome, carga_horaria, ordem) VALUES (?, ?, 20, ?)", (cid, m, i + 1))
            for i, m in enumerate(modulos)])

    profs = []
    for i, (nome, esp) in enumerate([("Ana Ribeiro", "Programação"), ("Carlos Mendes", "Web"), ("Júlia Prado", "Idiomas")]):
        email = sem_acento(nome.split()[0]) + "@demo.escola"
        pid = executar("""INSERT INTO professores (nome, email, cpf, senha, matricula, formacao, especialidade)
                          VALUES (?, ?, ?, '', ?, 'Licenciatura', ?)""", (nome, email, cpf_falso(rng), f"PRF{hoje.year}{i + 1:04d}", esp))
        conta(email, "professor", "professores", pid)
        profs.append(pid)

    inicio = somar_meses(hoje, -2)
    turmas = []
    for i, (curso, horario, sala) in enumerate([
        ("Python para Iniciantes", "Seg e Qua, 19h–21h", "Laboratório 1"),
        ("Desenvolvimento Web", "Ter e Qui, 19h–21h", "Laboratório 1"),
        ("Inglês Instrumental", "Sáb, 9h–12h", "Sala 101"),
    ]):
        cid, preco, mods = cursos[curso]
        tid = executar("""INSERT INTO turmas (codigo, nome, curso_id, professor_id, semestre, data_inicio, data_fim,
                          horario, sala, capacidade) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                       (f"TUR{i + 1:03d}", f"{curso} — Turma A", cid, profs[i], f"{hoje.year}.2", inicio.isoformat(),
                        somar_meses(inicio, 5).isoformat(), horario, sala, 20))
        turmas.append((tid, preco, mods))
        for dias, titulo, tipo in [(5, "Avaliação do módulo", "Prova"), (12, "Entrega de projeto", "Evento")]:
            executar("""INSERT INTO cronograma (turma_id, titulo, data_evento, hora_inicio, hora_fim, local, tipo)
                        VALUES (?, ?, ?, '19:00', '21:00', ?, ?)""",
                     (tid, titulo, (hoje + timedelta(days=dias + i)).isoformat(), sala, tipo))

    nomes = ["Beatriz Almeida", "Caio Ferreira", "Daniela Souza", "Eduardo Lima", "Fernanda Castro", "Gabriel Rocha",
             "Helena Martins", "Igor Barbosa", "Juliana Teixeira", "Lucas Pereira", "Mariana Costa", "Nicolas Araújo",
             "Olívia Santos", "Pedro Carvalho", "Rafaela Gomes", "Samuel Dias", "Tainá Moreira", "Vitor Nunes"]
    aulas = [inicio + timedelta(days=d) for d in range(0, 56, 4) if inicio + timedelta(days=d) <= hoje]
    for i, nome in enumerate(nomes):
        email = sem_acento(".".join(nome.split())) + "@demo.escola"
        aid = executar("""INSERT INTO alunos (nome, email, cpf, senha, matricula, data_nascimento, telefone, cidade, estado)
                          VALUES (?, ?, ?, '', ?, ?, ?, 'São Paulo', 'SP')""",
                       (nome, email, cpf_falso(rng), f"ALN{hoje.year}{i + 1:04d}",
                        date(2004 + i % 5, 1 + i % 12, 1 + i % 27).isoformat(), f"(11) 9{rng.randint(1000, 9999)}-{rng.randint(1000, 9999)}"))
        conta(email, "aluno", "alunos", aid)
        executar("INSERT INTO status_aluno (aluno_id, status, data_atualizacao) VALUES (?, ?, ?)",
                 (aid, "Não iniciou" if i >= 16 else "Frequente", hoje.isoformat()))
        if i >= 16:
            continue                                   # dois alunos ainda sem turma
        tid, preco, mods = turmas[i % 3]
        mid = executar("INSERT INTO matriculas (aluno_id, turma_id, data_matricula) VALUES (?, ?, ?)",
                       (aid, tid, (inicio - timedelta(days=rng.randint(1, 20))).isoformat()))
        fin = executar("INSERT INTO financeiro (matricula_id, valor_total, data_vencimento, parcelas, descricao) VALUES (?, ?, ?, 6, 'Matrícula')",
                       (mid, preco, somar_meses(inicio, 0).isoformat()))
        gerar_parcelas(fin, preco, 6, date(inicio.year, inicio.month, 10))
        # paga as parcelas já vencidas (alguns alunos ficam com uma em atraso)
        executar("""UPDATE parcelas SET status = 'pago', data_pagamento = data_vencimento, metodo_pagamento = ?
                    WHERE financeiro_id = ? AND data_vencimento < ? AND numero_parcela <= ?""",
                 (rng.choice(["Pix", "Boleto", "Cartão de crédito"]), fin, hoje.isoformat(), 2 if i % 5 == 0 else 6))
        recalcular_financeiro(get_db(), fin)
        for dia in aulas:
            executar("INSERT INTO frequencias (matricula_id, data_aula, presente) VALUES (?, ?, ?)",
                     (mid, dia.isoformat(), 0 if rng.random() < (0.35 if i % 7 == 0 else 0.08) else 1))
        n = [round(rng.uniform(4.5 if i % 6 == 0 else 6.5, 10), 1) for _ in range(3)]
        executar("""INSERT INTO notas (matricula_id, modulo_id, primeira_nota, segunda_nota, terceira_nota, media_final)
                    VALUES (?, ?, ?, ?, ?, ?)""", (mid, mods[0], *n, round(sum(n) / 3, 2)))
    get_db().commit()
    print(f"\n  Dados de demonstração criados. Senha de todas as contas demo: {SENHA_DEMO}"
          "\n    secretaria@demo.escola  (secretaria)"
          "\n    ana@demo.escola         (professora)"
          "\n    beatriz.almeida@demo.escola (aluna)\n")


if __name__ == "__main__":
    app = criar_app()
    with app.app_context():
        semear()
