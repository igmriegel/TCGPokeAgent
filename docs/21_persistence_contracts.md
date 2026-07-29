# Data catalog and provenance

External verification: **2026-07-27**.

## States

- `verified`: content or metadata directly observed at the source.
- `derivable`: produced from verified source by documented transformation.
- `pending`: metadata or content not yet inspected.
- `external`: source outside the two competitions/SDK, kept separate.

## Runtime and SDK sources

| Source | Content | Usage | Status |
|---|---|---|---|
| `all_card_data()` | ID, name, type, HP, stage, weakness, resistance, retreat, skills, attacks | catalog and features | verified in API documentation |
| `all_attack()` | ID, name, text, damage, energies | attack scoring | verified in API documentation |
| `Observation.current` | visible factual state | parser/evaluator | verified |
| `Observation.select` | context, options and cardinality | candidates/selections | verified |
| `Observation.logs` | incremental events | belief and audit | verified |
| `search_begin_input` | opaque search initialization | Search API | verified |
| local replays/traces | transitions, decisions and results | analysis/training | derivable |
| human demonstrations | visible state, legal options, selected indices, rationale and confidence | heuristic discovery/preference learning | derivable, consent-controlled |
| ladder logs | errors, duration and OOD | external validation | derivable after export |

## Authenticated Kaggle inventory

The authenticated CLI listed the competitions:

- Simulation: `pokemon-tcg-ai-battle`;
- Strategy: `pokemon-tcg-ai-battle-challenge-strategy`.

After accepting the rules, the API reported `userHasEntered=True` for both. The eight files were downloaded to the repository and inspected. The canonical manifest is [`data/raw/kaggle/manifest.json`](../data/raw/kaggle/manifest.json).

### Datasets present in both tracks

| File | Size (bytes) | Detectable format | Simulation | Strategy |
|---|---:|---|---|---|
| `Card_ID List_EN.pdf` | 137654485 | PDF 1.6, 1306 pages | `1931b688…58432` | identical to Simulation |
| `Card_ID List_JP.pdf` | 182284028 | PDF 1.6, 1306 pages | `ca963b82…7e74` | identical to Simulation |
| `EN_Card_Data.csv` | 359151 | CSV UTF-8, 2022 logical rows, 17 columns | `a0ea63cf…f373` | identical to Simulation |
| `JP_Card_Data.csv` | 442788 | CSV UTF-8, 2022 logical rows, 17 columns | `2215ba62…c27` | identical to Simulation |

The four pairs are byte-identical, confirmed by size and SHA-256. The copies were not deduplicated to preserve provenance per competition.

### Additional Simulation files

The listing includes the `ptcg_engine/ptcgProgram 22/` tree (C/C++ sources, license and project) and `sample_submission/sample_submission/` (`main.py`, `deck.csv` and `cg` library for Linux/macOS/Windows). They are SDK/submission artifacts, not Strategy datasets. The full inventory must be saved in the manifest after download.

## Local destination

```text
data/raw/kaggle/
  simulation/
  strategy/
  manifest.json
  samples/
  README.md
```

Files remain separated by competition. Do not create symlinks or deduplicate before comparing SHA-256 and licenses.

## Inspection completed

- both CSVs have 2022 logical records, 17 columns and 1267 distinct `Card ID`;
- one `Card ID` appears in up to three lines because each attack occupies one line;
- `(Card ID, Move Name)` has no duplicates in the EN file; the equivalent JP key also does not;
- there are line breaks inside effect fields, therefore `wc -l` does not represent the number of records;
- the PDFs have 1306 pages, are not encrypted and do not contain JavaScript;
- the sanitized samples are in `data/raw/kaggle/samples/`;
- use and redistribution remain subject to Kaggle rules; no embedded license was assumed.

Additional SDK and sample submission from Simulation must still be inventoried separately when F0 implementation starts; they are not part of these eight datasets.

## External sources

Rulebook, metagame and public decklists go in `data/external/` with URL, date, license and version. They are never presented as official competition data.
