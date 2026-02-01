# probrain-grimorio-backend-devops

![CI](../../actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Desafio Backend — Sistema de magias (D&D 5e) com **validação (Pydantic)**, **camadas (controller/service/repository)**, persistência simulada (**Fake DB + seed**), **cache TTL**, **rate limit**, **auth fake (Cognito-like)**, **observabilidade (request_id + instrumentação)** e **testes (pytest)** com **CI (GitHub Actions)**.

> Nota: o desafio pede funções com comportamento HTTP-like, por isso não subi FastAPI/Flask.  
> A separação controller/service/repository facilita migrar para FastAPI depois, se necessário.

---

## Sumário
- [Objetivo do desafio](#-objetivo-do-desafio)
- [Sessões do Colab](#-sessões-do-colab)
- [DevOps Checklist](#-devops-checklist-para-produção)
- [Arquitetura](#-arquitetura-limpa--fácil-manutenção)
- [Estrutura do projeto](#-estrutura-do-projeto)
- [Como rodar local](#-como-rodar-local-windows-cmd)
- [Endpoints simulados](#-endpoints-simulados)
- [Exemplos de uso](#-exemplos-de-uso)
- [Testes (QA)](#-testes-qa)
- [CI (GitHub Actions)](#-ci-github-actions)
- [Segurança (auth fake)](#-segurança-auth-fake)
- [Observabilidade](#-observabilidade)
- [Custo e escalabilidade](#-custo-e-escalabilidade-cloud-friendly)
- [Entrega (Colab)](#-entrega-colab)

---

## ✅ Objetivo do desafio
Construir uma “API” simulada por funções (sem subir servidor) para gerenciar magias e regras complexas:

- **Create**: criar magia (campos dinâmicos; ex.: custo obrigatório quando material aplicável)
- **Read**: buscar por nome, escola e/ou nível
- **Update**: atualizar magia existente
- **Delete**: remover magia
- **Regra extra**: `calcular_dano_escala(id_magia, nivel_slot)` para magias de ataque com progressão

---

## 📓 Sessões do Colab
O notebook deve ser executável de forma sequencial e organizado em 3 sessões obrigatórias:

1) **Sessão 1 — Setup e Infraestrutura**
   - Imports e inicialização
   - Fake DB + Seed (3 magias complexas)
   - Validação com modelos (Pydantic)

2) **Sessão 2 — API do Grimório (Lógica de Negócio)**
   - Funções estilo endpoint (inputs/outputs/status)
   - CRUD + regra `calcular_dano_escala`

3) **Sessão 3 — QA**
   - Testes com `pytest`
   - Casos de borda e rotas de erro/sucesso

---

## ✅ DevOps Checklist (para produção)
- [x] **CI automatizado** (GitHub Actions) executando testes
- [x] **Reprodutibilidade local** (venv + requirements + install -e)
- [x] **Observabilidade mínima** (request_id + instrumentação)
- [x] **Proteção de custo/abuso** (rate limit + cache TTL)
- [x] **Código modular** (separação controller/service/repository/models)
- [x] **Testes** para fluxos de sucesso e erro (pytest)

---

## 🧱 Arquitetura limpa / fácil manutenção
Separação por responsabilidade para facilitar manutenção e evolução:

- `controller.py` → comportamento HTTP-like (entrada/saída, status, padronização de responses)
- `service.py` → regras de negócio e validações de fluxo
- `repository.py` → persistência simulada (Fake DB)
- `models.py` → modelos Pydantic (integridade e campos dinâmicos)
- `seed.py` → dados iniciais (ex.: Bola de Fogo, Revivificar, Desejo)
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
