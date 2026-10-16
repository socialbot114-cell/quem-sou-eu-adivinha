# Benchmark: 1.2.7 (46)

Gerado em 2026-10-16. Simulação com `scripts/evaluate_gameplay.py`, sementes 42, 43 e 44, 523 partidas por semente.

Comparação feita no **mesmo catálogo** (593 personagens: os 543 publicados em revisão mais 50 futebolistas), mudando só a regra de recuperação:

- regra atual: até 4 palpites rejeitados e teto de 20 perguntas;
- recuperação (1.2.7): até 8 palpites rejeitados e teto de 30 perguntas.

Mede o motor com respostas simuladas a partir dos dados do catálogo. Não mede a correção dos fatos (JERV e validador de conteúdo cobrem isso).

## respostas corretas (`ideal`)

| métrica | regra atual | recuperação (1.2.7) | Δ |
|---|---:|---:|---:|
| primeiro palpite certo | 99.51% | 99.51% | +0.00 pp |
| acerto final | 100.00% | 100.00% | +0.00 pp |
| perguntas em média | 8.99 | 9.06 | +0.08 |
| jogos sem palpite certo (de 523) | 0.00 | 0.00 | +0.00 |
| palpites rejeitados em média | 0.00 | 0.00 | +0.00 |

## uma 'Não sei' por partida (`one_unknown`)

| métrica | regra atual | recuperação (1.2.7) | Δ |
|---|---:|---:|---:|
| primeiro palpite certo | 97.93% | 97.93% | +0.00 pp |
| acerto final | 100.00% | 100.00% | +0.00 pp |
| perguntas em média | 10.43 | 10.63 | +0.20 |
| jogos sem palpite certo (de 523) | 0.00 | 0.00 | +0.00 |
| palpites rejeitados em média | 0.02 | 0.02 | +0.00 |

## uma resposta contraditória (`one_contradiction`)

| métrica | regra atual | recuperação (1.2.7) | Δ |
|---|---:|---:|---:|
| primeiro palpite certo | 94.05% | 94.05% | +0.00 pp |
| acerto final | 100.00% | 100.00% | +0.00 pp |
| perguntas em média | 12.68 | 13.07 | +0.39 |
| jogos sem palpite certo (de 523) | 0.00 | 0.00 | +0.00 |
| palpites rejeitados em média | 0.06 | 0.06 | +0.00 |

## duas respostas contraditórias (`two_contradictions`)

| métrica | regra atual | recuperação (1.2.7) | Δ |
|---|---:|---:|---:|
| primeiro palpite certo | 79.32% | 79.49% | +0.16 pp |
| acerto final | 99.34% | 100.00% | +0.66 pp |
| perguntas em média | 15.18 | 15.98 | +0.80 |
| jogos sem palpite certo (de 523) | 4.00 | 0.00 | -4.00 |
| palpites rejeitados em média | 0.30 | 0.30 | +0.00 |

## 10% de respostas erradas (`random_10pct`)

| métrica | regra atual | recuperação (1.2.7) | Δ |
|---|---:|---:|---:|
| primeiro palpite certo | 78.39% | 79.22% | +0.82 pp |
| acerto final | 94.82% | 99.02% | +4.20 pp |
| perguntas em média | 12.06 | 13.11 | +1.05 |
| jogos sem palpite certo (de 523) | 31.67 | 6.00 | -25.67 |
| palpites rejeitados em média | 0.44 | 0.44 | +0.00 |

## respostas 'provavelmente' (`probably_answers`)

| métrica | regra atual | recuperação (1.2.7) | Δ |
|---|---:|---:|---:|
| primeiro palpite certo | 99.67% | 99.67% | +0.00 pp |
| acerto final | 100.00% | 100.00% | +0.00 pp |
| perguntas em média | 12.91 | 13.52 | +0.61 |
| jogos sem palpite certo (de 523) | 0.00 | 0.00 | +0.00 |
| palpites rejeitados em média | 0.00 | 0.00 | +0.00 |

## 50% de 'Não sei' (estresse) (`unknown_50`)

| métrica | regra atual | recuperação (1.2.7) | Δ |
|---|---:|---:|---:|
| primeiro palpite certo | 66.78% | 70.59% | +3.82 pp |
| acerto final | 92.14% | 98.74% | +6.60 pp |
| perguntas em média | 16.55 | 19.72 | +3.17 |
| jogos sem palpite certo (de 523) | 48.00 | 7.67 | -40.33 |
| palpites rejeitados em média | 0.70 | 0.67 | -0.03 |

## Portão de jogo (plano, seção 6)

- acerto final com 10% de erros: +4.20 pp (limite: não cair mais de 1 ponto): **passa**
- perguntas médias no cenário ideal: +0.08 (limite: não subir mais de 0,5): **passa**
- primeiro palpite no cenário ideal: 99.51% (mínimo 98%): **passa**
- personagens indistinguíveis: 0 (`validate_content.py`): **passa**

O `run_gate.py` recusa comparar políticas diferentes, por isso esta comparação é a A/B direta no mesmo catálogo.

## Conteúdo

- 593 personagens (543 + 50 futebolistas), 214 perguntas, validador aprovado.
- Futebolistas novos: afirmação principal aprovada pelo JERV (confiança ≥ 0,8), Copa do Mundo pelos elencos oficiais, atributos de clube do Wikidata.
- Correção: Rogério Ceni agora é campeão de 2002 (elenco oficial).
