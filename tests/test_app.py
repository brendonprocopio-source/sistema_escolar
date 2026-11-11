"""Testes de ponta a ponta.  Rodar:  python -m pytest -q"""
import io
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ADMIN = ("admin@escola.com", "Admin@12345")


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("DADOS_DIR", str(tmp_path))
    monkeypatch.setenv("ADMIN_SENHA", ADMIN[1])
    import auth
    from app import criar_app
    auth._tentativas.clear()
    app = criar_app({"TESTING": True})
    with app.app_context():
        from db import executar, get_db
        executar("UPDATE usuarios SET trocar_senha = 0")
        get_db().commit()
    return app


class Navegador:
    """Cliente de teste que cuida do token CSRF."""

    def __init__(self, app):
        self.c = app.test_client()

    def get(self, url, **kw):
        return self.c.get(url, **kw)

    def post(self, url, dados=None, **kw):
        pagina = self.c.get("/login").get_data(as_text=True) + self.c.get("/conta/senha").get_data(as_text=True)
        token = re.search(r'name="_csrf" value="([^"]+)"', pagina).group(1)
        return self.c.post(url, data={**(dados or {}), "_csrf": token}, **kw)

    def entrar(self, email, senha):
        return self.post("/login", {"email": email, "senha": senha})


@pytest.fixture()
def nav(app):
    n = Navegador(app)
    assert n.entrar(*ADMIN).status_code == 302
    return n


def senha_provisoria(resposta):
    return re.search(r"Senha provisória de acesso: (\w+)", resposta.get_data(as_text=True)).group(1)


def montar_escola(nav):
    """Cria curso, módulo, professor, turma e aluno; devolve a senha provisória do professor e do aluno."""
    assert nav.post("/cursos/novo", {"nome": "Python", "valor": "900", "duracao_meses": "3"}).status_code == 302
    assert nav.post("/modulos/novo", {"curso_id": "1", "nome": "Lógica", "ordem": "1"}).status_code == 302
    r = nav.post("/professores/novo", {"nome": "Ana Ribeiro", "email": "ana@x.com", "cpf": "529.982.247-25"},
                 follow_redirects=True)
    senha_prof = senha_provisoria(r)
    assert nav.post("/turmas/novo", {"codigo": "T1", "nome": "Python A", "curso_id": "1", "professor_id": "1",
                                     "capacidade": "1"}).status_code == 302
    r = nav.post("/alunos/novo", {"nome": "Beatriz Lima", "email": "bia@x.com", "cpf": "111.444.777-35"},
                 follow_redirects=True)
    return senha_prof, senha_provisoria(r)


def test_paginas_exigem_login(app):
    c = app.test_client()
    for url in ("/painel", "/alunos", "/financeiro", "/usuarios", "/alunos/1"):
        assert c.get(url).status_code == 302
    assert c.get("/cadastro").status_code == 404            # autocadastro desligado por padrão


def test_login_errado_e_bloqueio(app):
    n = Navegador(app)
    for _ in range(5):
        assert n.entrar(ADMIN[0], "errada").status_code == 401
    assert n.entrar(*ADMIN).status_code == 429               # bloqueado mesmo com a senha certa


def test_post_sem_csrf_e_recusado(app):
    assert app.test_client().post("/login", data={"email": "a", "senha": "b"}).status_code == 400


def test_todas_as_telas_abrem(nav):
    montar_escola(nav)
    urls = ["/painel", "/alunos", "/alunos?ver=inativos", "/alunos/novo", "/alunos/1", "/alunos/1/editar",
            "/professores", "/turmas", "/turmas/1", "/turmas/1/frequencia", "/turmas/1/notas", "/matriculas",
            "/matriculas/nova", "/financeiro", "/financeiro?ver=todas", "/cronograma", "/cronograma/novo",
            "/salas", "/relatorios", "/cursos", "/modulos", "/funcionarios", "/setores", "/usuarios",
            "/auditoria", "/conta/senha"]
    urls += [f"/relatorios/{r}" for r in ("turmas", "frequencia", "desempenho", "inadimplencia", "recebimentos")]
    for url in urls:
        assert nav.get(url).status_code == 200, url
    assert nav.get("/nao-existe").status_code == 404
    csv = nav.get("/relatorios/turmas?formato=csv")
    assert csv.mimetype == "text/csv" and "Python A" in csv.get_data(as_text=True)


