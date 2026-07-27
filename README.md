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

## Estado dos dados Kaggle

Os quatro datasets oficiais de cada competição foram baixados em 2026-07-27 para `data/raw/kaggle/`. Tamanho, SHA-256, formato, esquema dos CSVs e amostras sanitizadas estão registrados no [`manifest.json`](data/raw/kaggle/manifest.json) e no [catálogo de dados](docs/21_persistence_contracts.md).
