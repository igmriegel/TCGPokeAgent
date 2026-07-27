# Critérios objetivos de prontidão

## Documentação pronta

- [x] contrato usa `Observation` e `list[int]`;
- [x] `Selection` cobre zero, uma e múltiplas opções;
- [x] `SelectType`, `SelectContext` e `OptionType` têm papel definido;
- [x] `GameState` contém fatos e `BeliefState` contém hipóteses;
- [x] interfaces de parser, scorer, crença, busca e avaliação são independentes;
- [x] gates de smoke, full, busca e pacote são mensuráveis;
- [x] roadmap e trilha Strategy têm critérios de promoção;
- [x] fontes externas têm data de verificação;
- [x] downloads Kaggle têm hash, formato, schema local e amostras sanitizadas.

## MVP integrado

- [ ] SDK 1.14.10 instalado em ambiente isolado;
- [ ] deck oficial de 60 cartas validado;
- [ ] wrapper inicial e ramo de jogo passam;
- [ ] fallback cobre todos os contextos observados;
- [ ] smoke 20/20 sem falhas;
- [ ] relatório full com >= 200 partidas;
- [ ] ambos os lados e quatro oponentes;
- [ ] métricas e Wilson completos.

## Busca aprovada

- [ ] somente `MAIN`, mais de um candidato e overage >= 30 s;
- [ ] top 3, profundidade <= 4, <= 100 ms;
- [ ] determinização consistente;
- [ ] estados liberados e `search_end` garantido;
- [ ] falhas caem para heurística;
- [ ] vitória não cai contra heurística pura.

## Submissão aprovada

- [ ] `main.py` e `deck.csv` na raiz;
- [ ] imports funcionam em `/kaggle_simulations/agent/`;
- [ ] tamanho < 197,7 MiB;
- [ ] tar sem path traversal;
- [ ] smoke passa usando somente conteúdo extraído;
- [ ] hashes e manifesto congelados;
- [ ] evidência Strategy vinculada.

Prontidão exige todos os itens do bloco correspondente; porcentagem parcial não substitui gate.
