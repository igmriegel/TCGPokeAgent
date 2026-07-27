# Implementação da heurística e busca curta

## Despacho por contexto

| Grupo | Contextos | Regra inicial |
|---|---|---|
| setup | `SETUP_ACTIVE_POKEMON`, `SETUP_BENCH_POKEMON` | ativo com melhor sobrevivência/ataque cedo; banco útil sem ocupar slots críticos |
| início | `IS_FIRST`, `MULLIGAN` | regra fixa versionada e dependente do deck |
| mobilidade | `SWITCH`, `TO_ACTIVE`, `TO_BENCH`, `TO_FIELD` | preservar atacante e promover melhor estado pós-ação |
| recursos | `TO_HAND`, `TO_DECK`, `TO_DECK_BOTTOM`, `TO_PRIZE`, `NOT_MOVE`, `DISCARD` | valor marginal e raridade da peça |
| alvos | `DAMAGE*`, `HEAL`, `REMOVE_DAMAGE_COUNTER*`, `EFFECT_TARGET` | KO/prêmio, ameaça e eficiência |
| evolução | `EVOLVES_FROM`, `EVOLVES_TO`, `DEVOLVE`, `EVOLVE` | ganho imediato, sobrevivência e ataque habilitado |
| anexos | `ATTACH_*`, `DETACH_FROM`, `DISCARD_*`, `SWITCH_*` | habilitar ataque com menor desperdício |
| skills/ataques | `SKILL_ORDER`, `ATTACK`, `DISABLE_ATTACK` | valor esperado e sequência |
| contagem | `DRAW_COUNT`, `DAMAGE_COUNTER_COUNT`, `REMOVE_DAMAGE_COUNTER_COUNT` | máximo útil sem overpay |
| booleanos | `ACTIVATE`, `FIRST_EFFECT`, `MORE_DEVOLVE`, `COIN_HEAD` | benefício líquido; fallback explícito |
| condição | `AFFECT_SPECIAL_CONDITION`, `RECOVER_SPECIAL_CONDITION` | impacto no alvo e no próximo turno |

Contextos futuros desconhecidos usam fallback de cardinalidade/índice e emitem `unknown_context`.

## Score heurístico

Use soma configurável, com componentes normalizados e razões:

```text
score =
  win_now
  + efficient_attack
  + useful_evolution
  + attack_enabling_energy
  + bench_development
  + draw_search
  + resource_preservation
  + safe_end_turn
  - wasted_energy
  - key_piece_discard
  - pointless_evolution
  - blocked_bench
  - premature_end
```

`win_now` domina qualquer combinação não vencedora. Depois, pesos não substituem regras de legalidade. Ataque eficiente considera dano efetivo, KO, prêmios, fraqueza/resistência observada, custo e exposição no contra-ataque.

## Busca curta

### Determinização

- deck próprio: lista fixa menos cartas conhecidas;
- prêmios próprios: preenchimento estável do restante;
- adversário: deck de referência versionado menos cartas públicas;
- mão, prêmios e ativo oculto: preenchimento determinístico com cardinalidade exata;
- `manual_coin=False`.

### Algoritmo

1. Iniciar relógio monotônico.
2. Verificar gates e construir crença.
3. Chamar `search_begin` com a `Observation` recebida exatamente como veio.
4. Para cada uma das top 3 seleções heurísticas, chamar `search_step`.
5. Continuar por no máximo 4 seleções no ramo, usando heurística para respostas intermediárias.
6. Parar em fim de turno, terminal ou budget.
7. Avaliar folha com `StateEvaluator`.
8. Liberar todo `searchId` intermediário com `search_release`.
9. Executar `search_end()` em `finally`.
10. Escolher maior valor; empate por índice.

### Fallback

`BeliefState` inconsistente, retorno de erro, exceção, estado nulo ou tempo esgotado devolve top-1 heurístico. A falha é contabilizada sem propagar para o runtime.

## `StateEvaluator`

Primeira versão combina diferença de prêmios restantes, ameaça de KO, HP útil, atacantes preparados, energia útil, qualidade do banco, tamanho/qualidade conhecida da mão e risco de deck-out. Features ocultas vêm somente da crença e são identificadas no trace.

## Testes

- empate determinístico;
- vitória imediata supera demais opções;
- `END` prematuro recebe penalidade;
- busca nunca abre fora de `MAIN`;
- top 3 e profundidade 4;
- `search_release` e `search_end` mesmo em exceção;
- corte em 100 ms e abaixo de 30 s;
- falha de busca preserva exatamente a escolha heurística.