def test_validacoes_de_cadastro(nav):
    montar_escola(nav)
    r = nav.post("/alunos/novo", {"nome": "X Y Z", "email": "outro@x.com", "cpf": "123.456.789-00"})
    assert "CPF inválido" in r.get_data(as_text=True)
    r = nav.post("/alunos/novo", {"nome": "X Y Z", "email": "bia@x.com", "cpf": "390.533.447-05"})
    assert "Já existe" in r.get_data(as_text=True)
    r = nav.post("/turmas/novo", {"codigo": "T1", "nome": "Repetida", "curso_id": "1", "professor_id": "1"})
    assert "Já existe" in r.get_data(as_text=True)


def test_matricula_parcelas_e_pagamento(app, nav):
    montar_escola(nav)
    r = nav.post("/matriculas/nova", {"aluno_id": "1", "turma_id": "1", "valor_total": "1000", "parcelas": "3",
                                      "vencimento": "2026-01-31"})
    assert r.status_code == 302
    with app.app_context():
        from db import todos, um
        parcelas = todos("SELECT * FROM parcelas ORDER BY numero_parcela")
        assert [p["valor_parcela"] for p in parcelas] == [333.33, 333.33, 333.34]      # centavos na última
        assert [p["data_vencimento"] for p in parcelas] == ["2026-01-31", "2026-02-28", "2026-03-31"]
        assert um("SELECT status FROM status_aluno ORDER BY id DESC")["status"] == "Frequente"

    # mesma turma de novo: recusado (já matriculado)
    r = nav.post("/matriculas/nova", {"aluno_id": "1", "turma_id": "1", "valor_total": "10", "parcelas": "1",
                                      "vencimento": "2026-01-31"})
    assert "já está matriculado" in r.get_data(as_text=True)
    # turma com 1 vaga: segundo aluno não entra
    nav.post("/alunos/novo", {"nome": "Caio Souza", "email": "caio@x.com", "cpf": "390.533.447-05"})
    r = nav.post("/matriculas/nova", {"aluno_id": "2", "turma_id": "1", "valor_total": "10", "parcelas": "1",
                                      "vencimento": "2026-01-31"})
    assert "lotada" in r.get_data(as_text=True)

    assert nav.post("/parcelas/1/pagar", {"metodo": "Pix"}).status_code == 302
    assert nav.post("/parcelas/1/pagar", {"metodo": "Pix"}, follow_redirects=True).status_code == 200  # não paga 2x
    with app.app_context():
        from db import um
        f = um("SELECT * FROM financeiro")
        assert (f["valor_pago"], f["status"]) == (333.33, "parcial")
    nav.post("/parcelas/1/estornar")
    nav.post("/matriculas/1/cancelar")
    with app.app_context():
        from db import um, valor
        assert um("SELECT status FROM financeiro")["status"] == "cancelado"
        assert valor("SELECT COUNT(*) FROM parcelas WHERE status = 'cancelada'") == 3


