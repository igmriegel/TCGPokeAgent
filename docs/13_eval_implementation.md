# Implementação do runner e avaliação

## Camadas

1. `validation.py`: preflight de SDK, deck, agente e pacote.
2. `runner.py`: execução de uma partida e de um lote.
3. `metrics.py`: agregação sem I/O.
4. `comparison.py`: comparação pareada e gates.
5. `reporting.py`: serialização dos objetos calculados.

## Preflight

- confirmar versão exata do SDK;
- validar 60 cartas e regras de deck aceitas pelo engine;
- instanciar `cabt` com os agentes oficiais;
- chamar o candidato em fixtures de seleção vazia, simples e múltipla;
- rejeitar saída que não seja `list[int]`;
- confirmar diretórios graváveis de run.

## Execução

Cada partida recebe seed explícita e deadline interno. O runner captura observação, seleção, duração monotônica, saldo de overage, razões do scorer e status retornado pelo ambiente. Uma falha encerra a partida, mas o lote continua para produzir diagnóstico completo.

Ordem dos jogos é predefinida no manifesto. Quando paralelismo for introduzido, o resultado continua ordenado por `match_id`.

## Métricas

Mantenha registros brutos e agregados separados. Calcule percentis a partir das durações brutas, Wilson por matchup e lado, além de contagens de falha. Não arredonde valores no JSON; arredonde apenas a apresentação Markdown/CSV.

## Smoke e full

Smoke: 20 partidas balanceadas, destinado a integração. Full: mínimo 200, com matriz declarada antes do run. Ambos executam os dois lados. Full só começa após smoke verde.

## Validação do pacote

1. listar conteúdo do tar e rejeitar caminhos absolutos ou `..`;
2. extrair em diretório temporário;
3. confirmar `main.py` e `deck.csv` na raiz;
4. medir tamanho;
5. executar smoke com cwd e imports restritos ao conteúdo extraído;
6. calcular SHA-256 do pacote aprovado.

## Testes

- runner reproduz resultado com mesma seed;
- falha de uma partida não apaga anteriores;
- Wilson em casos 0%, 50% e 100%;
- percentis para lote pequeno;
- separação por lado;
- gate falha com uma ocorrência operacional;
- pacote aninhado ou com import externo é rejeitado.
