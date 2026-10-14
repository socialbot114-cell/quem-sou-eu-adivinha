# Status de validação do catálogo antes da expansão

Auditoria local atualizada em 2026-09-30. Onze respostas com evidência direta foram corrigidas; nenhuma expansão de personagens foi feita.

## Inventário

- 305 personagens: 76 na base principal e 229 na expansão.
- 128 perguntas em 12 categorias.
- 6.541 combinações aplicáveis personagem–pergunta; a base contém 6.542 valores de atributos.
- A expansão atual é reproduzida exatamente pelo gerador: 229 perfis e 72 perguntas, sem diferenças nos dados gerados.
- `scripts/validate_content.py` passa. As regras determinísticas verificadas para ordem das datas de nascimento e coerência entre `alive` e `died_before_1900` não encontraram violações.

## Cobertura de evidências existente

- A matriz anterior cobre 73 perfis e 1.288 células: 73 aceitas pelo JERV e 1.215 encaminhadas para revisão humana. Uma resposta, Ariana Grande / `acted_in_film`, tem adjudicação editorial documentada em `JERV-ANSWER-MATRIX-REVIEW.md`.
- A matriz dos 150 novos perfis cobre 3.141 células: 382 aceitas pelo JERV e 2.759 abaixo do limiar ou sem evidência suficiente. Dez células têm adjudicações manuais em `jerv-answer-matrix-150-adjudications.json`, deixando 2.749 pendentes nesse lote.
- Uma terceira matriz JERV (`jerv-answer-matrix-gap-report.json`) avaliou as 2.112 células que faltavam, cobrindo os 76 perfis principais e os seis perfis da expansão sem matriz. Agora todas as 6.541 células aplicáveis têm uma decisão bruta do JERV.
- Na avaliação JERV mais recente, 741 células foram aceitas pelo modelo; 22 têm adjudicação manual documentada. **5.783 células ainda estão em `human-review` ou aguardam adjudicação.** Aceitação do modelo é um sinal do trecho citado, não uma verificação independente da verdade.
- Onze respostas foram corrigidas com fonte direta. As seis primeiras: Gabriel Jesus / Barcelona; Ivete Sangalo / atuação; Marisa Monte / instrumentista e samba; Camila Loures / publicação de música; Lucas Rangel / plataforma inicial Vine, não YouTube. O follow-up das contradições corrigiu mais cinco: Whindersson Nunes, Felipe Neto, Bianca Andrade e Camila Loures / artista; Felipe Neto / conteúdo de humor.
- O follow-up (`jerv-answer-matrix-contradiction-followup-report.json`) usou trechos biográficos específicos para reavaliar 11 divergências. Quatro contradições seguem sinalizadas: Luva de Pedreiro / futebol e Caetano Veloso, Martin Luther King Jr. e Tiradentes / atividade política. Marta / meio-campo e Neymar / meio-campo continuam em revisão humana por falta de evidência suficiente ou confiança baixa.
- Foram geradas fontes de perfil para os 76 personagens principais em `primary-character-sources.json`. Os 305 perfis têm uma fonte de perfil, mas os trechos são reutilizados entre afirmações e podem não sustentar cada resposta específica.

## Revisão das perguntas

- Os relatórios das matrizes incluem as 128 perguntas. Depois de incorporar as revisões editoriais disponíveis, **18 IDs ainda não têm decisão final consolidada**; a fila completa está em `catalog-validation-queue.json`.
- A revisão editorial final cobre e aceita as 72 perguntas da expansão. As perguntas da base principal precisam de uma decisão consolidada antes do gate de expansão.

## Gate para começar a expansão

**Ainda não liberado.** O JERV avaliou todas as células, mas 5.783 respostas e 18 perguntas ainda precisam de revisão/adjudicação. Antes de expandir, é necessário resolver essas pendências com evidência rastreável e conservar “evidência insuficiente” como desconhecida, nunca como resposta “Não”.

Reexecute `python3 scripts/audit_catalog_evidence.py` para obter o estado consolidado. `--require-complete` falha enquanto o gate estiver fechado.

A fila detalhada gerada nesta auditoria está em [`catalog-validation-queue.json`](catalog-validation-queue.json): contém as 5.783 células pendentes, as 18 perguntas sem decisão final e as evidências associadas. O lote avaliado veio de `jerv-answer-matrix-gap-input.json` e seu resultado está em `jerv-answer-matrix-gap-report.json`; as correções estão registradas em `jerv-answer-matrix-gap-adjudications.json` e `jerv-answer-matrix-contradiction-adjudications.json`.
