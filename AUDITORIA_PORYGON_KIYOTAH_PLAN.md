# Auditoria Porygon × exemplos Kiyotah — plano

## Prompt original

> realize uma auditoria no código do agente do Porygon e nos agentes das seguintes pastas:
>
> `/home/igor/Documentos/Pokemon_TCG_engine_Kaggle/experiments/2026-08-10_kiyotah_dragapult`
> `/home/igor/Documentos/Pokemon_TCG_engine_Kaggle/experiments/2026-08-10_kiyotah_iono`
> `/home/igor/Documentos/Pokemon_TCG_engine_Kaggle/experiments/2026-08-10_kiyotah_mega_lucario`
>
> Encontre insights de melhorias que podemos fazer no nosso código que estão presentes nesses exemplos
>
> Todos esses decks tem melhor performance que nós, explore por que, enumere formas de melhorar, liste razões, faça um plano e apresente detalhadamente insights dessa analise e dessas comparações.

## Resumo e diagnóstico

O Porygon já é mais forte em engenharia que os exemplos: parser próprio, geração legal de seleções, filtros, `PrizeMap`, cálculo de dano, objetivos persistentes, estágios canônicos, compromissos de linha e rastros auditáveis. Os exemplos são políticas monolíticas específicas ao deck.

A vantagem potencial dos exemplos está em três padrões: planejamento explícito de ataque antes de escolher ações, contabilidade mais agressiva de cópias restantes e heurísticas contextuais para cada efeito. Não há métricas ou ratings nas três pastas que comprovem a alegação de desempenho superior; isso será validado em torneio local controlado, sem atribuir desempenho ao código antes de separar efeito de deck, pareamento e amostra.

| Insight observado | Exemplo | Adaptação segura ao Porygon |
|---|---|---|
| Planejar atacante, alvo, energia e troca antes de pontuar ações | Dragapult e Mega Lucario | Criar um avaliador de plano público de turno que reordene candidatos `MAIN` conforme uma linha concreta de KO, evolução, promoção ou sobrevivência. |
| Avaliar alvo por Prizes, HP, Energia, Tool e estágio | Dragapult e Mega Lucario | Generalizar a pontuação de alvo já existente para ações que alteram o alvo, preservando cálculo exato de dano e valor efetivo de Prize. |
| Inferir cópias restantes a partir do deck e zonas visíveis | Dragapult | Generalizar o inventário de cópias além de Proton e Supporters, usando apenas zonas públicas e `PrizeChecker`; cartas ocultas continuam hipótese, nunca fato. |
| Penalizar duplicatas e buscas sem conversão | Iono e Dragapult | Aplicar valor marginal: segunda cópia, busca, recuperação e compra só pontuam se aumentarem uma linha atual de ataque, desenvolvimento ou sobrevivência. |
| Usar logs do turno anterior para adaptar o plano | Dragapult | Formalizar sinais públicos de histórico de turno/matchup no Porygon, com evidência no trace e sem regras especulativas. |
| Proteger contra deck-out antes de compra opcional | Iono e Dragapult | Substituir limiares fixos copiados por um orçamento de compra por ação, bloqueando compra opcional quando não houver KO, Prize ou recuperação verificável. |
| Otimizar efeitos multi-alvo por resultado agregado | Dragapult | Criar otimizador contextual apenas para `DAMAGE_COUNTER`, `DISCARD`, busca e seleção múltipla que o deck realmente exponha em replays. |

Não adotar diretamente: estado global dos notebooks, ordenação por `attackId`, pontuações numéricas sem razões, acesso direto à SDK em toda a política e ausência de validação/fallback. Esses pontos conflitam com os contratos e a auditabilidade do projeto.

## Mudanças de implementação

1. Fechar a pré-condição P0 de T-034 antes de alterar gameplay: reproduzir os quatro prompts representativos do pacote `55333874`, obter julgamento do Owner para cada divergência e registrar objetivo, ranking, filtros, compromisso e fallback completos. Nenhuma regra inspirada nos exemplos será promovida sem essa evidência.

