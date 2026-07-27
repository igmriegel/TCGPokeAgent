# Pokémon TCG Engine para Kaggle

Plano executável, em português, para construir, medir e submeter um agente ao **PTCG AI Battle Challenge**. Identificadores da API e do código permanecem em inglês.

## Objetivo

O projeto evolui em três trilhas inseparáveis:

1. **MVP submetível:** deck fixo, integração real com `cabt`, heurísticas explícitas, busca curta e fallback determinístico.
2. **Melhoria contínua:** promoção por métricas para rankers supervisionados, self-play, RL e busca sob informação imperfeita.
3. **Strategy:** hipótese, ablação, resultado e evidência rastreável desde a primeira versão.

Esta revisão define a implementação; os módulos Python e os YAML existentes ainda não implementam esses contratos.

## Contrato externo

- Compatibilidade inicial: `kaggle-environments==1.14.10`.
- Entrada: `Observation(current, logs, select, search_begin_input)`.
- Saída em jogo: `list[int]` com índices das opções legais.
- Saída inicial: conteúdo do deck quando `select is None`.
- Submissão: `.tar.gz` com `main.py` e `deck.csv` na raiz, imports válidos a partir de `/kaggle_simulations/agent/` e tamanho máximo de 197,7 MiB.
- Orçamento publicado: `actTimeout=0` e `remainingOverageTime=600`.

Fontes verificadas em **2026-07-27**: [competição Simulation](https://www.kaggle.com/competitions/pokemon-tcg-ai-battle/overview/description), [API do `cabt`](https://matsuoinstitute.github.io/cabt/api.html) e [especificação do ambiente](https://raw.githubusercontent.com/Kaggle/kaggle-environments/master/kaggle_environments/envs/cabt/cabt.json).

## Ordem de implementação

1. Preparar SDK, deck oficial e wrapper mínimo.
2. Preservar `Observation` bruta e normalizar estado/opções.
3. Gerar toda `Selection` válida, inclusive vazia ou múltipla.
4. Implementar fallback por `SelectContext`.
5. Implementar `HeuristicScorer`.
6. Construir runner, métricas e smoke test de 20 partidas.
7. Adicionar `BeliefBuilder`, `StateEvaluator` e `ShortSearch`.
8. Executar gate completo de pelo menos 200 partidas.
9. Empacotar, extrair em diretório temporário e repetir a validação somente com o pacote.

Comece pelo [índice canônico](docs/20_master_index.md) e siga a [ordem vertical do MVP](docs/11_implementation_order.md).

## Estrutura

- `docs/`: contratos, gates, roadmap e registro Strategy.
- `src/`: namespaces reservados para implementação.
- `configs/`: perfis existentes; o contrato futuro está em `docs/22_config_spec.md`.
- `scripts/`: comandos que serão implementados conforme `docs/23_scripts_spec.md`.
- `data/raw/kaggle/`: destino autorizado para downloads oficiais, separado por competição.
- `notebooks/`: exploração; nunca fonte única de uma decisão.

## Ferramentas de qualidade

O projeto usa `ruff` para formatação e lint, `mypy` para checagem de tipos e
`pre-commit` para garantir que tudo seja executado antes de cada commit.

### Configuração inicial

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pre-commit ruff mypy
pre-commit install
```

### Execução manual

```bash
# Formatar todo o código
ruff format .

# Lint (verificar e corrigir automaticamente)
ruff check --fix .

# Checagem de tipos (apenas src/)
mypy --config-file=pyproject.toml src/

# Rodar todos os hooks do pre-commit sem commit
pre-commit run --all-files

# Rodar um hook específico
pre-commit run ruff-format --all-files

# Rodar testes
pytest tests/ -v
```

### Pré-commit (automático)

Com `pre-commit install` executado, a cada `git commit` os hooks rodam
automaticamente:

1. `ruff-format` — formata o código (equivalente ao Black).
2. `ruff` — lint com auto-fix (regras E, F, I, N, W).
3. `mypy` — checagem de tipos no diretório `src/`.

Se algum hook falhar, o commit é bloqueado. Corrija os apontamentos e tente
novamente.

## Dados

Os datasets oficiais das competições Kaggle ficam em `data/raw/kaggle/`:

```
data/raw/kaggle/
├── manifest.json            # Metadados, SHA-256 e proveniência
├── simulation/              # pokemon-tcg-ai-battle
│   ├── Card_ID List_EN.pdf  (137 MB)
│   ├── Card_ID List_JP.pdf  (182 MB)
│   ├── EN_Card_Data.csv     (359 KB, 2022 registros)
│   └── JP_Card_Data.csv     (442 KB, 2022 registros)
├── strategy/                # pokemon-tcg-ai-battle-challenge-strategy
│   └── (mesmos 4 arquivos, byte-idênticos)
└── samples/                 # Amostras sanitizadas dos CSVs
```

O diretório `data/raw/` está no `.gitignore` — os dados não são versionados.

### Setup da API Kaggle

```bash
cp kaggle.json.example ~/.kaggle/kaggle.json
# Editar ~/.kaggle/kaggle.json com username e key de
# https://www.kaggle.com/settings -> API -> Create New Token
chmod 600 ~/.kaggle/kaggle.json
```

### Download dos dados

```bash
# Verificar se os dados existem (exit 0 = OK)
python -m src.data.downloader --check

# Baixar dados (lazy — só baixa o que estiver faltando)
python -m src.data.downloader

# Apenas uma competição
python -m src.data.downloader --competition simulation

# Usando o script wrapper
scripts/download_data.sh
scripts/download_data.sh --check
```

## Estado dos dados Kaggle

Os quatro datasets oficiais de cada competição foram baixados em 2026-07-27 para `data/raw/kaggle/`. Tamanho, SHA-256, formato, esquema dos CSVs e amostras sanitizadas estão registrados no [`manifest.json`](data/raw/kaggle/manifest.json) e no [catálogo de dados](docs/21_persistence_contracts.md).
