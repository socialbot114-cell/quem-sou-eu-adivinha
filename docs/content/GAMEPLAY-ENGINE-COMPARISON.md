# Comparação do motor em partidas completas

Data: 2026-09-30. Catálogo avaliado: 305 personagens, 128 perguntas e 323 combinações personagem–categoria, após seis correções de respostas confirmadas por fonte.

O novo `scripts/evaluate_gameplay.py` acompanha uma partida até acertar, perder ou esgotar as quatro rejeições possíveis. Isso corresponde ao fluxo em `GameViews.swift`; ao contrário da simulação anterior, não encerra a partida no primeiro palpite.

## Configurações

- Referência: confiança antecipada `0.68`, margem `0.10`, piso de likelihood `0.25`.
- Candidata: confiança antecipada `0.60`, margem `0.08`, piso de likelihood `0.25`.
- Três seeds (`42`, `43`, `44`), com 323 partidas por cenário e seed.
- Os cenários introduzem respostas desconhecidas, uma ou duas contradições, 10% de respostas contraditórias aleatórias e respostas “provavelmente”.

## Resultados agregados

| Cenário | Acerto final referência | Acerto final candidata | Perguntas médias referência → candidata |
|---|---:|---:|---:|
| Ideal | 100,0% | 100,0% | 9,19 → 8,04 |
| Uma resposta desconhecida | 98,0% | 98,0% | 10,70 → 9,74 |
| Uma resposta contraditória | 97,3% | 97,5% | 12,27 → 11,65 |
| Duas respostas contraditórias | 73,5% | 75,4% | 13,16 → 13,01 |
| 10% de respostas contraditórias aleatórias | 81,7% | 83,3% | 11,13 → 10,29 |
| Respostas “provavelmente” coerentes com o personagem | 100,0% | 100,0% | 11,55 → 10,38 |

O acerto no primeiro palpite cai cerca de 1,5 ponto percentual com uma contradição e 2,5 pontos com duas; o acerto final aumenta porque a pessoa pode rejeitar o palpite e continuar. A candidata também usa menos perguntas em todos os cenários medidos. O P95 permanece no limite atual de 14 perguntas.

## Próxima validação

Estes números vêm do simulador Python que espelha o motor. Ainda é necessário executar os testes XCTest e o teste UI de recuperação no Simulator macOS antes de escolher estes limiares para a próxima build.
