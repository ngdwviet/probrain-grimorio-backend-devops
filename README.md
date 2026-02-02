# probrain-grimorio-backend-devops

![CI](../../actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Desafio Backend — Sistema de magias (D&D 5e) com **validação (Pydantic)**, **camadas (controller/service/repository)**, persistência simulada (**Fake DB + seed**), **cache TTL**, **rate limit**, **auth fake (Cognito-like)**, **observabilidade (request_id + instrumentação)** e **testes (pytest)** com **CI (GitHub Actions)**.

> **Nota:** o desafio pede funções com comportamento **HTTP-like**, por isso não subi FastAPI/Flask.  
> A separação `controller/service/repository` facilita migrar para FastAPI depois, se necessário.

---

## Sumário
- [✅ Objetivo do desafio](#-objetivo-do-desafio)
- [📓 Sessões do Colab](#-sessões-do-colab)
- [✅ DevOps Checklist](#-devops-checklist-para-produção)
- [🧱 Arquitetura](#-arquitetura-limpa--fácil-manutenção)
- [📁 Estrutura do projeto](#-estrutura-do-projeto)
- [🏁 Como rodar local](#-como-rodar-local-windows-cmd)
- [🧭 Endpoints simulados](#-endpoints-simulados)
- [🧙 Exemplos de uso](#-exemplos-de-uso)
- [🧪 Testes (QA)](#-testes-qa)
- [🔁 CI (GitHub Actions)](#-ci-github-actions)
- [🔐 Segurança (auth fake)](#-segurança-auth-fake)
- [📈 Observabilidade](#-observabilidade)
- [💰 Custo e escalabilidade](#-custo-e-escalabilidade-cloud-friendly)
- [📦 Entrega (Colab)](#-entrega-colab)

---

## ✅ Objetivo do desafio
Construir uma “API” simulada por **funções** (sem subir servidor) para gerenciar magias e regras complexas:

- **Create**: criar magia (campos dinâmicos; ex.: custo obrigatório quando material aplicável)
- **Read**: buscar por nome, escola e/ou nível
- **Update**: atualizar magia existente
- **Delete**: remover magia
- **Regra extra**: `calcular_dano_escala(id_magia, nivel_slot)` para magias de ataque com progressão

---

## 📓 Sessões do Colab
O notebook deve ser executável de forma sequencial e organizado em **3 sessões obrigatórias**:

### 1) Sessão 1 — Setup e Infraestrutura
- Imports e inicialização
- Fake DB + Seed (**3 magias complexas**)
- Validação com modelos (**Pydantic**)

### 2) Sessão 2 — API do Grimório (Lógica de Negócio)
- Funções estilo endpoint (**inputs/outputs/status**)
- CRUD + regra `calcular_dano_escala`

### 3) Sessão 3 — QA
- Testes com `pytest`
- Casos de borda e rotas de erro/sucesso

---

## ✅ DevOps Checklist (para produção)
✅ **CI automatizado** (GitHub Actions) executando testes  
✅ **Reprodutibilidade local** (venv + requirements + install -e)  
✅ **Observabilidade mínima** (request_id + instrumentação)  
✅ **Proteção de custo/abuso** (rate limit + cache TTL)  
✅ **Código modular** (separação controller/service/repository/models)  
✅ **Testes** para fluxos de sucesso e erro (pytest)

---

## 🧱 Arquitetura limpa / fácil manutenção
Separação por responsabilidade para facilitar manutenção e evolução:

- `controller.py` → comportamento HTTP-like (entrada/saída, status, padronização de responses)
- `service.py` → regras de negócio e validações de fluxo
- `repository.py` → persistência simulada (**Fake DB**)
- `models.py` → modelos Pydantic (integridade e campos dinâmicos)
- `seed.py` → dados iniciais (ex.: **Bola de Fogo**, **Revivificar**, **Desejo**)
- `cache.py` → cache TTL + rate limit (proteção contra abuso/custo)
- `auth.py` → autenticação fake (Cognito-like) + RBAC
- `observability.py` → instrumentação e request_id

---

## 📁 Estrutura do projeto
```text
.
├─ src/
│  └─ probrain_grimorio/
│     ├─ __init__.py
│     ├─ auth.py
│     ├─ cache.py
│     ├─ controller.py
│     ├─ models.py
│     ├─ observability.py
│     ├─ repository.py
│     ├─ seed.py
│     └─ service.py
├─ tests/
├─ notebook/
├─ pyproject.toml
├─ requirements.txt
└─ .github/workflows/ci.yml
```

---

## 🏁 Como rodar local (Windows CMD)

**1) Ir para a raiz do projeto**
```bat
cd C:\Users\Alber\Documents\Projetos\probrain-grimorio-backend-devops
```

**2) Ativar o virtualenv**
```bat
.venv\Scripts\activate
```

**3) Instalar dependências**
```bat
pip install -r requirements.txt
pip install -e .
```

**4) Rodar testes**
```bat
pytest -q
```

---

## 🧭 Endpoints simulados

| Ação | Função (controller) | Status esperados |
|---|---|---|
| Create | `create_magia_controller` | `201 / 400 / 401 / 403 / 429` |
| Read | `read_magias_controller` | `200 / 400 / 404 / 429` |
| Update | `update_magia_controller` | `200 / 400 / 401 / 403 / 404 / 429` |
| Delete | `delete_magia_controller` | `200 / 401 / 403 / 404 / 429` |
| Dano escala | `calcular_dano_escala_controller` | `200 / 400 / 404 / 429` |

> Observação: `429` pode ocorrer por **rate limit**.

---

## 🧙 Exemplos de uso

### Read (listar/buscar)
```python
from probrain_grimorio.controller import read_magias_controller

res = read_magias_controller(
    nome=None,
    escola="Evocação",
    nivel=None,
    limit=20,
    offset=0,
    client_id="client-123",
)
print(res)
```

### Create (criar magia)
```python
from probrain_grimorio.controller import create_magia_controller

payload = {
    "nome": "Bola de Fogo",
    "escola": "Evocação",
    "nivel": 3,
    "componentes": {"verbal": True, "somatico": True, "material": True},
    "custo_em_ouro": 0,
    "dano_base": "8d6",
    "dano_por_slot_acima": "1d6",
}

res = create_magia_controller(
    payload=payload,
    authorization="Bearer dev-token-writer",
    client_id="client-123",
)
print(res)
```

### Calcular dano escalável
```python
from probrain_grimorio.controller import calcular_dano_escala_controller

res = calcular_dano_escala_controller(
    id_magia="fireball-id",
    nivel_slot=5,
    client_id="client-123",
)
print(res)
```

---

## 🧪 Testes (QA)
Os testes cobrem:

- fluxos de sucesso (CRUD + dano escalável)
- casos de borda (payload inválido, magia inexistente, permissões)
- rotas principais de sucesso e erro (status codes)

Executar:
```bat
pytest -q
```

---

## 🔁 CI (GitHub Actions)
Pipeline executado a cada **push/PR** para garantir qualidade e evitar regressões:

1) setup do Python  
2) instalação de dependências  
3) execução de `pytest`

Arquivo: `.github/workflows/ci.yml`

---

## 🔐 Segurança (auth fake)
- Rotas de **escrita** (create/update/delete) exigem `writer` ou `admin`
- Tokens são **simulados** para o case (sem dependência externa)
- Objetivo: demonstrar noções de **autenticação/autorização** e **RBAC**

---

## 📈 Observabilidade
- Cada requisição carrega **`request_id`** para rastreabilidade.
- O decorator **`@instrument(...)`** registra eventos/tempo e ajuda no troubleshooting.

### Como seria em Datadog (conceitual)
Este case implementa instrumentação local (logs/métricas simples). Em produção, a adaptação típica seria:

- **Logs estruturados (JSON)** enviados para um agent/collector
- **Métricas** (status codes, latência por endpoint)
- **Correlação** via **`request_id`** (trace/log correlation)

---

## 💰 Custo e escalabilidade (cloud-friendly)
Mesmo sem servidor real no case, existem proteções com foco em operação:

- **Rate limit (60/min)**: evita rajadas e abuso
- **Cache TTL**: reduz recomputação em leituras repetidas

Essas medidas ajudam a **controlar custo** em ambiente cloud e evitar **chamadas desnecessárias**.

---

## 📦 Entrega (Colab)
A entrega oficial do desafio é via **Google Colab**.

- **Link do Colab:** 

### Recomendações para o notebook
No Colab, usar células Markdown para explicar:

- decisões de modelagem (**campos dinâmicos**)
- estratégia de **validação**
- **tratamento de erros**
- como a **arquitetura** facilita manutenção
=======

## Sumário
- [✅ Objetivo do desafio](#-objetivo-do-desafio)
- [📓 Sessões do Colab](#-sessões-do-colab)
- [✅ DevOps Checklist](#-devops-checklist-para-produção)
- [🧱 Arquitetura](#-arquitetura-limpa--fácil-manutenção)
- [📁 Estrutura do projeto](#-estrutura-do-projeto)
- [🏁 Como rodar local](#-como-rodar-local-windows-cmd)
- [🧭 Endpoints simulados](#-endpoints-simulados)
- [🧙 Exemplos de uso](#-exemplos-de-uso)
- [🧪 Testes (QA)](#-testes-qa)
- [🔁 CI (GitHub Actions)](#-ci-github-actions)
- [🔐 Segurança (auth fake)](#-segurança-auth-fake)
- [📈 Observabilidade](#-observabilidade)
- [💰 Custo e escalabilidade](#-custo-e-escalabilidade-cloud-friendly)
- [📦 Entrega (Colab)](#-entrega-colab)

---

## ✅ Objetivo do desafio
Construir uma “API” simulada por **funções** (sem subir servidor) para gerenciar magias e regras complexas:

- **Create**: criar magia (campos dinâmicos; ex.: custo obrigatório quando material aplicável)
- **Read**: buscar por nome, escola e/ou nível
- **Update**: atualizar magia existente
- **Delete**: remover magia
- **Regra extra**: `calcular_dano_escala(id_magia, nivel_slot)` para magias de ataque com progressão

---

## 📓 Sessões do Colab
O notebook deve ser executável de forma sequencial e organizado em **3 sessões obrigatórias**:

### 1) Sessão 1 — Setup e Infraestrutura
- Imports e inicialização
- Fake DB + Seed (**3 magias complexas**)
- Validação com modelos (**Pydantic**)

### 2) Sessão 2 — API do Grimório (Lógica de Negócio)
- Funções estilo endpoint (**inputs/outputs/status**)
- CRUD + regra `calcular_dano_escala`

### 3) Sessão 3 — QA
- Testes com `pytest`
- Casos de borda e rotas de erro/sucesso

---

## ✅ DevOps Checklist (para produção)
✅ **CI automatizado** (GitHub Actions) executando testes  
✅ **Reprodutibilidade local** (venv + requirements + install -e)  
✅ **Observabilidade mínima** (request_id + instrumentação)  
✅ **Proteção de custo/abuso** (rate limit + cache TTL)  
✅ **Código modular** (separação controller/service/repository/models)  
✅ **Testes** para fluxos de sucesso e erro (pytest)

---

## 🧱 Arquitetura limpa / fácil manutenção
Separação por responsabilidade para facilitar manutenção e evolução:

- `controller.py` → comportamento HTTP-like (entrada/saída, status, padronização de responses)
- `service.py` → regras de negócio e validações de fluxo
- `repository.py` → persistência simulada (**Fake DB**)
- `models.py` → modelos Pydantic (integridade e campos dinâmicos)
- `seed.py` → dados iniciais (ex.: **Bola de Fogo**, **Revivificar**, **Desejo**)
- `cache.py` → cache TTL + rate limit (proteção contra abuso/custo)
- `auth.py` → autenticação fake (Cognito-like) + RBAC
- `observability.py` → instrumentação e request_id

---

## 📁 Estrutura do projeto
```text
.
├─ src/
│  └─ probrain_grimorio/
│     ├─ __init__.py
│     ├─ auth.py
│     ├─ cache.py
│     ├─ controller.py
│     ├─ models.py
│     ├─ observability.py
│     ├─ repository.py
│     ├─ seed.py
│     └─ service.py
├─ tests/
├─ notebook/
├─ pyproject.toml
├─ requirements.txt
└─ .github/workflows/ci.yml
```

---

## 🏁 Como rodar local (Windows CMD)

**1) Ir para a raiz do projeto**
```bat
cd C:\Users\Alber\Documents\Projetos\probrain-grimorio-backend-devops
```

**2) Ativar o virtualenv**
```bat
.venv\Scripts\activate
```

**3) Instalar dependências**
```bat
pip install -r requirements.txt
pip install -e .
```

**4) Rodar testes**
```bat
pytest -q
```

---

## 🧭 Endpoints simulados

| Ação | Função (controller) | Status esperados |
|---|---|---|
| Create | `create_magia_controller` | `201 / 400 / 401 / 403 / 429` |
| Read | `read_magias_controller` | `200 / 400 / 404 / 429` |
| Update | `update_magia_controller` | `200 / 400 / 401 / 403 / 404 / 429` |
| Delete | `delete_magia_controller` | `200 / 401 / 403 / 404 / 429` |
| Dano escala | `calcular_dano_escala_controller` | `200 / 400 / 404 / 429` |

> Observação: `429` pode ocorrer por **rate limit**.

---

## 🧙 Exemplos de uso

### Read (listar/buscar)
```python
from probrain_grimorio.controller import read_magias_controller

res = read_magias_controller(
    nome=None,
    escola="Evocação",
    nivel=None,
    limit=20,
    offset=0,
    client_id="client-123",
)
print(res)
```

### Create (criar magia)
```python
from probrain_grimorio.controller import create_magia_controller

payload = {
    "nome": "Bola de Fogo",
    "escola": "Evocação",
    "nivel": 3,
    "componentes": {"verbal": True, "somatico": True, "material": True},
    "custo_em_ouro": 0,
    "dano_base": "8d6",
    "dano_por_slot_acima": "1d6",
}

res = create_magia_controller(
    payload=payload,
    authorization="Bearer dev-token-writer",
    client_id="client-123",
)
print(res)
```

### Calcular dano escalável
```python
from probrain_grimorio.controller import calcular_dano_escala_controller

res = calcular_dano_escala_controller(
    id_magia="fireball-id",
    nivel_slot=5,
    client_id="client-123",
)
print(res)
```

---

## 🧪 Testes (QA)
Os testes cobrem:

- fluxos de sucesso (CRUD + dano escalável)
- casos de borda (payload inválido, magia inexistente, permissões)
- rotas principais de sucesso e erro (status codes)

Executar:
```bat
pytest -q
```

---

## 🔁 CI (GitHub Actions)
Pipeline executado a cada **push/PR** para garantir qualidade e evitar regressões:

1) setup do Python  
2) instalação de dependências  
3) execução de `pytest`

Arquivo: `.github/workflows/ci.yml`

---

## 🔐 Segurança (auth fake)
- Rotas de **escrita** (create/update/delete) exigem `writer` ou `admin`
- Tokens são **simulados** para o case (sem dependência externa)
- Objetivo: demonstrar noções de **autenticação/autorização** e **RBAC**

---

## 📈 Observabilidade
- Cada requisição carrega **`request_id`** para rastreabilidade.
- O decorator **`@instrument(...)`** registra eventos/tempo e ajuda no troubleshooting.

### Como seria em Datadog (conceitual)
Este case implementa instrumentação local (logs/métricas simples). Em produção, a adaptação típica seria:

- **Logs estruturados (JSON)** enviados para um agent/collector
- **Métricas** (status codes, latência por endpoint)
- **Correlação** via **`request_id`** (trace/log correlation)

---

## 💰 Custo e escalabilidade (cloud-friendly)
Mesmo sem servidor real no case, existem proteções com foco em operação:

- **Rate limit (60/min)**: evita rajadas e abuso
- **Cache TTL**: reduz recomputação em leituras repetidas

Essas medidas ajudam a **controlar custo** em ambiente cloud e evitar **chamadas desnecessárias**.

---

## 📦 Entrega (Colab)
A entrega oficial do desafio é via **Google Colab**.

- **Link do Colab:** 

### Recomendações para o notebook
No Colab, usar células Markdown para explicar:

- decisões de modelagem (**campos dinâmicos**)
- estratégia de **validação**
- **tratamento de erros**
- como a **arquitetura** facilita manutenção
