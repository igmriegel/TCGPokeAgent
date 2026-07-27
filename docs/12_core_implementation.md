# Implementação do core

## Arquivos-alvo

| Arquivo | Responsabilidade |
|---|---|
| `src/core/types.py` | aliases, enums de resultado/falha e reexport dos enums `cabt` |
| `src/core/action.py` | `Candidate`, `Selection` e validação |
| `src/core/state.py` | `GameState`, visões de jogador/Pokémon e `BeliefState` |
| `src/core/parser.py` | observação → decisão normalizada |
| `src/core/interfaces.py` | protocolos pequenos e independentes |
| `src/core/catalog.py` | cache de `all_card_data()` e `all_attack()` |

O nome legado `action.py` pode permanecer por compatibilidade de layout, mas não define uma ação singular; seu tipo público é `Selection`.

## Parser

### Entrada

Aceitar a dataclass `Observation` ou payload convertível por `to_observation_class`. Guardar a entrada convertida sem mutação.

### Estado factual

Copiar campos oficiais de `State` e `PlayerState`. Manter `None` para cartas ocultas. Derivar apenas valores matemáticos, como dano atual `maxHp - hp`; não inferir identidade de cartas.

### Candidatos

Enumerar `select.option` com `enumerate`. Resolver metadados por `cardId`, `attackId`, área/índice e cartas visíveis. Campo ausente gera `None`, não valor inventado.

## Geração de `Selection`

1. Produzir combinações de tamanhos `minCount..maxCount`.
2. Para energia, somar `Option.count` e satisfazer `remainEnergyCost`.
3. Para dano, respeitar `remainDamageCounter` e granularidade oferecida.
4. Aplicar restrições específicas documentadas pelo contexto.
5. Validar novamente antes de devolver.
6. Ordenar por tupla de índices.

Não podar por qualidade nessa camada.

## `BeliefBuilder`

Subtrair do deck conhecido as cartas públicas e eventos inequívocos dos logs. Preencher zonas ocultas em ordem estável a partir do multiconjunto restante. Para o adversário, usar deck de referência versionado e remover cartas públicas. Validar que cada lista entregue a `search_begin` tenha exatamente o comprimento exigido.

Se uma subtração resultar negativa, faltar Basic no setup adversário ou uma cardinalidade não fechar, marcar `consistent=False` e não pesquisar.

## Testes obrigatórios

- golden tests de observações reais;
- preservação de índices;
- `minCount=0`;
- seleção múltipla;
- custo de energia com `count`;
- distribuição de dano;
- oponente com `hand=None`;
- cartas `None` em prêmio/ativo;
- crença consistente e inconsistente;
- serialização de snapshots sem transformar crença em fato.
