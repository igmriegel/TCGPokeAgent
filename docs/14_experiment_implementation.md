# Implementação de experimentos

## Caminho de um run

1. Carregar defaults, perfil de agente e perfil de avaliação.
2. Aplicar overrides explícitos.
3. Resolver e validar o `ExperimentSpec`.
4. Persistir `manifest.json` antes da primeira partida.
5. Executar a matriz planejada.
6. Calcular métricas e comparação.
7. Avaliar a expressão de aceite.
8. Persistir decisão e bloco para `strategy_notes.md`.

## Identidade

`experiment_id` identifica a hipótese; `run_id` identifica uma execução. Repetição usa novo `run_id`, mesmo `experiment_id`, e referencia o run anterior. Nomes não dependem apenas de timestamp.

## Versões

O manifesto registra:

- commit ou marcador do source;
- hash do deck;
- hash da configuração efetiva;
- versão do SDK e Python;
- hash do modelo;
- esquema de features;
- seeds e pool de oponentes.

`null` é permitido apenas para componente inexistente, nunca para componente não medido.

## Ablation

Cada regra heurística possui flag. Uma ablação muda uma família por vez e mantém o restante congelado. Para modelos, comparar: heurística, modelo sem feature group, modelo completo e, quando aplicável, busca ligada/desligada.

## Holdout temporal

Traces são particionados pela data/ordem de geração. O grid usa treino/validação; uma única avaliação final em holdout escolhe promoção. Regenerar o holdout requer nova versão de dataset.

## Registro

O registry é append-only e aponta para artefatos, não duplica métricas. Runs incompletos permanecem como `FAILED` com erro; não são apagados nem contabilizados como jogos válidos.

## Testes

- mesma spec expande mesma matriz;
- override aparece no manifesto;
- grids não colidem;
- comparação rejeita decks/seeds incompatíveis;
- decisão de gate é reproduzível dos relatórios;
- entrada Strategy contém caminhos existentes.
