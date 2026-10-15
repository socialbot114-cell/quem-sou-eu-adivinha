# Benchmark de acertos e erros: 1.2.6 (45)

Gerado em 2026-10-15 por `scripts/evaluate_gameplay.py` (sementes 42, 43 e 44; 523 partidas por semente).

Este benchmark mede o motor de perguntas com as respostas simuladas a partir dos dados do catálogo. Ele não mede a correção dos fatos: a checagem de fatos é a revisão JERV e o validador de conteúdo, descritas no fim.

## Catálogo

- Base publicada (1.2.6 (44)): 505 personagens e 158 perguntas.
- Candidato (1.2.6 (45)): 543 personagens (+38 futebolistas aprovados pelo JERV e pelo portão de Copa do Mundo) e 158 perguntas.
- Correção: Rogério Ceni agora é marcado como campeão da Copa de 2002 (elenco oficial), antes estava como não campeão.

## respostas corretas (`ideal`)

| métrica | base (44) | candidato (45) | Δ |
|---|---:|---:|---:|
| primeiro palpite certo | 98.85% | 98.99% | +0.14 pp |
| acerto final | 100.00% | 100.00% | +0.00 pp |
| acerto até 14 perguntas | 98.41% | 97.50% | -0.91 pp |
| perguntas em média | 8.75 | 9.19 | +0.44 |
| perguntas (p95) | 14.00 | 14.00 | +0.00 |
| jogos sem palpite certo (de 523) | 0.00 | 0.00 | +0.00 |
| palpites rejeitados em média | 0.01 | 0.01 | +0.00 |

## uma resposta 'Não sei' por partida (`one_unknown`)

| métrica | base (44) | candidato (45) | Δ |
|---|---:|---:|---:|
| primeiro palpite certo | 96.43% | 96.08% | -0.35 pp |
| acerto final | 100.00% | 100.00% | +0.00 pp |
| acerto até 14 perguntas | 87.25% | 81.16% | -6.09 pp |
| perguntas em média | 10.33 | 10.86 | +0.53 |
| perguntas (p95) | 15.00 | 18.67 | +3.67 |
| jogos sem palpite certo (de 523) | 0.00 | 0.00 | +0.00 |
| palpites rejeitados em média | 0.03 | 0.04 | +0.01 |

## uma resposta contraditória (`one_contradiction`)

| métrica | base (44) | candidato (45) | Δ |
|---|---:|---:|---:|
| primeiro palpite certo | 91.97% | 91.38% | -0.59 pp |
| acerto final | 100.00% | 100.00% | +0.00 pp |
| acerto até 14 perguntas | 86.04% | 77.84% | -8.21 pp |
| perguntas em média | 12.54 | 13.25 | +0.71 |
| perguntas (p95) | 20.00 | 20.00 | +0.00 |
| jogos sem palpite certo (de 523) | 0.00 | 0.00 | +0.00 |
| palpites rejeitados em média | 0.08 | 0.09 | +0.01 |

## duas respostas contraditórias (`two_contradictions`)

| métrica | base (44) | candidato (45) | Δ |
|---|---:|---:|---:|
| primeiro palpite certo | 73.61% | 71.42% | -2.19 pp |
| acerto final | 98.98% | 98.81% | -0.17 pp |
| acerto até 14 perguntas | 54.94% | 47.12% | -7.82 pp |
| perguntas em média | 14.94 | 15.54 | +0.59 |
| perguntas (p95) | 20.00 | 20.00 | +0.00 |
| jogos sem palpite certo (de 523) | 5.33 | 6.67 | +1.33 |
| palpites rejeitados em média | 0.37 | 0.42 | +0.05 |

## 10% de respostas erradas (aleatórias) (`random_10pct`)

| métrica | base (44) | candidato (45) | Δ |
|---|---:|---:|---:|
| primeiro palpite certo | 73.49% | 74.51% | +1.02 pp |
| acerto final | 95.16% | 94.71% | -0.45 pp |
| acerto até 14 perguntas | 71.96% | 68.92% | -3.03 pp |
| perguntas em média | 12.10 | 12.54 | +0.44 |
| perguntas (p95) | 20.00 | 20.00 | +0.00 |
| jogos sem palpite certo (de 523) | 25.33 | 29.67 | +4.33 |
| palpites rejeitados em média | 0.50 | 0.51 | +0.00 |

## respostas 'provavelmente' (`probably_answers`)

| métrica | base (44) | candidato (45) | Δ |
|---|---:|---:|---:|
| primeiro palpite certo | 99.04% | 99.29% | +0.25 pp |
| acerto final | 100.00% | 100.00% | +0.00 pp |
| acerto até 14 perguntas | 82.79% | 75.64% | -7.15 pp |
| perguntas em média | 13.16 | 13.72 | +0.56 |
| perguntas (p95) | 20.00 | 20.00 | +0.00 |
| jogos sem palpite certo (de 523) | 0.00 | 0.00 | +0.00 |
| palpites rejeitados em média | 0.01 | 0.01 | +0.00 |

## 50% de 'Não sei' (estresse) (`unknown_50`)

| métrica | base (44) | candidato (45) | Δ |
|---|---:|---:|---:|
| primeiro palpite certo | 63.86% | 59.42% | -4.45 pp |
| acerto final | 94.14% | 91.62% | -2.51 pp |
| acerto até 14 perguntas | 29.26% | 27.51% | -1.75 pp |
| perguntas em média | 16.51 | 16.69 | +0.18 |
| perguntas (p95) | 20.00 | 20.00 | +0.00 |
| jogos sem palpite certo (de 523) | 30.67 | 47.00 | +16.33 |
| palpites rejeitados em média | 0.70 | 0.83 | +0.14 |

## Portão de jogo (plano de qualidade, seção 6)

| critério | limite | resultado | situação |
|---|---|---|---|
| acerto final com 10% de erros | não cair mais de 1 ponto | -0.45 pp | passa |
| perguntas médias sem erros | não subir mais de 0,5 | +0.44 | passa |
| primeiro palpite sem erros | pelo menos 98% | 98.99% | passa |
| personagens indistinguíveis | zero | 0 (validador de conteúdo) | passa |

Riscos conhecidos, fora dos critérios do plano:

- Cenário de 50% 'Não sei': jogos sem palpite certo sobem de 30.7 para 47.0.
- Cenário de uma contradição: acerto até 14 perguntas cai 8.2 pontos, embora o acerto final continue em 100%.

## Expectativa mínima no lançamento

- Jogador que responde corretamente: primeiro palpite em 99.0% e acerto final em 100.0% das partidas, com 9.2 perguntas em média.
- Jogador que erra 10% das respostas: acerto final de 94.7%, com 30 partidas em 523 sem palpite certo dentro de 20 perguntas.
- Jogador que responde 'Não sei' em metade das perguntas: acerto final de 91.6%.

## Validação do conteúdo

- `scripts/validate_content.py`: aprovado, 543 personagens, 158 perguntas, 158 atributos e 16 retratos creditados.
- JERV sobre as afirmações principais dos 335 futebolistas candidatos: 330 aceitas com confiança ≥ 0,8 (1 contradita, 1 insuficiente, 3 em revisão). O lote publicado usa 38 delas; as demais ficam para a próxima versão, porque reduzem o acerto no portão de jogo.
- Copa do Mundo: status de campeão verificado pelos elencos oficiais das Copas masculinas (1930 a 2022) e femininas (1991 a 2023) em `docs/content/world-cup-champion-squads.json`.
