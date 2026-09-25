# Quem Sou Eu? Adivinha

Jogo de adivinhação offline para iPhone. O motor local escolhe perguntas por ganho de informação e reordena os candidatos conforme as respostas.

## Estado atual

- MVP SwiftUI premium com onboarding e mascote
- 149 personalidades e 102 perguntas validadas
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

O catálogo principal fica em `iosApp/Resources/KnowledgeBase/knowledge.json`; o lote temático complementar fica em `iosApp/Resources/KnowledgeBase/character-expansion.json`. Para reconstruir e validar o lote:

```sh
python3 scripts/build_character_expansion.py
python3 scripts/validate_content.py
python3 scripts/evaluate_offline.py
```

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

Jev revisa a clareza de cada pergunta nova e se a fonte sustenta a profissão principal dos personagens; decisões abaixo de 0,8 são registradas para revisão editorial. O validador determinístico e o simulador offline verificam as respostas estruturadas, cobertura e capacidade de distinção. Trechos biográficos, licenças e datas de verificação ficam em `docs/content/`; a chave `TYPESAFE_API_KEY` é usada somente no ambiente editorial, nunca no app. O jogo continua funcionando inteiramente offline e usa até 14 perguntas por partida.
