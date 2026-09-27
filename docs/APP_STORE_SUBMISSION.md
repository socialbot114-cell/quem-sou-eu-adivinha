# App Store Submission Package

## App Information

- App name: `Quem Sou Eu? Adivinha`
- Subtitle: `Jogo de pistas e perguntas`
- Primary category: `Games`
- Secondary category: `Entertainment`
- Game subcategory: `Trivia`
- Price: `Free`
- Copyright: `2026 Gustavo De Melo Ferreira`
- Intended audience: `9+ family experience`
- Bundle ID: `br.com.quemsoueu.adivinha`
- Version: `1.2.3` (build 41)

## Promotional Text

Pense em uma personalidade. Responda perguntas e veja o jogo descobrir quem você imaginou.

## Description

Pense em alguém conhecido e deixe o Quem Sou Eu? Adivinha tentar descobrir quem é.

O jogo faz perguntas simples, combina suas respostas e apresenta o palpite mais provável. Você pode escolher uma categoria ou jogar com todas as personalidades disponíveis.

Recursos:

- Partidas rápidas com até 14 perguntas.
- Doze categorias temáticas e modo livre.
- Motor de descoberta que funciona totalmente offline.
- Pontos, moedas, sequência e conquistas salvos no aparelho.
- Princesa Detetive, coleção de descobertas e interface premium.

Não é necessário criar uma conta. O jogo não exibe anúncios, não exige internet e não coleta dados pessoais.

## Keywords

adivinha,quiz,perguntas,jogo,personalidades,trivia,quem sou eu

## What's New

Uma nova experiência para o Quem Sou Eu? Adivinha.

- Jogo de pistas e perguntas offline.
- 305 personalidades em doze categorias temáticas.
- 150 novas personalidades adicionadas às categorias existentes, com pistas ampliadas para K-pop, música, esportes, artistas brasileiros e criadores digitais.
- Onboarding, retomada de partida e coleção de descobertas.
- Novo visual com a Princesa Detetive.
- Retratos, compartilhamento, pontos, moedas e sequência.

## URLs

- Support URL: `https://socialbot114-cell.github.io/quem-sou-eu-adivinha-site/`
- Marketing URL: `https://socialbot114-cell.github.io/quem-sou-eu-adivinha-site/`
- Privacy Policy URL: `https://socialbot114-cell.github.io/quem-sou-eu-adivinha-site/privacy.html`

## App Privacy

Select `Data Not Collected`.

The app does not collect, transmit, sell, share or use personal data. It has no account system, advertising SDK, analytics SDK, tracking, backend or network requirement. Local progress is stored only on the user's device.

## Export Compliance

Select that the app does not use encryption other than the standard encryption provided by the operating system, if App Store Connect asks this question. The project already declares `ITSAppUsesNonExemptEncryption` as `false`.

## Content Rights

Declare that the app contains third-party editorial photographs and that the developer has the necessary rights. The approved photographs use Creative Commons licenses and include author, source, license and modification details in the in-app credits and `docs/content/image-credits.json`. Do not use any unapproved image from the source collection.

## Review Notes

Olá,

O Quem Sou Eu? Adivinha é um jogo de perguntas totalmente offline para iPhone.

Para testar:

1. Abra o app.
2. Conclua ou pule a apresentação inicial.
3. Toque em `Jogar agora` ou abra a aba `Jogar`.
4. Escolha uma categoria ou o modo livre.
5. Responda usando `Sim`, `Provavelmente`, `Não sei`, `Acho que não` ou `Não`.
6. Continue até o app apresentar o palpite.

Não é necessário criar uma conta, fazer login, conceder permissões ou conectar-se à internet. O progresso é salvo localmente no dispositivo. Não há compras, anúncios, rastreamento ou conteúdo que exija autenticação.

Obrigado.

## Screenshot Set

Use screenshots capturadas do build final em um iPhone real ou no Simulator. Não use as imagens de referência da pasta `prints/`.

The release package is in `store-kit/screenshots/iphone/` and contains three real app screenshots at `1284x2778` for the 6.5-inch iPhone slot (`APP_IPHONE_65`). Apple currently requires the 6.5-inch set when a 6.9-inch set is not provided, and scales it for supported displays. See [Apple's screenshot specifications](https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications/). The 1.2.3 submission currently has eight screenshots in this set, all processed as `COMPLETE`.

Recommended order when expanding the set:

1. Home screen showing the mascot and `Jogar agora`.
2. Category screen showing the category grid.
3. Question screen showing the progress indicator and answer buttons.
4. Result screen showing a successful guess.
5. Profile screen showing offline operation and privacy information.

For a dedicated 6.9-inch set, use an accepted portrait size such as `1290x2796` pixels and the `APP_IPHONE_67` display type. Capture the final release candidate after its build is marked `VALID` in App Store Connect.

## Final Submission Checklist

- [x] Confirm build 41 is marked `VALID` through the App Store Connect API.
- [x] Associate build 41 with version 1.2.3.
- [x] Upload and process the 6.5-inch screenshots; eight images show `COMPLETE`.
- [x] Confirm subtitle, description, keywords and URLs.
- [x] Set `Games` / `Trivia` and free pricing.
- [x] Confirm the age-rating questionnaire matches the app content (currently recorded as 4+ in `PROJECT_STATUS.md`).
- [x] Set App Privacy to `Data Not Collected`.
- [x] Answer export compliance.
- [x] Confirm content rights.
- [x] Add the App Review notes above.
- [x] Submit for Review through `.github/workflows/app-store-review.yml`; version state is `WAITING_FOR_REVIEW`.

## API Workflow

Run `App Store Connect Release` manually from the release branch with `operation=inspect` to read the build, version, screenshot, review-contact, and submission states. To submit, run with `operation=submit` and the exact confirmation `SUBMIT 1.2.3 (41)`. The workflow waits for build 41 to become `VALID`, uploads metadata and screenshots, associates the build, and submits with automatic release after approval. The 1.2.3 submission is currently `WAITING_FOR_REVIEW` (submission ID `e452da04-8ccf-4245-ac9d-04d41184cf83`).