def test_chamada_e_notas_nao_duplicam(app, nav):
    montar_escola(nav)
    nav.post("/matriculas/nova", {"aluno_id": "1", "turma_id": "1", "valor_total": "0", "parcelas": "1",
                                  "vencimento": "2026-01-31"})
    for presente in ({"p_1": "on"}, {}):
        assert nav.post("/turmas/1/frequencia", {"data": "2026-03-02", **presente}).status_code == 302
    assert nav.post("/turmas/1/notas", {"modulo": "1", "n1_1": "8", "n2_1": "7,5"}).status_code == 302
    assert nav.post("/turmas/1/notas", {"modulo": "1", "n1_1": "9", "n2_1": "7"}).status_code == 302
    r = nav.post("/turmas/1/notas", {"modulo": "1", "n1_1": "11"})
    assert "0 a 10" in r.get_data(as_text=True)
    with app.app_context():
        from db import todos
        freq, notas = todos("SELECT * FROM frequencias"), todos("SELECT * FROM notas")
        assert len(freq) == 1 and freq[0]["presente"] == 0
        assert len(notas) == 1 and notas[0]["media_final"] == 8.0


def test_permissoes_por_perfil(app, nav):
    senha_prof, senha_aluno = montar_escola(nav)
    nav.post("/alunos/novo", {"nome": "Caio Souza", "email": "caio@x.com", "cpf": "390.533.447-05"})
    nav.post("/matriculas/nova", {"aluno_id": "1", "turma_id": "1", "valor_total": "100", "parcelas": "1",
                                  "vencimento": "2026-01-31"})

    aluno = Navegador(app)
    aluno.entrar("bia@x.com", senha_aluno)
    assert aluno.get("/painel").headers["Location"] == "/conta/senha"        # senha provisória: obrigado a trocar
    aluno.post("/conta/senha", {"atual": senha_aluno, "nova": "Nova@12345", "confirmar": "Nova@12345"})
    assert aluno.get("/alunos/1").status_code == 200
    for url in ("/alunos/2", "/alunos", "/financeiro", "/turmas/1", "/usuarios", "/relatorios/turmas"):
        assert aluno.get(url).status_code == 403, url
    assert aluno.post("/parcelas/1/pagar", {"metodo": "Pix"}).status_code == 403
    assert "Observações pedagógicas" not in aluno.get("/alunos/1").get_data(as_text=True)

    prof = Navegador(app)
    prof.entrar("ana@x.com", senha_prof)
    prof.post("/conta/senha", {"atual": senha_prof, "nova": "Nova@12345", "confirmar": "Nova@12345"})
    assert prof.get("/turmas/1").status_code == 200 and prof.get("/alunos/1").status_code == 200
    for url in ("/alunos/2", "/financeiro", "/cursos", "/alunos"):          # aluno 2 não é da turma dele
        assert prof.get(url).status_code == 403, url
    ficha = prof.get("/alunos/1").get_data(as_text=True)
    assert "111.444.777" not in ficha and "11144477735" not in ficha         # professor não vê CPF


def test_anexos(app, nav, tmp_path):
    montar_escola(nav)
    r = nav.post("/alunos/1/anexos", {"arquivo": (io.BytesIO(b"x"), "../../virus.exe")},
                 content_type="multipart/form-data", follow_redirects=True)
    assert "não permitido" in r.get_data(as_text=True)
    nav.post("/alunos/1/anexos", {"arquivo": (io.BytesIO(b"%PDF-1.4"), "../../contrato.pdf")},
             content_type="multipart/form-data")
    guardados = list((tmp_path / "uploads").iterdir())
    assert len(guardados) == 1 and re.fullmatch(r"[0-9a-f]{32}\.pdf", guardados[0].name)
    assert nav.get("/anexos/1").data == b"%PDF-1.4"
    nav.post("/anexos/1/excluir")
    assert not list((tmp_path / "uploads").iterdir())


def test_usuarios_e_backup(nav):
    montar_escola(nav)
    assert nav.post("/usuarios/1/alternar").status_code == 400              # não bloqueia a si mesmo
    assert nav.post("/usuarios/2/alternar").status_code == 302
    assert Navegador(nav.c.application).entrar("ana@x.com", "qualquer").status_code == 401
    r = nav.post("/backup")
    assert r.status_code == 200 and r.data.startswith(b"SQLite format 3")
