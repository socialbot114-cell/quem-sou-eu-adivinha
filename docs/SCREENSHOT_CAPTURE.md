# Final Screenshot Capture

Screenshots must come from the final signed app build. The current files in `prints/` are design references and must not be uploaded as App Store screenshots.

## Capture Order

1. Home: show `Olá!`, the mascot, statistics and `Jogar agora`.
2. Categories: show the category grid and the `Todas` option.
3. Question: show a real question, progress indicator and answer choices.
4. Result: answer enough questions to show `Acho que descobri!` and the guessed person.
5. Profile: show `Funciona sem internet` and `Nenhum dado coletado`.

## Simulator

Use an iPhone 15 Pro Max or another 6.7-inch iPhone simulator. Capture portrait screenshots at the simulator's native resolution. Do not add fake device frames, third-party logos, copyrighted photographs or promotional text over the screenshots.

## GitHub Actions review capture

Run the `Quem Sou Eu iOS Screenshots` workflow manually. On macOS runners it captures the home screen, the expanded category grid, a real game question, the result, and profile/credits screens, plus an MP4 screen recording. Download the `quem-sou-eu-ios-media-iphone` or `quem-sou-eu-ios-media-ipad` artifact to review the updated catalog. These captures are for QA and layout review; before App Store upload, repeat the store screenshot checklist with the exact signed release build and verify the required App Store Connect dimensions.

## Before Upload

- Confirm the app opens with populated questions and personalities.
- Confirm the result screen is reachable.
- Confirm the version and build number match the build selected in App Store Connect.
- Confirm all screenshots show the same final build.
- Rename files `01-home.png` through `05-profile.png`.
