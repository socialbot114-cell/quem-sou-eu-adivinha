# Roadmap para 1.000 personagens

Meta: pelo menos 1.000 personagens no app, todos com afirmação principal aprovada pelo JERV, cobertura de 80% em cada pergunta da categoria, zero colisões e portão de jogo aprovado contra a versão anterior.

Situação inicial (1.2.6 (45), em revisão na App Store): 543 personagens = 505 da base + 38 futebolistas. Faltam 457.

## Restrições medidas

1. **Distinguibilidade.** Cada personagem precisa ser diferente dos outros pelas perguntas úteis da categoria. Futebolistas com só 17 atributos não se separam: com 80 novos, o acerto final em 10% de erros caiu 1,8 ponto; com 330, caiu 8,7.
2. **Cobertura.** Toda pergunta precisa de pelo menos 80% das pessoas da categoria com valor. Uma pergunta com lacunas torna o validador reprovado.
3. **Copa do Mundo.** Campeão sem status verificado não entra. Status vem de `docs/content/world-cup-champion-squads.json`.
4. **JERV.** Aprova a afirmação principal (role) contra o trecho da Wikipédia com confiança ≥ 0,8. Não verifica cada atributo: atributos vêm do Wikidata.
5. **Simulador lento.** Com ~800 pessoas, uma semente leva ~10 min. Rodar as sementes em paralelo.

## Testes e validações

Cada item abaixo precisa passar antes de um lote subir. Os scripts que existem estão indicados.

| # | Teste | Como roda | Critério |
|---|---|---|---|
| T1 | Validação do conteúdo | `scripts/validate_content.py` | passa sem erro |
| T2 | Determinismo do construtor | `build_character_expansion.build()` duas vezes | saídas idênticas |
| T3 | Distinguibilidade por categoria | `scripts/check_wave.py` (a criar) | 0 colisões nas perguntas úteis e 0 no modo Todos |
| T4 | Cobertura por pergunta | `scripts/check_wave.py` (a criar) | ≥ 80% em toda pergunta da categoria |
| T5 | JERV na afirmação principal | `review_character_content.py` (SKIILS/jerv) | aceito com confiança ≥ 0,8, supports |
| T6 | JERV na redação das perguntas novas | mesmo worker, `questions` | aceito (clear, ≥ 0,8) |
| T7 | Fontes | `validate_content.py` | uma fonte por pessoa, texto sem espaços nas bordas |
| T8 | Identidade | nomes e QIDs únicos; sem homônimos | nenhum duplicado |
| T9 | Procedência dos atributos | cada valor vem de uma propriedade Wikidata ou de elenco oficial | registrado em `provenance` |
| T10 | Portão de jogo | `scripts/evaluate_gameplay.py`, sementes 42, 43, 44 | ver seção "Portão" |
| T11 | Avaliação offline | `scripts/evaluate_offline.py` (job da CI) | sem regressão |
| T12 | Testes do motor | `GameEngineTests` (CI) | passa, incluindo o teste de 5.000 pessoas |
| T13 | Auditoria por amostra | 150 aleatórios por lote, checados contra o resumo da Wikipédia | 0 erros críticos (plano, seção 5) |
| T14 | Build e TestFlight | workflows `iOS Build` e `iOS TestFlight` | verde |
| T15 | App Store | `App Store Connect Release` (inspect, depois submit com confirmação exata) | VALID e submetido |

## Portão de jogo

Compara o catálogo candidato com a versão publicada, nas sementes 42, 43 e 44:

- acerto final no cenário de 10% de erros: não cair mais de 1 ponto;
- perguntas médias no cenário ideal: não subir mais de 0,5;
- primeiro palpite no cenário ideal: pelo menos 98%;
- personagens indistinguíveis: zero.

Regressões em cenários de estresse (50% "Não sei", duas contradições) são registradas no benchmark e não bloqueiam sozinhas, mas precisam de explicação.

## Fases

**Fase 0. Ferramentas.** Script `check_wave.py` (T3, T4). Simulador paralelo por semente. Construtor lendo `scripts/character-batch-wave-*.json`.

**Fase 1. Atributos que separam futebolistas.** Clubes frequentes, posições e países de liga como perguntas novas, com valores para os 129 existentes. Meta: +150 futebolistas aprovados.

**Fase 2. Música.** Música internacional e Artistas brasileiros, com gêneros musicais (Wikidata P136) e instrumentos. Meta: +140.

**Fase 3. Cinema e esportes.** Cinema e TV (gênero de filme, franquias, Oscar) e Outros esportes (modalidade, medalhas). Meta: +160.

**Fase 4. Personalidades.** Personalidades mundiais e outros nichos que passarem nos critérios. Meta: +60. Políticos, criadores e tecnologia só entram se o dado for verificável.

**Fase 5. Integração e auditoria.** Um lote por vez, cada um com T1 a T13 e o portão de jogo sobre o catálogo acumulado. Lote que reprova é cortado ou recebe atributos novos antes de voltar.

**Fase 6. Release.** Build 46 ou seguinte, TestFlight, App Store, com a confirmação exata.

## Convenções de trabalho paralelo

- Cada agente escreve só na sua pasta: `docs/content/waves/<nome>/` e `scripts/character-batch-wave-<nome>.json`.
- Nenhum agente altera `iosApp/`, `docs/content/character-sources.json`, `docs/content/jerv-character-review-final.json` ou os scripts de construção existentes.
- Nenhum agente faz commit, push ou envio à App Store.
- Só o integrador (eu) junta os lotes no app, um por vez, com o portão.
- Caches de rede vão para `novos personagens/.cache/`. As chamadas à Wikidata e à Wikipédia são sequenciais, com pausa, por causa do limite de requisições.
- O JERV roda um lote por vez, para não estourar o limite da API.

## Decisões pendentes para você

1. **Revisão humana (T13).** O plano exige revisão humana de 150 por lote. Até você indicar revisor, a auditoria é automatizada e registrada como tal.
2. **Custo do JERV.** Cada lote de ~150 afirmações gera cerca de 13 chamadas à API.
3. **Ordem das categorias.** Esta ordem assume que futebol e música são as mais verificáveis. Se você preferir outra, ajusto.

## Critério de conclusão

Pelo menos 1.000 personagens no app, com T1 a T13 aprovados, portão de jogo aprovado contra a versão anterior e build com a confirmação de submissão.
