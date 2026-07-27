# Visão do produto

## Resultado esperado

Entregar um agente reproduzível que:

- sempre devolva uma `Selection` legal no formato `list[int]`;
- jogue com um deck fixo de 60 cartas validado pelo SDK;
- use heurística explícita como caminho seguro;
- aplique busca curta apenas quando houver benefício e orçamento;
- produza evidência suficiente para promoção técnica e para o writeup Strategy.

## Escopo do MVP

O MVP usa `kaggle-environments==1.14.10`, o deck do agente oficial `cabt.first_agent`, uma política heurística e busca de até 100 ms em decisões `MAIN`. Suporte multi-deck, otimização do deck, treinamento e modelos aprendidos ficam depois do primeiro pacote válido.

## Definição de submetível

Um candidato é submetível quando:

- passa 20 partidas de smoke e pelo menos 200 do gate completo;
- joga nos dois lados contra `random`, `first`, heurística sem busca e self-play;
- registra zero `INVALID`, `ERROR` e `TIMEOUT`;
- cumpre formato, tamanho e imports do pacote;
- mantém fallback determinístico para cada `SelectContext`;
- é revalidado após extração do `.tar.gz`.

## Não objetivos desta revisão

Esta etapa não implementa módulos Python, não altera YAML executável e não treina modelos. A única exceção posterior autorizada pelo usuário é o armazenamento dos datasets oficiais em `data/raw/kaggle/`, atualmente bloqueado até o aceite das regras das competições.

## Fontes de verdade

1. API oficial do `cabt` para tipos e Search API.
2. `cabt.json` para orçamento e forma da ação.
3. página da competição para SDK e pacote.
4. estes documentos para arquitetura, gates e operação.
5. código implementado, quando existir, acompanhado de teste que demonstre conformidade.