2. Adicionar ao `HonchkrowPorygonAgent` um `PublicTurnPlan` factual e replanejável, separado de `GameState` e `BeliefState`. Em cada `MAIN`, ele classificará linhas concretas em ordem: vitória/KO que fecha Prizes, prevenção de derrota sem Pokémon, KO de maior Prize, ataque habilitado por evolução/promoção/energia, desenvolvimento e recursos. O plano só poderá comprometer ações quando todos os pré-requisitos públicos estiverem presentes.

3. Extrair um avaliador comum de linha de ataque:
   - enumerar atacante ativo/Bench promovível, ataque legal, alvo acessível, Energia necessária e ação preparatória disponível;
   - calcular dano, KO, Prizes e custo com as funções canônicas;
   - reclassificar anexação, evolução, Giovanni, retirada e promoção apenas quando elas completarem essa mesma linha;
   - manter as exceções ratificadas de Porygon2, Rocket Feathers, R Command, Ignition, Articuno e Mega Abomasnow.

4. Criar `VisibleDeckInventory`, alimentado pela definição do deck, mão, campo, descarte, Prize público, `looking` e resultados exatos do `PrizeChecker`. Expor cópias restantes, recuperabilidade e valor marginal por carta; substituir contagens locais duplicadas gradualmente, sem inventar conteúdo de Prizes ocultos.

5. Integrar um guard de recursos baseado em conversão, não em limiar fixo: cada compra, busca ou recuperação opcional precisa demonstrar ganho imediato de KO, Prize, atacante, evolução, recuperação ou sobrevivência. Caso contrário, preservar o recurso e registrar `resource_guard` no ledger. O deck-out continua sendo bloqueio rígido quando a ação reduzir a última reserva sem linha pública de ganho.

6. Estender o trace de decisão com `turn_plan`, opções de ataque avaliadas, pré-requisitos faltantes, inventário relevante, razão de bloqueio e motivo de replanejamento. Isso elimina as lacunas atuais de T-034 entre estado/candidatos e seleção final.

## Validação

1. Criar goldens para: atacante do Bench que exige promoção; evolução e ataque no mesmo turno; escolha de alvo por Prize; busca sem alvo restante; descarte de duplicata versus peça de linha; compra bloqueada por reserva; e efeito multi-seleção aplicável ao deck.

2. Reproduzir os prompts de T-034 antes e depois; exigir que toda divergência tenha explicação de plano e decisão aceita pelo Owner, sem inferir resultado alternativo da partida.

3. Executar os três notebooks sem modificá-los como referências de comportamento, validar seus pacotes extraídos e rodar uma matriz bilateral: Porygon baseline e candidato contra Dragapult, Iono e Mega Lucario, nos dois lados, com 200 episódios por combinação política–oponente–lado. Reportar taxa de vitória, falhas, deck-outs, latência, motivos terminais e variância por matchup.

4. Promover somente se o candidato mantiver zero `INVALID`/`ERROR`/`TIMEOUT`, não piorar a conformidade de T-034, não aumentar deck-outs e superar o baseline em screening de 300 partidas seguido de bloco independente de 1.000 partidas. O torneio contra os exemplos informa matchups; a promoção continua baseada na comparação Porygon baseline × candidato.

## Premissas

- Prioridade escolhida: conformidade estratégica do Owner primeiro, ganho de vitórias depois.
- Os exemplos são fonte de padrões, não especificação de regras para o deck Honchkrow/Porygon.
- O estado observado é público e factual; estimativas de cartas ocultas permanecem no mecanismo de crença, nunca no inventário factual.
- A sequência canônica `DEVELOP → SEARCH → CALCULATE → SUPPORTER → FACTORY → ROTO → HEADSET → ATTACK` permanece vigente; o planejador a torna verificável, não a substitui.
