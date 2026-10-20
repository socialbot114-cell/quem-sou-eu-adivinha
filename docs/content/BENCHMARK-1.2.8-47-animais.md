# Benchmark: 1.2.8 (47) com animais

Gerado em 2026-10-20. Simulação com `scripts/evaluate_gameplay.py` pelo portão `scripts/run_gate.py`, sementes 42, 43 e 44 (médias).

Comparação: **base publicada 1.2.8 sem animais (773 personagens)** contra **candidato com animais (879 personagens: 773 + 106 animais)**.

Mede o motor com respostas simuladas a partir dos dados do catálogo. Não mede a correção dos fatos: a correção é coberta pelo JERV e pelo validador de conteúdo (`scripts/validate_content.py`).

Veredito do portão: **aprovado**.

## critérios do portão

- acerto final com 10% de erros: base 98.36%, candidato 97.55% (Δ -0.81 pp); limite não cair mais de 1 ponto; PASSA
- perguntas médias no cenário ideal: base 9.11, candidato 9.07 (Δ -0.05); limite não subir mais de 0,5; PASSA
- primeiro palpite no cenário ideal: base 99.49%, candidato 99.55% (Δ +0.06 pp); limite pelo menos 98%; PASSA

## cenários

| cenário | 1º palpite base | 1º palpite cand. | acerto final base | acerto final cand. | perguntas base | perguntas cand. |
|---|---:|---:|---:|---:|---:|---:|
| respostas corretas (ideal) | 99.49% | 99.55% | 100.00% | 100.00% | 9.11 | 9.07 |
| uma 'Não sei' por partida | 98.57% | 98.51% | 100.00% | 100.00% | 10.44 | 10.55 |
| uma resposta contraditória | 89.21% | 90.93% | 100.00% | 100.00% | 13.27 | 13.42 |
| duas respostas contraditórias | 74.13% | 73.51% | 100.00% | 100.00% | 17.12 | 16.95 |
| 10% de respostas erradas (aleatórias) | 76.57% | 75.51% | 98.36% | 97.55% | 13.73 | 13.73 |
| respostas 'provavelmente' | 99.62% | 99.67% | 100.00% | 100.00% | 13.60 | 13.90 |
| 50% de 'Não sei' | 72.10% | 68.60% | 98.19% | 96.77% | 20.87 | 20.53 |

## por que 106 animais e não 278

Com as 278 espécies aceitas pelo JERV, 625 pares de animais diferiam em apenas uma resposta. O gate reprovou (acerto final com 10% de erros caiu 4,9 pontos). Exigindo distância mínima de 2 respostas entre quaisquer dois animais, sobram 106, e o gate passou.
