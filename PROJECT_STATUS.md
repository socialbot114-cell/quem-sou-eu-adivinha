# Quem Sou Eu? Adivinha - Estado do Projeto

## Estado

MVP inicial em construção. O projeto já contém configuração XcodeGen, base offline, motor probabilístico, fluxo SwiftUI e persistência local.

## Apple configurada

- App Store Connect app ID: `6810873964`
- Bundle ID: `br.com.quemsoueu.adivinha`
- Bundle identifier resource ID: `XS57YRQC46`
- Provisioning profile: `Quem Sou Eu Adivinha App Store 2026 v2` (`YX8AJ63395`)
- Profile UUID: `2bf9e748-a220-4274-a157-c5878696d5dc`
- Versão `1.2.3`, build `41`: IPA enviado ao TestFlight (run `36331786815`) e submetido à App Review; App Store Connect está em `WAITING_FOR_REVIEW`, com publicação automática após aprovação (`AFTER_APPROVAL`).
- App Store version ID: `056c95ba-e1f4-484b-8377-3622a368f980`; review submission ID: `e452da04-8ccf-4245-ac9d-04d41184cf83`.
- Site: https://socialbot114-cell.github.io/quem-sou-eu-adivinha-site/
- Repositório do app: https://github.com/socialbot114-cell/quem-sou-eu-adivinha
- Repositório do site: https://github.com/socialbot114-cell/quem-sou-eu-adivinha-site

Metadata, descrição, palavras-chave, copyright, notas de revisão, URLs de suporte e marketing foram salvos no App Store Connect. Categoria `Games > Trivia`, categoria secundária `Entertainment`, direitos de conteúdo, classificação etária sem conteúdo sensível, preço gratuito e disponibilidade mundial também foram configurados. App Privacy foi publicado como `Data Not Collected`.

## Submission package

- Copy-ready metadata and review answers: `docs/APP_STORE_SUBMISSION.md`
- Real screenshot capture instructions: `docs/SCREENSHOT_CAPTURE.md`
- The screenshots in `prints/` are references only and must not be uploaded.

## Próximos marcos

- Acompanhar a App Review da versão 1.2.3. O workflow de verificação `36336639557` confirmou o build 41 `VALID`, associado à versão; os screenshots do slot iPhone 6,5" estão todos `COMPLETE`.
- A versão será publicada automaticamente depois da aprovação da Apple (`releaseType: AFTER_APPROVAL`).
- A submissão foi realizada pelo workflow `.github/workflows/app-store-review.yml` (run `36336324022`); inspeção inicial: `36336221653`.
- Screenshots fornecidos: `store-kit/screenshots/iphone/` (três PNGs 1284×2778, slot iPhone 6,5"). O App Store Connect mostra oito imagens `COMPLETE` nesse conjunto.
- O workflow `ios-release.yml` assinou e enviou o IPA ao TestFlight pela API do App Store Connect. A integração Xcode Cloud é separada e permanece como tarefa posterior.
- Revisão editorial dos perfis e perguntas da base expandida com o worker JERV concluída.
- Revisar manualmente as 2.749 células da matriz de respostas dos 150 novos personagens que ainda não atingiram o limiar de evidência JERV.
- Avaliar a diferença restante em acerto no cenário simulado com uma resposta contraditória antes do próximo release.
- Screenshots e vídeo de demonstração foram gerados no simulador macOS via GitHub Actions.
- Site de suporte e privacidade publicado; App ID e registro App Store Connect configurados.
- Workflow TestFlight configurado; teste em aparelho físico continua como validação futura.

## Catálogo expandido

- Base total: 305 personalidades, 128 perguntas e 12 categorias temáticas, além do modo Todos.
- Lote complementar: `iosApp/Resources/KnowledgeBase/character-expansion.json` (229 perfis, incluindo o lote de 150 personagens em `scripts/character-batch-150.json`, distribuído pelas 12 categorias existentes).
- Proveniência das respostas: `docs/content/character-sources.json`.
- Revisão Jev/JERV: `docs/content/jerv-character-review-report.json`, com decisões editoriais adicionais em `docs/content/jerv-character-human-review.json`.
- Matriz JERV dos 150 novos perfis: `docs/content/jerv-answer-matrix-150-input.json`, `docs/content/jerv-answer-matrix-150-report.json` e adjudicações em `docs/content/jerv-answer-matrix-150-adjudications.json`.
- Simulação offline da base completa: 100% ideal, 97,5% com uma resposta desconhecida e 94,7% com uma resposta contraditória (323 ocorrências categoria–personagem).
- Retratos licenciados: 16, com autores, licenças, origens e modificações em `docs/content/image-credits.json`.

## Identidade planejada

- Nome: `Quem Sou Eu? Adivinha`
- Bundle ID: `br.com.quemsoueu.adivinha`
- Team ID: `SRN7AW424S`
- Plataforma inicial: iPhone
- Offline, sem anúncios, sem login e sem coleta de dados

## Regra de publicação

Screenshots finais devem ser capturas do app real. As artes em `prints/` são referências e não devem ser enviadas diretamente para a App Store.
