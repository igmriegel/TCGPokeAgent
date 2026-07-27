# Ordem vertical de implementação do MVP

Cada fatia termina em teste executável; não se constroem todas as abstrações antes da primeira partida.

## F0 — ambiente e pacote mínimo

1. Criar ambiente isolado e instalar `kaggle-environments==1.14.10`.
2. Localizar `cabt.first_agent`, copiar seu deck de 60 cartas e validá-lo pelo SDK.
3. Criar `main.py` fino e `deck.csv`.
4. Rodar `first` versus `random` nos dois lados.
5. Empacotar, extrair e repetir o teste a partir do conteúdo extraído.

Gate: pacote estruturalmente válido, imports portáveis e zero falhas.

## F1 — parser, candidatos e fallback

1. Modelar enums oficiais e `Selection`.
2. Preservar `Observation` bruta.
3. Mapear `State` para `GameState` factual.
4. Converter `Option` em `Candidate` sem renumerar.
5. Gerar seleções de cardinalidade zero, simples e múltipla.
6. Implementar fallback total por contexto.
7. Executar smoke de 20 partidas.

Gate: todas as decisões legais; zero `INVALID`, `ERROR` e `TIMEOUT`.

## F2 — heurística mensurável

1. Implementar catálogo de cartas/ataques do SDK.
2. Criar features de estado e seleção.
3. Implementar regras positivas, penalidades e razões.
4. Instrumentar duração e decisão.
5. Comparar contra `random`, `first` e ablações.

Gate: melhora reproduzível, sem regressão operacional.

## F3 — harness experimental

1. Persistir manifesto, partidas e decisões.
2. Agregar W/D/L, Wilson, lados e duração.
3. Produzir comparação pareada.
4. Executar full de pelo menos 200 partidas.

Gate: relatório completo reproduzível pela configuração e seeds.

## F4 — crença e busca curta

1. Construir `BeliefBuilder` determinístico.
2. Validar cardinalidade das zonas ocultas.
3. Implementar `StateEvaluator`.
4. Integrar Search API com liberação de estados e `search_end` em `finally`.
5. Medir cobertura, falhas e ganho sobre heurística pura.

Gate: busca não reduz vitória, não viola 100 ms e não produz falha operacional.

## F5 — candidato submetível

1. Congelar deck, código, configuração e versões.
2. Rodar matriz final nos dois lados.
3. Gerar `.tar.gz` abaixo de 197,7 MiB.
4. Extrair em diretório limpo e executar somente o conteúdo do pacote.
5. Registrar hashes e evidências Strategy.

Gate: todos os itens de [`24_handoff_spec.md`](24_handoff_spec.md).
