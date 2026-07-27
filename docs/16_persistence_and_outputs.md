# Persistência e outputs

## Layout de run

```text
runs/<experiment_id>/<run_id>/
  manifest.json
  matches.jsonl
  decisions.jsonl
  metrics.json
  metrics.csv
  summary.md
  replays/
  errors/
```

`runs/` é saída gerada, fora do pacote de submissão.

## Contratos

- `manifest.json`: entrada resolvida, versões, hashes, seeds e matriz.
- `matches.jsonl`: um `MatchRecord` por linha.
- `decisions.jsonl`: um `DecisionRecord` por linha.
- `metrics.json`: valores completos para máquinas.
- `metrics.csv`: tabela achatada para análise.
- `summary.md`: interpretação e decisão, sem recomputar métricas.
- `replays/`: payload suficiente para reprodução/auditoria.
- `errors/`: stack trace e contexto sanitizado.

## Imutabilidade

Arquivos de um run concluído não são sobrescritos. Correção cria novo `run_id` e referencia o anterior. Artefato promovido recebe SHA-256 e cópia do manifesto.

## Retenção

- logs brutos: conservar para candidatos e falhas; runs exploratórios podem seguir política documentada;
- relatórios: conservar todos;
- datasets derivados: versionar esquema, fontes e transformação;
- modelos/pacotes: conservar versões promovidas e referência anterior.

## Privacidade e segurança

Não persistir token Kaggle, variáveis secretas ou caminhos de credenciais. Amostras do catálogo removem identificadores pessoais; dados oficiais de cartas não contêm dados pessoais esperados, mas ainda passam por inspeção de colunas.

## Atomicidade

Escrever saídas temporárias e renomear somente após validação. Manifesto começa como `RUNNING`; conclusão muda para `COMPLETED` após todos os arquivos obrigatórios existirem.
