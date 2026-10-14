# Quem Sou Eu? Adivinha

Jogo de adivinhação offline para iPhone. O motor local escolhe perguntas por ganho de informação e reordena os candidatos conforme as respostas.

## Estado atual

- MVP SwiftUI premium com onboarding e mascote
- 305 personalidades e 128 perguntas validadas
- Doze categorias temáticas e modo Todos
- Partidas restauráveis, coleção e progresso local
- Dezesseis retratos selecionados com créditos e licenças documentados
- Testes do motor e da persistência em CI macOS

## Desenvolvimento

```sh
brew install xcodegen
cd iosApp
xcodegen generate
xcodebuild -project QuemSouEu.xcodeproj -scheme QuemSouEu -sdk iphonesimulator -configuration Debug build CODE_SIGNING_ALLOWED=NO
```

O catálogo principal fica em `iosApp/Resources/KnowledgeBase/knowledge.json`; `scripts/character-batch-150.json` é a fonte dos 150 personagens novos e `iosApp/Resources/KnowledgeBase/character-expansion.json` é a expansão embarcada gerada. Para reconstruir e testar o catálogo:

```sh
python3 scripts/build_character_expansion.py
python3 scripts/validate_content.py
python3 scripts/audit_catalog_evidence.py
python3 scripts/evaluate_offline.py
python3 scripts/evaluate_gameplay.py --seed 42
```

`evaluate_gameplay.py` simula partidas completas, incluindo palpites rejeitados, e compara respostas ideais, desconhecidas, contraditórias e ruidosas. Use-o para validar alterações no motor sem depender de dados enviados à rede.

`audit_catalog_evidence.py` compara as células aplicáveis do catálogo com as matrizes de revisão e mostra se ainda faltam fontes, decisões humanas ou respostas por revisar antes de adicionar novos lotes.

O lote editorial é processado e avaliado pelo worker de personagens em `../SKIILS/jerv/worker/review_character_content.py`:

```sh
python3 scripts/build_character_sources.py
python3 scripts/build_jerv_character_review.py
python3 "../SKIILS/jerv/worker/review_character_content.py" \
  docs/content/jerv-character-review-input.json \
  --output docs/content/jerv-character-review-report.json
python3 scripts/finalize_jerv_character_review.py
python3 scripts/validate_content.py
```

Para revisar as respostas dos 150 novos personagens com JERV por categoria e combinar os relatórios:

```sh
python3 scripts/run_jerv_answer_matrix_150.py
```

O relatório combinado fica em `docs/content/jerv-answer-matrix-150-report.json`; “evidência insuficiente” é mantida como pendência editorial e não é interpretada como resposta “Não”.

Para adicionar fontes da base principal e reavaliar a matriz complementar que cobre as células antes sem JERV:

```sh
python3 scripts/build_character_sources.py --scope primary
python3 "../SKIILS/jerv/worker/review_character_content.py" \
  docs/content/jerv-answer-matrix-gap-input.json \
  --output docs/content/jerv-answer-matrix-gap-report.json \
  --batch-size 12
python3 scripts/audit_catalog_evidence.py --output docs/content/catalog-validation-queue.json
```

Para obter fontes básicas da base principal e revisar pelo JERV as células que ainda não tinham matriz:

```sh
python3 scripts/build_character_sources.py --scope primary
python3 "../SKIILS/jerv/worker/review_character_content.py" \
  docs/content/jerv-answer-matrix-gap-input.json \
  --output docs/content/jerv-answer-matrix-gap-report.json \
  --batch-size 12
python3 scripts/audit_catalog_evidence.py
```

O relatório adicional avalia as respostas, mas `human-review` continua exigindo adjudicação com evidência específica antes de liberar outro lote.

Jev revisa a clareza de cada pergunta nova e se a fonte sustenta a profissão principal dos personagens; decisões abaixo de 0,8 são registradas para revisão editorial. O validador determinístico e o simulador offline verificam as respostas estruturadas, cobertura e capacidade de distinção. Trechos biográficos, licenças e datas de verificação ficam em `docs/content/`; a chave `TYPESAFE_API_KEY` é usada somente no ambiente editorial, nunca no app. O jogo continua funcionando inteiramente offline e usa até 14 perguntas por partida.
