# Quem Sou Eu? Adivinha

Jogo de adivinhação offline para iPhone. O motor local escolhe perguntas por ganho de informação e reordena os candidatos conforme as respostas.

## Estado atual

- MVP SwiftUI premium com onboarding e mascote
- 76 personalidades e 56 perguntas validadas
- Seis categorias completas e modo Todos
- Partidas restauráveis, coleção e progresso local
- Retratos selecionados com créditos e licenças documentados
- Testes do motor e da persistência em CI macOS

## Desenvolvimento

```sh
brew install xcodegen
cd iosApp
xcodegen generate
xcodebuild -project QuemSouEu.xcodeproj -scheme QuemSouEu -sdk iphonesimulator -configuration Debug build CODE_SIGNING_ALLOWED=NO
```

O conteúdo fica em `iosApp/Resources/KnowledgeBase/knowledge.json`. Novas pessoas, perguntas e imagens devem passar por `python3 scripts/validate_content.py`. A versão atual usa até 14 perguntas por partida e apresenta um resultado sem palpite quando a confiança é insuficiente.
