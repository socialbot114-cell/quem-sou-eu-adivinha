# Quem Sou Eu? Adivinha - Estado do Projeto

## Estado

MVP inicial em construção. O projeto já contém configuração XcodeGen, base offline, motor probabilístico, fluxo SwiftUI e persistência local.

## Apple configurada

- App Store Connect app ID: `6810873964`
- Bundle ID: `br.com.quemsoueu.adivinha`
- Bundle identifier resource ID: `XS57YRQC46`
- Provisioning profile: `Quem Sou Eu Adivinha App Store 2026 v2` (`YX8AJ63395`)
- Profile UUID: `2bf9e748-a220-4274-a157-c5878696d5dc`
- Versão `1.2.3`, build `41`: IPA enviado ao TestFlight (run `36331786815`) e aprovada, pronta para distribuição (status confirmado pelo usuário).
- App Store version ID: `056c95ba-e1f4-484b-8377-3622a368f980`; review submission ID: `e452da04-8ccf-4245-ac9d-04d41184cf83`.
- Versão `1.2.4`, build `42`: CI (XCTest + UI) aprovado no run `36937852282`, IPA enviado ao TestFlight (run `36940046828`) e submetido para revisão em 2026-10-01 (run `36940913783`), estado `WAITING_FOR_REVIEW`, liberação automática após aprovação. App Store version ID: `220a90f8-db90-4465-990a-d9b72aeac931`; review submission ID: `aefc0167-7593-4344-ac6c-b0183a2c6f2e`.
- Site: https://socialbot114-cell.github.io/quem-sou-eu-adivinha-site/
- Repositório do app: https://github.com/socialbot114-cell/quem-sou-eu-adivinha
- Repositório do site: https://github.com/socialbot114-cell/quem-sou-eu-adivinha-site

Metadata, descrição, palavras-chave, copyright, notas de revisão, URLs de suporte e marketing foram salvos no App Store Connect. Categoria `Games > Trivia`, categoria secundária `Entertainment`, direitos de conteúdo, classificação etária sem conteúdo sensível, preço gratuito e disponibilidade mundial também foram configurados. App Privacy foi publicado como `Data Not Collected`.

## Submission package

- Copy-ready metadata and review answers: `docs/APP_STORE_SUBMISSION.md`
- Real screenshot capture instructions: `docs/SCREENSHOT_CAPTURE.md`
- The screenshots in `prints/` are references only and must not be uploaded.

## Próximos marcos

- Validar perguntas e respostas dos 305 personagens antes de iniciar lotes para 5.000 perfis; gate atual fechado.
- Auditoria atual: JERV avaliou as 6.541 células aplicáveis; 741 foram aceitas pelo modelo, 22 têm adjudicação e 5.783 permanecem em revisão humana.
- Onze respostas foram corrigidas com fontes; quatro contradições JERV continuam pendentes de adjudicação.
- Há 18 perguntas sem decisão editorial consolidada e 0 violações nas invariantes determinísticas verificadas para datas/estado de vida.
- Fila e relatório: `docs/content/CATALOG-VALIDATION-STATUS.md` e `docs/content/catalog-validation-queue.json`.
- Versão `1.2.4`: motor com orçamento adaptativo de perguntas (+3 por palpite rejeitado, até 2 “Não sei” gratuitos, teto 20), piso de likelihood `0,18`, confiança `0,68` / margem `0,10` e botão “Desfazer última resposta”; onze respostas corrigidas com fonte. Métricas em `docs/content/GAMEPLAY-ENGINE-COMPARISON.md`. O build number é o número da execução do workflow `iOS TestFlight`.
- Ferramentas: `scripts/audit_catalog_evidence.py` (evidências) e `scripts/evaluate_gameplay.py` (partidas completas).
- Screenshots fornecidos: `store-kit/screenshots/iphone/` (três PNGs 1284×2778, slot iPhone 6,5"). O App Store Connect mostra oito imagens `COMPLETE` nesse conjunto.
- O workflow `ios-release.yml` assinou e enviou o IPA ao TestFlight pela API do App Store Connect. A integração Xcode Cloud é separada e permanece como tarefa posterior.
- O JERV final revisou as funções principais dos 229 perfis de expansão e a redação das 72 perguntas dessa expansão; essa revisão não comprova cada atributo/resposta.
- Adjudicar os 5.783 resultados `human-review` com fontes específicas antes de abrir o gate para novos personagens.
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
