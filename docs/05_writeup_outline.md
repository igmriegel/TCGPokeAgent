# Estrutura do writeup Strategy

## Seções

1. Problema, informação imperfeita e restrições do runtime.
2. Dados oficiais, externos e gerados; licença, versão e leakage.
3. Deck fixo do MVP e justificativa.
4. Representação factual, `BeliefState` e `Selection`.
5. Heurística, fallback e busca curta.
6. Protocolo pareado, métricas e intervalos.
7. Ablações e evolução M1–M8.
8. Falhas, limites, custo e reprodutibilidade.
9. Conclusão sustentada pelas evidências.

## Evidência mínima

- tabela W/D/L por matchup e lado;
- intervalo de Wilson e tamanho da amostra;
- p50/p95/máxima de decisão;
- ablação de cada grupo de regras;
- cobertura e falhas da busca;
- traces curtos de decisões representativas;
- hashes de deck, configuração, modelo e pacote;
- vínculo de cada afirmação ao `experiment_id`.

## Regra editorial

Uma conclusão entra no writeup apenas se estiver registrada em [`strategy_notes.md`](strategy_notes.md) com artefato verificável. Correlação é descrita como correlação; inferência causal exige ablação controlada.
