# Quem Sou Eu? Adivinha - Estado do Projeto

## Estado

MVP inicial em construção. O projeto já contém configuração XcodeGen, base offline, motor probabilístico, fluxo SwiftUI e persistência local.

## Apple configurada

- App Store Connect app ID: `6810873964`
- Bundle ID: `br.com.quemsoueu.adivinha`
- Bundle identifier resource ID: `XS57YRQC46`
- Provisioning profile: `Quem Sou Eu Adivinha App Store 2026 v2` (`YX8AJ63395`)
- Profile UUID: `2bf9e748-a220-4274-a157-c5878696d5dc`
- Candidato de release: versão `1.2.3`, build `41` (IPA enviado ao TestFlight pelo GitHub Actions, run `36331786815`).
- Site: https://socialbot114-cell.github.io/quem-sou-eu-adivinha-site/
- Repositório do app: https://github.com/socialbot114-cell/quem-sou-eu-adivinha
- Repositório do site: https://github.com/socialbot114-cell/quem-sou-eu-adivinha-site

Metadata, descrição, palavras-chave, copyright, notas de revisão, URLs de suporte e marketing foram salvos no App Store Connect. Categoria `Games > Trivia`, categoria secundária `Entertainment`, direitos de conteúdo, classificação etária sem conteúdo sensível, preço gratuito e disponibilidade mundial também foram configurados. App Privacy foi publicado como `Data Not Collected`.

## Submission package

- Copy-ready metadata and review answers: `docs/APP_STORE_SUBMISSION.md`
- Real screenshot capture instructions: `docs/SCREENSHOT_CAPTURE.md`
- The screenshots in `prints/` are references only and must not be uploaded.

## Próximos marcos

- Confirmar o processamento do build 41 pelo workflow `.github/workflows/app-store-review.yml`; os testes de UI das telas principais passaram no workflow de screenshots do mesmo commit.
- Criar/submeter a versão 1.2.3 para App Review pela API após confirmar o build e os screenshots no relatório do workflow.
- Screenshots selecionados para a submissão: `store-kit/screenshots/iphone/` (três PNGs 1284×2778, slot iPhone 6,5", validados contra as capturas do app).
- Para a 1.2.3, usar o workflow `ios-release.yml`, que assina e envia o IPA ao TestFlight pela API do App Store Connect. A integração Xcode Cloud é separada e permanece como tarefa posterior.
- Revisão editorial dos perfis e perguntas da base expandida com o worker JERV concluída.
- Revisar manualmente as 2.749 células da matriz de respostas dos 150 novos personagens que ainda não atingiram o limiar de evidência JERV.
- Avaliar a diferença restante em acerto no cenário simulado com uma resposta contraditória antes do próximo release.
- Adicionar screenshots e vídeo de demonstração gerados no simulador macOS via GitHub Actions.
- Criar site de suporte e privacidade.
- Criar App ID e registro exclusivo no App Store Connect.
- Configurar workflow TestFlight.
- Testar em aparelho real e enviar a versão 1.2 para revisão.

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
