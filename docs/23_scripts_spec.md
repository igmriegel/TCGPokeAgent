# Contrato de comandos operacionais

Estes comandos são alvos de implementação; não são declarados disponíveis hoje.

```bash
python -m scripts.preflight --config configs/default.yaml
python -m scripts.run_eval --profile smoke --agent heuristic
python -m scripts.run_eval --profile full --agent search
python -m scripts.compare_runs --candidate RUN --baseline RUN
python -m scripts.freeze_candidate --run RUN
python -m scripts.package_submission --artifact ARTIFACT
python -m scripts.validate_package --archive submission.tar.gz
python -m scripts.export_strategy --run RUN
python -m scripts.inventory_kaggle_data
```

## Regras comuns

- `--help` e exit codes estáveis;
- config e overrides impressos antes da mutação;
- output path impresso no final;
- stdout para resumo, stderr para diagnóstico;
- `0` sucesso, `2` input/config inválido, `3` gate reprovado, `4` falha de runtime;
- scripts chamam `src/`, não duplicam regra de jogo.

## Inventário Kaggle

Após aceitar as regras:

```bash
kaggle competitions download pokemon-tcg-ai-battle -p data/raw/kaggle/simulation
kaggle competitions download pokemon-tcg-ai-battle-challenge-strategy -p data/raw/kaggle/strategy
python -m scripts.inventory_kaggle_data
```

O inventário falha se algum arquivo não tiver fonte, competição, versão/data, tamanho, SHA-256, formato, licença/status, utilidade e risco de leakage.

## Pacote

`package_submission` cria uma staging directory explícita, copia apenas allowlist, verifica raiz e tamanho e gera o tar. `validate_package` rejeita path traversal e executa smoke sem imports do checkout.

## Idempotência

Preflight e inventário podem ser repetidos. Runs e freezes nunca sobrescrevem IDs existentes. Package pode ser reproduzido com os mesmos inputs e registra seu hash, mesmo que metadados do tar impeçam byte-identidade sem normalização.
