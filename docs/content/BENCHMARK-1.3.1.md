# Benchmark 1.3.1: peso das respostas "Provavelmente"

Simulador `scripts/evaluate_gameplay.py`, 879 personagens (modo Todos sem Animais, Animais com perguntas próprias), seeds 42, 43 e 44, médias.

Mudança: a evidência de "Provavelmente" e "Acho que não" passou de 0,75/0,25 para 0,85/0,15 (`Answer.evidence`).

| Cenário | Antes: 1º palpite / final / perguntas | Depois: 1º palpite / final / perguntas |
|---|---|---|
| ideal | 99,6% / 100% / 9,07 | 99,6% / 100% / 9,09 |
| uma resposta "Não sei" | 98,5% / 100% / 10,55 | 98,5% / 100% / 10,54 |
| uma contradição | 90,9% / 100% / 13,42 | 90,2% / 100% / 13,47 |
| duas contradições | 73,5% / 100% / 16,95 | 73,7% / 100% / 17,02 |
| 10% de respostas erradas | 75,5% / 97,55% / 13,73 | 75,2% / 97,69% / 13,78 |
| só "Provavelmente" | 99,7% / 100% / 13,90 | 99,6% / 100% / 9,79 |
| 50% "Não sei" | 68,6% / 96,77% / 20,53 | 69,2% / 96,81% / 20,58 |

Critérios do portão: acerto final com 10% de erros (+0,14 pp), perguntas ideais (+0,02) e primeiro palpite ideal (99,6%) dentro dos limites. Aprovado.

Testado e descartado (amostra de 1/6 dos personagens): suavizar as notas após um palpite errado (sem efeito), piso de verossimilhança 0,12, 0,14 e 0,25 (trocam perguntas por acerto no primeiro palpite) e oferecer o próximo palpite sem nova pergunta após um erro (14,48 contra 14,47 perguntas).

Limite da simulação: as respostas "Provavelmente" simuladas seguem o valor verdadeiro do atributo. Quem hesita e erra reduz o ganho. O benefício real depende de como as pessoas respondem e deve ser observado no TestFlight.
