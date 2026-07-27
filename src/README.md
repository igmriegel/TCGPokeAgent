# Layout de implementação

Namespaces reservados, na ordem vertical do MVP:

- `core/`: `Selection`, estado factual, crença, parser e interfaces.
- `agents/`: fallback, heurística, busca curta e wrapper.
- `eval/`: runner, validação, métricas, comparação e reporting.
- `experiments/`: specs, execução, grids e registry.
- `logs/`: traces brutos.
- `reports/`: resumos calculados.
- `data/`: datasets derivados; dados oficiais brutos ficam em `data/raw/`.
- `artifacts/`: modelos e pacotes congelados.

Os módulos atuais são placeholders. Implemente conforme [`docs/11_implementation_order.md`](../docs/11_implementation_order.md), sem tratar o código existente como contrato.
