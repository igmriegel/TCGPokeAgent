# Catálogo de dados e proveniência

Verificação externa: **2026-07-27**.

## Estados

- `verificada`: conteúdo ou metadado observado diretamente na fonte.
- `derivável`: produzido de fonte verificada por transformação documentada.
- `pendente`: metadado ou conteúdo ainda não inspecionado.
- `externa`: fonte fora das duas competições/SDK, mantida separada.

## Fontes de runtime e SDK

| Fonte | Conteúdo | Uso | Status |
|---|---|---|---|
| `all_card_data()` | ID, nome, tipo, HP, estágio, fraqueza, resistência, recuo, skills, ataques | catálogo e features | verificada na documentação da API |
| `all_attack()` | ID, nome, texto, dano, energias | scoring de ataque | verificada na documentação da API |
| `Observation.current` | estado factual visível | parser/evaluator | verificada |
| `Observation.select` | contexto, opções e cardinalidade | candidatos/seleções | verificada |
| `Observation.logs` | eventos incrementais | crença e auditoria | verificada |
| `search_begin_input` | inicialização opaca da busca | Search API | verificada |
| replays/traces locais | transições, decisões e resultados | análise/treino | derivável |
| logs de ladder | erros, duração e OOD | validação externa | derivável após export |

## Inventário Kaggle autenticado

O CLI autenticado listou as competições:

- Simulation: `pokemon-tcg-ai-battle`;
- Strategy: `pokemon-tcg-ai-battle-challenge-strategy`.

Após o aceite das regras, a API reportou `userHasEntered=True` para ambas. Os oito arquivos foram baixados para o repositório e inspecionados. O manifesto canônico é [`data/raw/kaggle/manifest.json`](../data/raw/kaggle/manifest.json).

### Datasets presentes nas duas trilhas

| Arquivo | Tamanho (bytes) | Formato detectável | Simulation | Strategy |
|---|---:|---|---|---|
| `Card_ID List_EN.pdf` | 137654485 | PDF 1.6, 1306 páginas | `1931b688…58432` | idêntico à Simulation |
| `Card_ID List_JP.pdf` | 182284028 | PDF 1.6, 1306 páginas | `ca963b82…7e74` | idêntico à Simulation |
| `EN_Card_Data.csv` | 359151 | CSV UTF-8, 2022 linhas lógicas, 17 colunas | `a0ea63cf…f373` | idêntico à Simulation |
| `JP_Card_Data.csv` | 442788 | CSV UTF-8, 2022 linhas lógicas, 17 colunas | `2215ba62…c27` | idêntico à Simulation |

Os quatro pares são byte a byte idênticos, confirmado por tamanho e SHA-256. As cópias não foram deduplicadas para preservar a proveniência por competição.

### Arquivos adicionais da Simulation

A listagem inclui a árvore `ptcg_engine/ptcgProgram 22/` (fontes C/C++, licença e projeto) e `sample_submission/sample_submission/` (`main.py`, `deck.csv` e biblioteca `cg` para Linux/macOS/Windows). Eles são artefatos de SDK/submissão, não datasets Strategy. O inventário completo deve ser salvo no manifesto após o download.

## Destino local

```text
data/raw/kaggle/
  simulation/
  strategy/
  manifest.json
  samples/
  README.md
```

Os arquivos permanecem separados por competição. Não criar symlink nem deduplicar antes de comparar SHA-256 e licenças.

## Inspeção concluída

- ambos os CSVs têm 2022 registros lógicos, 17 colunas e 1267 `Card ID` distintos;
- um `Card ID` aparece em até três linhas porque cada ataque ocupa uma linha;
- `(Card ID, Move Name)` não apresenta duplicatas no arquivo EN; a chave equivalente JP também não;
- há quebras de linha dentro de campos de efeito, portanto `wc -l` não representa o número de registros;
- os PDFs têm 1306 páginas, não são criptografados e não contêm JavaScript;
- as amostras sanitizadas estão em `data/raw/kaggle/samples/`;
- uso e redistribuição continuam sujeitos às regras Kaggle; nenhuma licença embutida foi presumida.

SDK e sample submission adicionais da Simulation ainda devem ser inventariados separadamente quando a implementação F0 começar; eles não fazem parte destes oito datasets.

## Fontes externas

Rulebook, metagame e decklists públicas ficam em `data/external/` com URL, data, licença e versão. Nunca são apresentados como dados oficiais da competição.
