# Contratos dos agentes

## `AgentPolicy`

Todos os agentes expõem apenas:

```python
select(observation: Observation) -> list[int]
```

O resultado é validado antes de sair do wrapper. Configuração, estado histórico e logs são dependências internas; não mudam o contrato.

## `FallbackPolicy`

Política determinística e total:

1. gera todas as `Selection` válidas;
2. despacha pela dupla `SelectContext`/`SelectType`;
3. usa regra especializada quando existir;
4. caso contrário escolhe por segurança e índice lexicográfico;
5. devolve `[]` somente quando `minCount == 0` e a regra considerar não selecionar seguro; se uma escolha for obrigatória, devolve a combinação válida de menores índices.

O fallback cobre setup, primeiro jogador, mulligan, ativo/banco, alvos, descarte, energia, ataques, contagens, condições especiais e `YES_NO`.

## `HeuristicPolicy`

Ordena seleções por soma explicável:

1. vitória imediata;
2. ataque eficiente;
3. evolução útil;
4. energia que habilita ataque;
5. desenvolvimento do banco;
6. compra e busca;
7. preservação de recursos;
8. encerramento do turno.

Penaliza energia desperdiçada, descarte de peça-chave, evolução sem benefício, banco bloqueado e encerramento prematuro. Cada componente emite uma razão auditável. Empate: `Selection.indices`.

## `SearchPolicy`

Decora a heurística; não a substitui. Só abre quando:

- `SelectType.MAIN`;
- mais de uma seleção válida;
- pelo menos dois candidatos relevantes;
- `remainingOverageTime >= 30`;
- crença consistente e `search_begin_input` disponível.

Reavalia no máximo top 3, profundidade de até 4 seleções e 100 ms totais. Qualquer erro devolve imediatamente o top-1 heurístico.

## `main.py`

Wrapper fino:

- ramo inicial retorna o deck;
- demais ramos delegam a uma instância persistente da política;
- resolve imports no diretório da submissão;
- nunca contém heurísticas duplicadas;
- em exceção, registra erro e retorna fallback já validado.

O pacote pode desligar busca por configuração sem mudar política ou wrapper.
