# Revisão JERV das respostas

Atualizado em 2026-09-25. A matriz bruta está em [`jerv-answer-matrix-report.json`](jerv-answer-matrix-report.json), com as afirmações e fontes correspondentes em [`jerv-answer-matrix-input.json`](jerv-answer-matrix-input.json).

## Escopo e resultado automático

- 73 personagens da expansão, 62 perguntas e 1.288 células personagem–pergunta.
- JERV aceitou 73 afirmações (confiança ≥ 0,8); 245 respostas receberam “supports”, mas abaixo do limiar; 969 ficaram como evidência insuficiente; e uma foi marcada como contraditória, com baixa confiança (0,14).
- Resultado automático: 73 aceitas e 1.215 para revisão humana. “Evidência insuficiente” significa que o trecho citado não confirma a resposta — não confirma “Não”.
- A revisão de redação das perguntas aceitou 55 e encaminhou 7 para revisão humana.
- O escopo não inclui os 76 personagens anteriores da base principal. Anitta é uma exceção pontual revisada manualmente, não parte desta matriz.

## Adjudicações e correções

- `naomi-campbell--artist`: resposta “Sim” mantida; JERV aceitou com confiança 0,83. A fonte a identifica como modelo e atriz.
- `paris-hilton--fashion_model`: resposta “Sim” corrigida; JERV aceitou com confiança 1,0. A fonte registra que Hilton trabalhou com modelagem de moda.
- `ariana-grande--acted_in_film`: a matriz diz “Sim”. JERV marcou contradição com confiança 0,14, mas a fonte cita sua atuação como Cat Valentine em *Victorious* e *Sam & Cat*. Adjudicação manual: **Sim**; manter a avaliação bruta do JERV e tratar esta célula como resolvida por revisão editorial.
- `anitta` (base principal, fora da matriz): `actor=1` e `presenter=1` foram atualizados. A fonte identifica Anitta como atriz e apresentadora ocasional e registra que ela apresentou uma temporada de *Música Boa Ao Vivo*.
- `tyra-banks--artist`: o valor proposto é “Sim”, mas o suporte do JERV ficou abaixo do limiar (0,30); permanece pendente de revisão junto com a definição da pergunta “É artista?”.

As fontes citadas são páginas da Wikipédia sob CC BY-SA 4.0: [Ariana Grande](https://en.wikipedia.org/wiki/Ariana_Grande), [Naomi Campbell](https://en.wikipedia.org/wiki/Naomi_Campbell), [Paris Hilton](https://en.wikipedia.org/wiki/Paris_Hilton), [Anitta](https://en.wikipedia.org/wiki/Anitta_(singer)) e [Tyra Banks](https://en.wikipedia.org/wiki/Tyra_Banks). O manifesto de fontes registra título, URL, trecho, licença e data de verificação dos perfis da expansão.

## Perguntas encaminhadas para revisão humana

Os sete resultados tiveram decisão “clear”, mas confiança abaixo do limiar de 0,8; portanto, não são reprovações automáticas:

| ID | Pergunta | Confiança |
| --- | --- | ---: |
| `football` | É do futebol? | 0,48 |
| `artist` | É artista? | 0,60 |
| `creator` | É criador de conteúdo digital? | 0,52 |
| `politician` | Exerceu atividade política? | 0,54 |
| `historical` | É uma personalidade histórica? | 0,38 |
| `lifestyle-brand` | Fundou uma marca própria de produtos, moda, beleza ou estilo de vida? | 0,73 |
| `founded-outside-us` | A empresa de tecnologia que fundou tem sede fora dos EUA? | 0,69 |

## Próxima etapa editorial

O restante das 1.214 células automáticas ainda pendentes precisa de fonte mais específica ou adjudicação humana. Priorizar os atributos com mais respostas sem evidência e revisar a base principal separadamente antes de usar esta auditoria como gate de publicação.
