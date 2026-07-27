# Protocolo experimental

## Unidade de mudança

Toda alteração começa com uma hipótese falsificável e termina com `promote`, `iterate` ou `reject`. O registro inclui versão do agente, versão do deck, hash do modelo quando houver, configuração efetiva, seeds, oponentes e artefatos.

## Comparação pareada

- Congele o pool de oponentes.
- Use as mesmas seeds para candidato e referência.
- Rode ambos como jogador 0 e jogador 1.
- Mantenha o deck constante, salvo experimento explicitamente identificado como deck.
- Compare primeiro com a melhor versão estável; compare também com a ablação direta.
- Não misture resultados de SDKs ou esquemas de features diferentes.

## Estágios

### Smoke

Execute 20 partidas distribuídas nos dois lados. O único gate é operacional: zero `INVALID`, `ERROR` e `TIMEOUT`, relatórios completos e decisões dentro do orçamento.

### Full

Execute pelo menos 200 partidas, balanceadas por lado e matchup. Reporte W/D/L, Wilson, duração e falhas. Amostras maiores são obrigatórias quando o intervalo não sustenta a decisão.

### Candidate

Repita o full contra `random`, `first`, versão estável e ablação relevante. Congele o pacote e execute a validação pós-extração.

## Regras de promoção

- Heurística: promove somente com ganho reproduzível no matchup alvo e nenhuma regressão operacional.
- Busca: promove somente se não reduzir a taxa de vitória contra heurística pura e respeitar latência/falhas.
- Modelo: promove somente após holdout temporal, partidas pareadas e ablação.
- Resultado inconclusivo gera mais partidas ou hipótese revisada; nunca promoção por inspeção visual.

## Leakage

Separe treino, validação e teste por tempo de geração do trace. Replays da mesma partida e estados derivados não cruzam partições. Logs de ladder não entram no treino antes de receber versão, origem e regra de uso.
