# Comparação do motor em partidas completas

Data: 2026-10-01. Catálogo avaliado: 305 personagens, 128 perguntas e 323 combinações personagem–categoria, após onze correções de respostas confirmadas por fonte.

`scripts/evaluate_gameplay.py` acompanha uma partida até acertar, perder ou esgotar as quatro rejeições possíveis, como o fluxo em `GameViews.swift`. Os números abaixo são médias das seeds `42`, `43` e `44` (323 partidas por cenário e seed).

## Configurações

- **1.2.3 (anterior):** limite fixo de 14 perguntas, confiança antecipada `0,60`, margem `0,08`, piso de likelihood `0,25`.
- **1.2.4 (adotada):** orçamento adaptativo (`GuessPolicy.questionBudget`): 14 perguntas, +3 por palpite rejeitado, até 2 respostas “Não sei” sem consumir o orçamento, teto de 20; confiança `0,68`, margem `0,10`, piso `0,18`. Também há o botão “Desfazer última resposta”, que o simulador não modela.

Para reproduzir: `python3 scripts/evaluate_gameplay.py --seed 42` (adotada) e `python3 scripts/evaluate_gameplay.py --seed 42 --budget-policy legacy --likelihood-floor 0.25 --guess-confidence 0.60 --margin-threshold 0.08` (anterior).

## Resultados agregados

| Cenário | 1º palpite 1.2.3 → 1.2.4 | Acerto final 1.2.3 → 1.2.4 | Perguntas médias 1.2.3 → 1.2.4 |
|---|---:|---:|---:|
| Ideal | 99,8% → 99,7% | 100,0% → 100,0% | 8,04 → 7,23 |
| Uma resposta desconhecida | 95,9% → 95,6% | 98,0% → 100,0% | 9,72 → 9,04 |
| Uma resposta contraditória | 92,2% → 90,3% | 97,4% → 99,3% | 11,60 → 11,18 |
| Duas respostas contraditórias | 59,9% → 56,4% | 76,0% → 88,1% | 13,02 → 13,02 |
| 10% de respostas contraditórias aleatórias | 75,5% → 75,5% | 83,4% → 95,9% | 10,26 → 9,81 |
| Respostas “provavelmente” | 100,0% → 100,0% | 100,0% → 100,0% | 10,35 → 11,53 |

Nos cenários com respostas erradas o P95 sobe de 14 para 17 perguntas, porque as perguntas extras só aparecem depois de um palpite rejeitado; no cenário ideal o P95 cai para 13.

## Calibração do piso

Com o orçamento adaptativo, pisos mais baixos aceleram a partida, mas derrubam o primeiro palpite quando há respostas erradas:

| Piso / confiança / margem | Perguntas (ideal) | 1º palpite (uma contradição) | Final (duas contradições) | Final (10% aleatórias) |
|---|---:|---:|---:|---:|
| 0,15 / 0,60 / 0,08 | 5,91 | 78,0% | 90,2% | 96,3% |
| 0,20 / 0,60 / 0,08 | 6,81 | 88,3% | 87,6% | 96,2% |
| **0,18 / 0,68 / 0,10** | **7,23** | **90,3%** | **88,1%** | **95,9%** |
| 0,25 / 0,60 / 0,08 | 8,04 | 92,2% | 84,6% | 94,3% |

A configuração adotada mantém o primeiro palpite próximo da 1.2.3 e ganha 12 pontos de acerto final nos cenários com erros.

## Limitações conhecidas

- O jogador simulado erra apenas invertendo a resposta; na prática, “provavelmente” em caso de dúvida é mais comum.
- Na mesma categoria, Alexia Putellas e Aitana Bonmatí não se diferenciam em nenhum atributo, e 117 pares diferem em um único atributo. Preencher esses atributos é o próximo ganho de qualidade.

## Candidata 1.2.5 (429 personagens): publicada por decisão do responsável

Motor da 1.2.4 (piso `0,18`, confiança `0,68`, margem `0,10`, orçamento adaptativo), catálogo com 200 personagens novos e 30 perguntas opcionais. Três sementes, salvo onde indicado.

