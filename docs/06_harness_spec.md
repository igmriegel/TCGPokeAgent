# Contrato do ambiente e da submissão

Verificado em 2026-07-27 contra a [API do `cabt`](https://matsuoinstitute.github.io/cabt/api.html), o [`cabt.json`](https://raw.githubusercontent.com/Kaggle/kaggle-environments/master/kaggle_environments/envs/cabt/cabt.json) e a [competição](https://www.kaggle.com/competitions/pokemon-tcg-ai-battle/overview/description).

## Entrada do agente

`Observation` contém:

| Campo | Tipo | Contrato |
|---|---|---|
| `current` | `State | None` | `None` somente na seleção inicial do deck |
| `logs` | `list[Log]` | eventos desde a seleção anterior |
| `select` | `SelectData | None` | `None` somente na seleção inicial do deck |
| `search_begin_input` | `str | None` | entrada opaca associada a `search_begin` |

O wrapper converte o payload com `to_observation_class` quando o runtime não entregar a dataclass. Ele preserva a instância bruta recebida para a Search API.

## Saída do agente

Em jogo, `AgentPolicy.select(observation) -> list[int]`. Cada inteiro é a posição original em `observation.select.option`. A lista pode conter zero, um ou vários índices conforme `minCount` e `maxCount`.

Na chamada inicial, `select is None` e `current is None`; `main.py` devolve o deck no formato exigido pelo SDK. Esse ramo não executa parser, heurística ou busca.

## `SelectData`

Campos canônicos:

- `type: SelectType`;
- `context: SelectContext`;
- `minCount`, `maxCount`;
- `remainDamageCounter`, `remainEnergyCost`;
- `option: list[Option]`;
- `deck`, presente ao selecionar dentro do deck;
- `contextCard`, usado no contexto de ativação;
- `effect`, carta cujo efeito está em processamento.

`SelectType` define a família da seleção; `SelectContext` define sua finalidade. A estratégia despacha pela dupla, com prioridade para `SelectContext`.

## `SelectType` e `OptionType`

| `SelectType` | `OptionType` esperado |
|---|---|
| `MAIN` | `PLAY`, `ATTACH`, `EVOLVE`, `ABILITY`, `DISCARD`, `RETREAT`, `ATTACK`, `END` |
| `CARD` | `CARD` |
| `ATTACHED_CARD` | `TOOL_CARD`, `ENERGY_CARD` |
| `CARD_OR_ATTACHED_CARD` | `CARD`, `TOOL_CARD`, `ENERGY_CARD` |
| `ENERGY` | `ENERGY` |
| `SKILL` | `SKILL` |
| `ATTACK` | `ATTACK` |
| `EVOLVE` | `EVOLVE` |
| `COUNT` | `NUMBER` |
| `YES_NO` | `YES`, `NO` |
| `SPECIAL_CONDITION` | `SPECIAL_CONDITION` |

Campos de `Option` são opcionais e interpretados pelo `type`: `number`, `area`, `index`, `playerIndex`, `toolIndex`, `energyIndex`, `count`, `inPlayArea`, `inPlayIndex`, `attackId`, `cardId`, `serial` e `specialConditionType`.

## Orçamento

O ambiente publica `actTimeout=0`, `runTimeout=2000`, `remainingOverageTime=600` e ação como array. O agente não interpreta `actTimeout=0` como tempo infinito: aplica 100 ms como limite interno da busca e preserva margem para parsing/fallback. Busca é desligada abaixo de 30 segundos de `remainingOverageTime`.

## Pacote

- fixar `kaggle-environments==1.14.10` durante o MVP;
- validar o deck de 60 cartas do `cabt.first_agent` no SDK instalado;
- manter `main.py` e `deck.csv` na raiz do `.tar.gz`;
- fazer imports a partir de `/kaggle_simulations/agent/`;
- manter o arquivo abaixo de 197,7 MiB;
- extrair em diretório temporário e testar usando somente o conteúdo extraído.

Diferenças contra a versão mais recente do SDK são inventariadas depois que o MVP 1.14.10 estiver verde; não se atualiza a dependência silenciosamente.
