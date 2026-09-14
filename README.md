# Quem Sou Eu? Adivinha

Jogo de adivinhação offline para iPhone. O motor local escolhe perguntas por ganho de informação e reordena os candidatos conforme as respostas.

## Estado atual

- MVP SwiftUI funcional
- Set inicial de 12 personalidades
- Set inicial de 10 perguntas
- Sete categorias e modo Todos
- Progresso local
- Teste unitário do motor

## Desenvolvimento

```sh
brew install xcodegen
cd iosApp
xcodegen generate
xcodebuild -project QuemSouEu.xcodeproj -scheme QuemSouEu -sdk iphonesimulator -configuration Debug build CODE_SIGNING_ALLOWED=NO
```

O conteúdo fica em `iosApp/Resources/KnowledgeBase/knowledge.json`. Novas pessoas e perguntas devem passar pelo validador antes de entrar no app. A versão atual usa até 10 perguntas por partida.
