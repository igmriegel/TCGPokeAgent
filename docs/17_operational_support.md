# Operação diária

## Ciclo

1. `preflight`: versões, deck, dados e imports.
2. `smoke`: 20 partidas nos dois lados.
3. `full`: pelo menos 200 partidas.
4. `compare`: candidato versus referência/ablação.
5. `freeze`: código, deck, configuração e hashes.
6. `package`: `.tar.gz`.
7. `validate-package`: extração e smoke isolado.
8. `strategy-export`: bloco de evidência.

Comandos-alvo estão em [`23_scripts_spec.md`](23_scripts_spec.md).

## Perfis de runtime

- `heuristic-only`: caminho estável e fallback de toda versão.
- `search-enabled`: mesma heurística com busca sujeita a gates.
- `trace`: logging detalhado, somente local.
- `submission`: logging limitado, paths relativos e dependências empacotadas.

## Diagnóstico

Ordem de inspeção:

1. status do ambiente e erro;
2. observação/select original;
3. seleções válidas geradas;
4. escolha/fallback e razões;
5. duração e overage;
6. crença e ciclo da Search API;
7. versão/hash de todos os componentes.

## Incidentes

- um `INVALID`, `ERROR` ou `TIMEOUT`: bloquear promoção;
- falha de busca: manter partida via heurística e abrir ocorrência;
- schema desconhecido: fallback legal, guardar fixture sanitizada e adicionar teste;
- regressão de SDK: congelar 1.14.10 e abrir experimento de compatibilidade;
- pacote falha isolado: não submeter, mesmo que o código local passe.
