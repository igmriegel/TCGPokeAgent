# Handoff de implementação

## Decisões fechadas

- SDK inicial `kaggle-environments==1.14.10`;
- deck único do `cabt.first_agent`;
- entrada `Observation`, saída `list[int]`;
- unidade de decisão `Selection`;
- `GameState` factual separado de `BeliefState`;
- fallback determinístico total;
- heurística antes de busca/modelos;
- busca top 3, profundidade 4, 100 ms, corte em 30 s;
- smoke 20 e full >= 200, ambos os lados;
- zero `INVALID`, `ERROR`, `TIMEOUT`;
- pacote revalidado após extração.

Nenhum desses pontos requer nova decisão arquitetural para iniciar o MVP.

## Primeira entrega do engenheiro

Entregar F0 e F1 de [`11_implementation_order.md`](11_implementation_order.md), incluindo:

- ambiente reproduzível;
- deck validado;
- wrapper e pacote mínimo;
- tipos `Selection`, `GameState` e candidatos;
- parser com fixtures;
- fallback de todos os contextos observados;
- smoke de 20 partidas e relatório.

## Evidência exigida no PR

- testes e comando executado;
- versão do SDK;
- hash do deck;
- resultados por lado;
- contagens de falha;
- exemplo de seleção múltipla;
- pacote extraído e testado;
- atualização de `strategy_notes.md` quando houver afirmação experimental.

## Dados disponíveis

Os oito datasets das duas trilhas estão em `data/raw/kaggle/`, com SHA-256, schema e proveniência no manifesto. Não há bloqueio de autenticação pendente para iniciar o inventário ou a implementação.

## Regra de mudança

Mudança de comportamento atualiza código, teste, config, manifesto do experimento, relatório e Strategy. Mudança de contrato externo exige fonte oficial e data. Uma versão só substitui a estável após gate completo e rollback preservado.

## Aceite

O handoff está completo quando a primeira entrega passa todos os itens “MVP integrado” de [`19_final_harness_checklist.md`](19_final_harness_checklist.md). A submissão só está completa quando também passa o bloco “Submissão aprovada”.
