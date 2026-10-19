# Benchmark: 1.2.8 (47)

Gerado em 2026-10-19. Simulação com `scripts/evaluate_gameplay.py`, sementes 42, 43 e 44, 523 partidas por semente.

Comparação: **1.2.7 (593 personagens, palpite a 0,68)** contra **1.2.8 (773 personagens, palpite a 0,55)**.

Mede o motor com respostas simuladas a partir dos dados do catálogo. Não mede a correção dos fatos (JERV e validador de conteúdo cobrem isso).

## respostas corretas (`ideal`)

| métrica | 1.2.7 (593) | 1.2.8 (773) | Δ |
|---|---:|---:|---:|
| primeiro palpite certo | 99.51% | 99.49% | -0.02 pp |
| acerto final | 100.00% | 100.00% | +0.00 pp |
| perguntas em média | 9.06 | 9.11 | +0.05 |
| jogos sem palpite certo (de 523) | 0.00 | 0.00 | +0.00 |
| palpites rejeitados em média | 0.00 | 0.01 | +0.01 |

## uma 'Não sei' por partida (`one_unknown`)

| métrica | 1.2.7 (593) | 1.2.8 (773) | Δ |
|---|---:|---:|---:|
| primeiro palpite certo | 97.93% | 98.57% | +0.64 pp |
| acerto final | 100.00% | 100.00% | +0.00 pp |
| perguntas em média | 10.63 | 10.44 | -0.19 |
| jogos sem palpite certo (de 523) | 0.00 | 0.00 | +0.00 |
| palpites rejeitados em média | 0.02 | 0.02 | -0.00 |

## uma resposta contraditória (`one_contradiction`)

| métrica | 1.2.7 (593) | 1.2.8 (773) | Δ |
|---|---:|---:|---:|
| primeiro palpite certo | 94.05% | 89.21% | -4.84 pp |
| acerto final | 100.00% | 100.00% | +0.00 pp |
| perguntas em média | 13.07 | 13.27 | +0.20 |
| jogos sem palpite certo (de 523) | 0.00 | 0.00 | +0.00 |
| palpites rejeitados em média | 0.06 | 0.11 | +0.05 |

## duas respostas contraditórias (`two_contradictions`)

| métrica | 1.2.7 (593) | 1.2.8 (773) | Δ |
|---|---:|---:|---:|
| primeiro palpite certo | 79.49% | 74.13% | -5.36 pp |
| acerto final | 100.00% | 100.00% | +0.00 pp |
| perguntas em média | 15.98 | 17.12 | +1.14 |
| jogos sem palpite certo (de 523) | 0.00 | 0.00 | +0.00 |
| palpites rejeitados em média | 0.30 | 0.34 | +0.04 |

## 10% de respostas erradas (`random_10pct`)

| métrica | 1.2.7 (593) | 1.2.8 (773) | Δ |
|---|---:|---:|---:|
| primeiro palpite certo | 79.22% | 76.57% | -2.65 pp |
| acerto final | 99.02% | 98.36% | -0.66 pp |
| perguntas em média | 13.11 | 13.73 | +0.62 |
| jogos sem palpite certo (de 523) | 6.00 | 13.00 | +7.00 |
| palpites rejeitados em média | 0.44 | 0.49 | +0.05 |

## respostas 'provavelmente' (`probably_answers`)

| métrica | 1.2.7 (593) | 1.2.8 (773) | Δ |
|---|---:|---:|---:|
| primeiro palpite certo | 99.67% | 99.62% | -0.05 pp |
| acerto final | 100.00% | 100.00% | +0.00 pp |
| perguntas em média | 13.52 | 13.60 | +0.08 |
| jogos sem palpite certo (de 523) | 0.00 | 0.00 | +0.00 |
| palpites rejeitados em média | 0.00 | 0.00 | +0.00 |

## 50% de 'Não sei' (estresse) (`unknown_50`)

| métrica | 1.2.7 (593) | 1.2.8 (773) | Δ |
|---|---:|---:|---:|
| primeiro palpite certo | 70.59% | 72.10% | +1.51 pp |
| acerto final | 98.74% | 98.19% | -0.56 pp |
| perguntas em média | 19.72 | 20.87 | +1.15 |
| jogos sem palpite certo (de 523) | 7.67 | 14.33 | +6.67 |
| palpites rejeitados em média | 0.67 | 0.69 | +0.02 |

## Portão de jogo (plano, seção 6)

- acerto final com 10% de erros: -0.66 pp (limite: não cair mais de 1 ponto): **passa**
- perguntas médias no cenário ideal: +0.05 (limite: não subir mais de 0,5): **passa**
- primeiro palpite no cenário ideal: 99.49% (mínimo 98%): **passa**
- personagens indistinguíveis: 0 (`validate_content.py`): **passa**

## Conteúdo

- 773 personagens: 505 da base + 50 futebolistas (1.2.7) + 80 futebolistas (futebol-2, perguntas de clube) + 100 futebolistas (futebol-3).
- Todos com afirmação principal aprovada pelo JERV (confiança ≥ 0,8) e Copa do Mundo pelos elencos oficiais.
- Palpite antecipado: a 0,55 em vez de 0,68 (menos perguntas em todos os cenários, sem perda de acerto final).
- Correção do Rogério Ceni (campeão de 2002).
