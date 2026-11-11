# Sistema de Gestão Escolar

Sistema web para escolas e cursos livres: alunos, professores, turmas, chamada, notas,
matrículas, parcelas, relatórios e controle de acesso por perfil.
Feito com **Flask + SQLite**, sem dependências de front-end (nenhum CDN, funciona offline).

## Como rodar

**No Windows (mais fácil):** dê dois cliques em `iniciar.bat`, ou no PowerShell, dentro da pasta:

```powershell
.\iniciar.ps1            # instala o que falta, inicia e abre o navegador
.\iniciar.ps1 -Demo      # primeira vez com dados de demonstração
.\iniciar.ps1 -Porta 8080
.\iniciar.ps1 -Testes    # roda os testes
```

O script confere o Python, cria o ambiente `.venv`, instala as dependências só quando mudam,
oferece reaproveitar um `escola.db` antigo e abre o navegador quando o sistema estiver no ar.

**Em qualquer sistema (manual):**

```bash
pip install -r requirements.txt
python app.py                 # abre em http://localhost:5000
```

Na primeira execução o sistema cria o banco em `dados/escola.db` e mostra **no terminal**
o e-mail e a senha inicial do administrador (a troca é obrigatória no primeiro acesso).

Para experimentar com dados de demonstração (banco vazio):

```bash
python seed.py                # cria cursos, turmas, 18 alunos, parcelas, notas…
```

Com Docker: `docker compose up -d --build` (a senha inicial aparece em `docker compose logs`).

### Já usava a versão anterior?

Copie o seu `escola.db` antigo para a pasta `dados/` antes de iniciar. As tabelas são as
mesmas; na primeira execução o sistema ajusta o que falta (índices, parcelas, colunas novas)
e as senhas antigas continuam valendo.

## Perfis

| Perfil | O que acessa |
|---|---|
| Administrador | Tudo, mais cursos, módulos, funcionários, setores, usuários, auditoria e backup |
| Secretaria (funcionário) | Alunos, professores, turmas, matrículas, financeiro, cronograma, salas, relatórios |
| Professor | Só as próprias turmas: chamada, notas e observações dos seus alunos |
| Aluno | Só a própria ficha: turmas, frequência, boletim e parcelas |

Contas são criadas junto com o cadastro da pessoa, com senha provisória mostrada uma única vez.

## Configuração (variáveis de ambiente, todas opcionais)

| Variável | Para quê | Padrão |
|---|---|---|
| `NOME_ESCOLA` | Nome exibido no sistema | Gestão Escolar |
| `DADOS_DIR` | Pasta do banco, anexos e chave | `./dados` |
| `PORT` | Porta | 5000 |
| `ADMIN_EMAIL` / `ADMIN_SENHA` | Administrador criado no primeiro uso | admin@escola.com / senha aleatória |
| `SECRET_KEY` | Chave das sessões | gerada e salva em `dados/secret_key` |
| `AUTOCADASTRO=1` | Libera a tela pública "Criar conta de aluno" | desligado |

Média de aprovação (6,0) e frequência mínima (75%) ficam em `app.py`.

## Estrutura

```
app.py              cria o app, menu, filtros e páginas de erro
db.py               schema, conexão por requisição e migrações
auth.py             senhas, login, perfis, CSRF e auditoria
rotas/
  cadastros.py      CRUD genérico: cada cadastro é uma configuração (alunos, turmas, cursos…)
  alunos.py         ficha do aluno, situação, observações e anexos
  turmas.py         diário: chamada e notas
  comercial.py      matrículas, parcelas, recebimentos e estornos
  relatorios.py     relatórios em tela, impressão e CSV
  admin.py          usuários, auditoria e backup
  conta.py          login, troca de senha, autocadastro
  painel.py         painel inicial por perfil
templates/  static/ telas e um único CSS/JS
seed.py             dados de demonstração
tests/              testes de ponta a ponta (python -m pytest -q)
```

Para criar um cadastro novo, acrescente uma entrada em `CADASTROS` (`rotas/cadastros.py`) e um
item em `MENU` (`app.py`) — listagem, busca, formulário e validação vêm prontos.

## Segurança e dados

- Senhas com hash (scrypt); bloqueio após 5 tentativas erradas de login.
- Proteção CSRF em todos os formulários; cada perfil só enxerga o que lhe cabe.
- Anexos são guardados com nome aleatório, fora da pasta pública, e só a secretaria baixa.
- A pasta `dados/` (banco + anexos) contém dados pessoais: **não envie para o GitHub**
  (já está no `.gitignore`) e faça backup dela. Em *Relatórios* o administrador baixa uma cópia do banco.
- Em produção, publique atrás de HTTPS (proxy reverso).