| Cenário | 1.2.4 1º palpite / final / perguntas | 1.2.5 1º palpite / final / perguntas |
|---|---:|---:|
| Ideal | 99,7% / 100% / 7,2 | 98,9% / 100% / 8,7 |
| Duas respostas contraditórias | 56,4% / 88,1% / 13,0 | 67,8% / 89,9% / 13,7 |
| 10% de respostas contraditórias | 75,5% / 95,9% / 9,8 | 70,7% / 90,0% / 11,5 |

Decomposição do cenário de 10% (semente 42, 1.2.4 = 96,0% final):

| Variante | Final |
|---|---:|
| Personagens antigos + perguntas antigas (1.2.4) | 96,0% |
| Personagens antigos + perguntas novas | 96,3% |
| + 100 jogadores novos | 91,5% |
| + 100 artistas novos | 93,6% |
| 1.2.5 completa | 89,3% |

Conclusão: as perguntas novas não prejudicam; os personagens novos prejudicam, nas duas categorias. Varrer limiares (piso 0,18–0,21, confiança 0,64–0,68, margem 0,10–0,12) não recupera o cenário de 10%: a margem não limita o resultado e o piso mais alto piora o acerto final. A 1.2.5 fica fora da produção até o motor ser ajustado para catálogos maiores e o cenário de 10% voltar a pelo menos 95%.

Decisão registrada em 2026-10-13: o responsável optou por lançar a 1.2.5 com os 200 personagens, aceitando a queda de cerca de 6 pontos no cenário de 10% de respostas erradas e partidas mais longas. O aceite editorial foi feito sem revisão humana completa. Um duplicado (Ricardo Kaká, mesma pessoa que Kaká) foi removido antes do lançamento.

## Correção 1.2.6: o motor não pode desistir

Relato dos jogadores (1.2.5): em várias partidas o jogo terminava sem nunca tentar adivinhar. Causas encontradas e reproduzidas no simulador (`scripts/evaluate_gameplay.py`, que espelha o motor Swift):

1. **Portão de palpite (0,18).** `presentBestGuess()` só mostrava palpite com confiança ≥ 0,18. Abaixo disso, a partida terminava sem palpite. Com muitos candidatos, a confiança fica baixa mesmo quando o líder é o certo.
2. **Orçamento de perguntas parado.** O limite base (14, mais 3 por rejeição e 2 "Não sei" grátis) não acompanha categorias maiores (Futebol tem 27 atributos para centenas de personagens; Artistas, 43). Ao atingir o limite com confiança baixa, a partida desistia.
3. **Pool pequeno de perguntas.** Categorias como Tecnologia, Cinema e Moda têm 17–18 atributos. Depois de ~15 perguntas, não sobra pergunta útil e o jogo desistia.
4. **Rejeição no limite encerrava a partida.** Ao rejeitar um palpite com o orçamento já esgotado, `reject()` terminava o jogo mesmo com candidatos restantes. Foi o bug que mais derrubou partidas perfeitas.

Correções:

- Sempre oferecer o líder enquanto houver candidato (sem portão de confiança).
- Quando a confiança do líder está abaixo de 0,50, o limite de perguntas se estende até o teto de 20 (ou até acabarem os atributos).
- Após uma rejeição, o jogo só encerra se as rejeições acabarem ou se não sobrar candidato. Sem perguntas restantes, oferece o próximo candidato.

Resultados (3 sementes, 429 personagens, 102 perguntas):

| Cenário | Antes: acerto final / perguntas / sem palpite | Depois: acerto final / perguntas / sem palpite |
|---|---:|---:|
| Sem erros | 100,0% / 8,69 / 0 | 100,0% / 8,75 / 0 |
| Uma resposta "Não sei" | 100,0% / 10,20 / 0 | 100,0% / 10,33 / 0 |
| Uma resposta errada | 99,4% / 12,05 / 9 | 100,0% / 12,54 / 0 |
| Duas respostas erradas | 89,8% / 13,71 / 150 | 99,0% / 14,94 / 0 |
| 10% de respostas erradas | 91,0% / 11,47 / 110 | 95,2% / 12,10 / 0 |
| "Provavelmente" coerente | 100,0% / 12,37 / 0 | 100,0% / 13,16 / 0 |
| 50% de "Não sei" | 72,5% / 14,91 / 430 | 94,1% / 16,51 / 0 |

Nenhuma partida termina sem palpite. O custo é de cerca de 0,1 pergunta nas partidas perfeitas e 1,5 com metade de "Não sei".
