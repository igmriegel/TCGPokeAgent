# Roadmap do MVP à pesquisa

| Marco | Entrega | Gate |
|---|---|---|
| M0 | SDK 1.14.10, deck oficial, wrapper, parser e fallback | smoke de 20; zero falhas |
| M1 | heurísticas configuráveis e ablações por regra | ganho reproduzível sem novas falhas |
| M2 | ranker linear NumPy | supera heurística em holdout temporal e partidas pareadas |
| M3 | LightGBM LambdaRank | ganho local, SHAP/ablação e pacote compatível |
| M4 | MLP pequeno em NumPy, se LightGBM for inseguro | preserva pelo menos 95% do ganho do ranker |
| M5 | PPO com action masking e curriculum | supera pool fixo e versão anterior com confiança |
| M6 | GRU-PPO ou belief model | ganho em matchups de informação oculta |
| M7 | ISMCTS/PUCT com múltiplas determinizações | ganho justifica CPU e latência |
| M8 | otimização conjunta de deck, política e priors | robustez contra pool diverso e meta do ladder |

## Sequência obrigatória

Nenhum marco pula o anterior como baseline comparável. Cada promoção preserva rollback para a melhor versão estável e registra hipótese, ablação, deck, modelo e relatório.

## Abordagens adiadas

- LLM no runtime: tamanho, latência e não determinismo não resolvem uma necessidade textual.
- DQN tabular inicial: opções variáveis e combinações tornam a representação frágil.
- MCTS completo inicial: informação oculta exige antes uma crença e um avaliador validados.
