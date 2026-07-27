# Contrato de configuração

## Schema canônico

```yaml
project:
  name: pokemon_tcg_engine_kaggle
  sdk_version: "1.14.10"
  seed: 0
agent:
  kind: heuristic
  version: dev
  deck: deck.csv
  fallback: deterministic
heuristic:
  weights: {}
  rules: {}
search:
  enabled: false
  top_k: 3
  max_depth: 4
  max_decision_ms: 100
  disable_below_overage_s: 30
  manual_coin: false
  opponent_deck_version: null
evaluation:
  profile: smoke
  games: 20
  seeds: []
  opponents: [random, first, heuristic, self]
  both_sides: true
outputs:
  root: runs
  decisions: true
  replays: true
```

## Validação

- campos desconhecidos: erro;
- campo obrigatório ausente: erro;
- `games < 20` no smoke ou `< 200` no full: erro;
- `both_sides != true`: erro nos gates;
- busca com limites diferentes do MVP: exige `experiment_id`;
- `manual_coin != false`: proibido no runtime competitivo;
- deck/oponente sem versão/hash no freeze: erro.

## Camadas

1. `default.yaml`;
2. perfil do agente;
3. perfil de avaliação;
4. overrides CLI.

Merge de mappings é profundo; listas são substituídas integralmente. Nenhum valor vem de estado global oculto. O manifesto grava configuração resolvida e lista de overrides.

## Migração dos arquivos atuais

- `agent_baseline.yaml`: renomear conceitualmente para fallback/first apenas na implementação.
- `agent_heuristic.yaml`: pesos e flags M1.
- `agent_hybrid.yaml`: reservar para modelos M2+; busca curta não torna o agente “híbrido”.
- `eval_small.yaml`: exatamente 20 partidas.
- `eval_full.yaml`: pelo menos 200.

Os YAML existentes permanecem inalterados nesta revisão documental e não devem ser tratados como executáveis até passarem pelo schema.
