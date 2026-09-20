# Plano de acao: motor de adivinhacao offline

## 1. Objetivo

Fortalecer o motor atual do **Quem Sou Eu? Adivinha** para que ele identifique a pessoa imaginada de forma clara, consistente e mensuravel, mantendo o aplicativo:

- 100% funcional sem internet;
- sem LLMs, APIs externas ou servicos remotos;
- deterministico quando executado com a mesma base, respostas e semente de teste;
- privado, com dados armazenados somente no aparelho;
- tolerante a respostas incertas, contraditorias ou equivocadas;
- simples de testar e evoluir antes de cada publicacao.

O trabalho deve evoluir o motor probabilistico existente, nao substitui-lo por uma arvore binaria rigida.

## 2. Estado atual

O projeto ja possui uma boa fundacao:

- aplicativo nativo SwiftUI para iOS 17;
- base local em `iosApp/Resources/KnowledgeBase/knowledge.json`;
- candidatos representados por atributos continuos entre `0.0` e `1.0`;
- cinco respostas: sim, provavelmente, nao sei, acho que nao e nao;
- atualizacao probabilistica dos candidatos;
- selecao de perguntas por entropia e ganho de informacao;
- partidas interrompidas salvas localmente;
- historico, pontos, moedas e colecao local;
- testes unitarios do motor e da persistencia.

Arquivos centrais:

- `iosApp/Sources/GameEngine/GameEngine.swift`
- `iosApp/Sources/Views/GameViews.swift`
- `iosApp/Sources/Models/Models.swift`
- `iosApp/Sources/Persistence/ProgressStore.swift`
- `iosApp/Resources/KnowledgeBase/knowledge.json`
- `iosApp/Tests/GameEngineTests.swift`
- `iosApp/Tests/ProgressStoreTests.swift`

## 3. Problemas prioritarios

### 3.1 Encerramento da partida

Atualmente, o motor apresenta um palpite quando a confianca ultrapassa um limite, mas a partida so e concluida depois da confirmacao do usuario. O fluxo precisa impedir qualquer resposta, avancar de pergunta ou registrar resultado depois de uma vitoria ou derrota.

Riscos atuais:

- toque duplo registrar mais de um evento;
- uma acao atrasada mudar a fase depois do resultado;
- pergunta anterior permanecer em memoria durante o palpite;
- partida concluida ser tratada como interrompida;
- comportamento da tela nao estar coberto por testes de estado.

### 3.2 Politica de palpite simplificada

Usar apenas `confidence >= 0.68` nao e suficiente. Um candidato pode ter 68% e o segundo 30%, ou ter 68% e o segundo 67% dependendo da normalizacao e da distribuicao. A qualidade do palpite deve considerar mais de uma medida.

### 3.3 Limite curto e rigido

O limite atual de ate 14 atributos pode forcar um resultado quando ainda existem candidatos muito parecidos. O limite precisa ser uma protecao de duracao, nao o principal criterio para palpitar.

### 3.4 Ausencia de avaliacao completa

Os testes atuais verificam comportamentos isolados, mas nao simulam uma partida para cada personalidade. Sem essa avaliacao, nao existe uma medida objetiva da taxa de acerto ou das pessoas mais dificeis.

### 3.5 Base estatica sem diagnostico de qualidade

O validador atual deve ser ampliado para detectar:

- pessoas indistinguiveis;
- atributos sem cobertura suficiente;
- perguntas que quase nunca reduzem incerteza;
- valores ausentes em excesso;
- perguntas semanticamente repetidas;
- categorias com poucos candidatos ou pouca variacao;
- atributos especificos demais ou amplos demais.

### 3.6 Lacunas validadas no codigo atual (auditoria offline)

Riscos confirmados por leitura direta do codigo, que este plano deve fechar:

| Gap | Risco concreto offline | Local |
|---|---|---|
| soma zero nao recuperada | `apply`/`reject` com `total == 0` deixam escores `0.0`; `bestGuess` retorna pessoa arbitraria em vez de `nil` | `GameEngine.swift:40-48` |
| ausente tratado como `0.5` | 41 atributos com >60% ausentes; 16 artistas com 39/56 omitidos; penalidade de 33% sem dado real | `GameEngine.swift:37,80-86` |
| cobertura sobre massa | pergunta passa com 20% de contagem se a massa estiver concentrada; `nextQuestion` retorna `nil` prematuro no modo Todos | `GameEngine.swift:21-28,60-77` |
| indice aleatorio sem guarda | `chooseCandidateIndex` fora de `[0, count)` causa crash por acesso fora dos limites | `GameEngine.swift:27-28` |
| sem segundo candidato | politica usa so `confidence >= 0.68`; candidatos quase empatados geram falso palpite | `GameEngine.swift:18-19`, `GameViews.swift:255` |
| fase sem `loading` e sem guardas | toque duplo aplica evidencia 2x, duplica `answers` e pode chamar `recordWin` 2x | `GameViews.swift:114-120,250-284` |
| pergunta obsoleta em `confirming` | VoiceOver le card antigo; `persistRound` salva `currentQuestionID` ja respondido | `GameViews.swift:212-221,307-317` |
| limite 14 vs base esparsa | categorias com poucos atributos uteis forcam decisao com confianca baixa | `GameViews.swift:149` |
| salvamento sem versao nem expiracao | base v2 invalida respostas da v1; confianca inflada; partida antiga restaurada | `ProgressModels.swift:18-25`, `GameViews.swift:231-247` |
| rejeicao sem conjunto nem limite | `rejectedPersonIDs` como array duplica; sem `maxRejected` ha loop ate esgotar candidatos | `GameViews.swift:286-296` |
| base vazia silenciosa | `KnowledgeStore` com `try?` retorna base vazia; sem fallback nem erro tipado | `KnowledgeStore.swift:9-18` |
| base 100% binaria `0/1` | sem nuance `0.5`; respostas "Provavelmente" quase nao diferenciam; pares diferem em 1 atributo | `knowledge.json` |
| atributos hierarquicos independentes | `born_before_1970` implica `born_before_1990`, mas o motor trata como independentes | `GameEngine.swift`, `validate_content.py` |
| streak com relogio para tras | mudar o relogio offline congela o streak sem resetar | `ProgressStore.swift:166-179` |
| snapshot corrompido perde tudo | `try? decode` cai para zeros legados e apaga descobertas sem aviso | `ProgressStore.swift:188-222` |
| `categoryHistory` sem limite | apendice infinito offline; `gameHistory` com `removeFirst` O(n) | `ProgressStore.swift:233-263` |

## 4. Principios de arquitetura

### 4.1 Nucleo offline

Todo o ciclo da partida deve funcionar dentro do aplicativo:

```text
knowledge.json local
        |
        v
GameEngine probabilistico
        |
        v
selecao por ganho de informacao
        |
        v
politica de pergunta ou palpite
        |
        v
maquina de estados da partida
        |
        v
persistencia local
```

### 4.2 Separacao de responsabilidades

- `GameEngine`: probabilidades, ranking, entropia e escolha de pergunta.
- `GuessPolicy`: decisao pura sobre perguntar, palpitar ou encerrar sem palpite.
- `GameSession`: estado e transicoes da rodada.
- `ProgressStore`: progresso permanente e partida interrompida.
- `KnowledgeStore`: carregamento e validacao da base embarcada.
- Ferramentas em `scripts/`: auditoria, simulacao e relatorios de desenvolvimento.

Nao e obrigatorio criar todos esses tipos imediatamente. A extracao deve acontecer somente quando facilitar testes e reduzir responsabilidade excessiva da `GameView`.

### 4.3 Motor independente da interface

Regras de jogo nao devem depender de SwiftUI. A interface deve renderizar um estado e enviar uma acao. Isso permite testar a partida sem abrir o Simulator.

### 4.4 Probabilidades nunca invalidas

O motor deve sempre garantir:

- valores finitos;
- probabilidades maiores ou iguais a zero;
- soma normalizada proxima de `1.0` quando existirem candidatos ativos;
- candidato rejeitado com massa nula ou residual controlada;
- nenhum acesso a indice aleatorio fora dos limites;
- comportamento definido quando todos os candidatos forem rejeitados.

### 4.5 Invariantes offline

Todo o motor deve respeitar estes invariantes, verificaveis em testes sem Simulator e sem rede:

- soma dos escores: `1.0 +- 1e-9` quando existir ao menos um candidato nao rejeitado;
- nenhum escore `NaN`, `+Inf` ou `-Inf` apos `apply`, `reject` ou `restore`;
- candidato rejeitado tem escore `0.0` e nunca volta ao ranking na mesma rodada;
- `asked` e `askedAttributes` sao idempotentes: responder a mesma pergunta duas vezes nao duplica evidencia;
- `bestGuess` e `nil` quando todos os candidatos forem rejeitados ou a massa ativa for zero;
- `nextQuestion` nunca retorna pergunta com atributo ja perguntado, ID ja perguntado ou ganho <= 0;
- `chooseCandidateIndex` com indice fora de `[0, count)` usa fallback deterministico ordenado por ID, nunca crash;
- mesma base + mesmas respostas + mesma semente produzem mesma sequencia de perguntas e mesmo palpite;
- nenhuma transicao de estado terminal (`won`, `lost`, `unavailable`) aceita nova resposta;
- nenhuma persistencia de resultado ocorre mais de uma vez por rodada.

Qualquer violacao desses invariantes e tratada como bug critico, mesmo que nao gere crash visivel.

## 5. Fase 1: estabilizar o ciclo da partida

Prioridade: critica.

### 5.1 Tornar os estados explicitos

Estados recomendados:

- `loading`
- `asking(Question)`
- `confirming(Person)`
- `won(Person)`
- `lost(Person?)`
- `unavailable`

Estados `won`, `lost` e `unavailable` sao terminais. Somente uma acao explicita de reinicio pode criar outra rodada.

### 5.2 Definir transicoes permitidas

```text
loading -> asking | unavailable
asking -> asking | confirming | lost
confirming -> won | asking | lost
won -> nova rodada | sair
lost -> nova rodada | sair
unavailable -> sair
```

Qualquer outra transicao deve ser ignorada ou tratada como erro de programacao em testes.

### 5.3 Proteger comandos

- `respond` deve aceitar resposta somente durante `asking` e para a pergunta atual.
- `confirmGuess` deve funcionar somente durante `confirming`.
- `reject` deve funcionar somente para o candidato atualmente apresentado.
- `advance` nao deve executar em estado terminal.
- o resultado deve ser persistido no maximo uma vez.
- botoes devem ser temporariamente bloqueados durante uma transicao.

### 5.4 Limpar estado visual obsoleto

- remover a pergunta atual ao apresentar palpite;
- remover a pergunta ao concluir a partida;
- limpar salvamento interrompido em vitoria ou derrota;
- criar uma nova instancia completa do motor ao reiniciar.

### 5.5 Criterios de aceite

- confirmar um palpite registra exatamente uma vitoria;
- toques repetidos nao alteram pontos ou historico;
- nenhuma pergunta aparece depois da vitoria;
- rejeitar um palpite nunca o apresenta novamente;
- derrota registra exatamente uma partida;
- reabrir o app nao restaura uma partida concluida.

## 6. Fase 2: fortalecer o modelo probabilistico

Prioridade: alta.

### 6.1 Canal de confiabilidade da resposta

Uma resposta humana nao deve ser tratada como evidencia perfeita. O motor deve aplicar uma confiabilidade configuravel, por exemplo:

- `Sim`: evidencia forte, mas nao absoluta;
- `Provavelmente`: evidencia moderada;
- `Nao sei`: registra a pergunta, sem alterar os escores;
- `Acho que nao`: evidencia negativa moderada;
- `Nao`: evidencia negativa forte, mas nao absoluta.

Uma resposta contraditoria nao pode eliminar definitivamente a pessoa correta.

### 6.2 Suavizacao

Adicionar um piso de probabilidade calibrado para evitar colapso numerico. Opcoes a avaliar:

- epsilon fixo pequeno;
- suavizacao baseada na confianca do atributo;
- parametros de amostra por atributo no futuro.

A primeira implementacao deve ser simples, documentada e coberta por testes. Evitar complexidade estatistica que nao produza ganho mensuravel.

### 6.3 Valores ausentes

Hoje, atributo ausente tende a ser tratado como neutro. A politica deve ser explicita:

- valor ausente nao favorece nem pune fortemente;
- perguntas com baixa cobertura devem receber ganho reduzido;
- uma pergunta nao deve ser escolhida se poucos candidatos ativos possuem aquele atributo;
- o relatorio da base deve destacar ausencias relevantes.

### 6.4 Normalizacao robusta

Depois de cada resposta:

- validar soma dos pesos;
- normalizar os candidatos ativos;
- recuperar de soma zero com uma distribuicao segura entre candidatos nao rejeitados;
- impedir `NaN` e infinito;
- preservar rejeicoes.

### 6.5 Ranking completo

O motor deve expor, sem revelar necessariamente na interface:

- melhor candidato;
- segundo candidato;
- lista ordenada dos melhores candidatos;
- confianca normalizada;
- margem absoluta entre primeiro e segundo;
- razao entre primeiro e segundo;
- entropia atual;
- numero efetivo de candidatos.

Numero efetivo sugerido:

```text
effectiveCandidates = 2 ^ entropy
```

### 6.6 Contrato da camada de calibracao local

A base embarcada e imutavel. Qualquer aprendizado local vive em uma camada separada (`CalibrationOverlay`), versionada pelo hash da base:

- arquivo local separado, ex: `CalibrationOverlay.json`, com `knowledgeHash`, `knowledgeVersion` e `updatedAt`;
- ajuste somente apos `minObservations = 5` confirmacoes para o mesmo par pessoa/pergunta;
- magnitude maxima por ajuste: `maxDelta = 0.06`, sempre dentro de `[0.0, 1.0]`;
- peso da base original sempre maior que o peso das observacoes locais;
- partidas nao confirmadas, abandonadas ou com multiplas rejeicoes sem resposta correta nunca alimentam a calibracao;
- calibracao expira ou e invalidada quando `knowledgeHash` muda; opcionalmente expira em 7 dias sem uso;
- botao "Apagar aprendizado local" remove o overlay sem tocar na base;
- chave de configuracao "Melhorar palpites neste aparelho", desligada por padrao ate o motor estavel;
- nenhum dado sai do aparelho; nenhum identificador pessoal e armazenado.

## 7. Fase 3: politica inteligente de palpite

Prioridade: alta.

### 7.1 Remover dependencia de um unico limite

A decisao deve combinar:

- quantidade de perguntas respondidas;
- confianca do primeiro candidato;
- margem para o segundo candidato;
- razao entre primeiro e segundo;
- entropia atual;
- numero efetivo de candidatos;
- ganho esperado da proxima pergunta;
- quantidade de palpites rejeitados;
- limite maximo de seguranca.

### 7.2 Politica inicial sugerida

Os valores devem ser calibrados pelo simulador, nao tratados como definitivos.

```text
Palpitar cedo quando:
- existem evidencias suficientes;
- primeiro candidato tem alta confianca;
- margem para o segundo e clara;
- numero efetivo de candidatos esta baixo.

Continuar perguntando quando:
- existe pergunta com ganho relevante;
- primeiro e segundo candidatos estao proximos;
- ha poucas respostas informativas.

Forcar decisao quando:
- atingiu o limite maximo;
- nao existe pergunta util;
- todos os atributos relevantes ja foram usados.
```

### 7.2b Tabela de decisao (valores iniciais, calibrar via simulador)

Valores abaixo sao ponto de partida, nao definitivos. O simulador da Fase 6 deve calibrar cada limite por categoria.

| Condicao | Acao |
|---|---|
| `informativeAnswers < 4` | perguntar, nunca palpitar |
| `confidence >= 0.78` E `margin >= 0.22` E `ratio >= 3.0` E `effectiveCandidates <= 3.5` E `nextIG < 0.08` | palpitar |
| `confidence >= 0.68` mas `margin < 0.10` ou `ratio < 1.5` | perguntar (lideranca fraca) |
| `effectiveCandidates > 6.0` ou `entropy > 2.6` | perguntar, mesmo com confianca alta |
| existe pergunta com `IG >= 0.08` e `informativeAnswers < maxQuestions` | perguntar |
| `rejectedGuesses >= 4` | encerrar com derrota e abrir fluxo da Fase 9 |
| `informativeAnswers >= maxQuestions` ou `nextQuestion == nil` | decisao forcada: palpite se `confidence >= 0.18`, senao derrota |
| `unknownStreak >= 3` | continuar perguntando, sem liberar palpite cedo |

Definicoes:

```text
margin = top1 - top2
ratio = top1 / max(top2, 1e-9)
effectiveCandidates = 2 ^ entropy
nextIG = ganho esperado da melhor pergunta disponivel
informativeAnswers = respostas diferentes de "Nao sei"
maxQuestions = limite de seguranca (avaliar 20 a 24)
```

### 7.3 Tratamento de `Nao sei`

`Nao sei` deve contar como pergunta exibida, mas nao como evidencia suficiente para liberar um palpite cedo. Manter separadamente:

- perguntas exibidas;
- respostas informativas;
- respostas desconhecidas.

### 7.4 Rejeicao de palpites

- candidato rejeitado nao pode retornar na mesma rodada;
- apos rejeicao, recalcular ranking e entropia;
- continuar com uma pergunta util quando houver;
- apresentar o proximo palpite apenas com evidencia suficiente;
- limitar palpites rejeitados para evitar loop infinito;
- depois do limite, pedir ao usuario que informe quem era ou encerrar claramente.

### 7.5 Limite de duracao

Avaliar um limite entre 20 e 24 perguntas. O numero final deve considerar:

- taxa de acerto;
- duracao media;
- cansaco do usuario;
- quantidade de atributos disponiveis por categoria.

### 7.6 Explicacao simples ao usuario

Mensagens devem indicar o estado real:

- alta confianca: "Acho que descobri!"
- duvida entre candidatos: "Estou entre algumas pessoas. Mais uma pista!"
- base insuficiente: "Ainda nao tenho pistas suficientes."
- limite atingido: "Nao consegui descobrir desta vez."

Nao exibir percentuais tecnicos na experiencia principal. Eles podem existir em modo de diagnostico.

## 8. Fase 4: melhorar selecao de perguntas

Prioridade: alta.

### 8.1 Ganho de informacao esperado

Manter Shannon Entropy e Expected Information Gain como base. Revisar o calculo para garantir que:

- probabilidades das respostas simuladas estejam normalizadas;
- `Nao sei` nao seja tratado como uma divisao informativa;
- cobertura seja calculada sobre a massa probabilistica ativa;
- candidatos rejeitados nao influenciem a escolha;
- perguntas com ganho quase zero sejam descartadas.

### 8.2 Desempate deterministico

Em producao, uma pequena variacao entre perguntas equivalentes pode melhorar repetibilidade da experiencia, mas testes precisam ser deterministas.

Implementar:

- gerador de indice injetavel;
- validacao do indice retornado;
- criterio secundario estavel por ID em testes;
- opcionalmente uma semente local por rodada.

### 8.3 Penalidades de qualidade

O escore de pergunta pode considerar:

- cobertura do atributo;
- clareza definida na base;
- frequencia recente da pergunta;
- especificidade excessiva no inicio da partida;
- redundancia com atributos ja perguntados.

Adicionar apenas criterios que possam ser medidos pelo avaliador.

### 8.4 Perguntas amplas e especificas

Diretriz para a base:

- aproximadamente 40% a 50% de perguntas amplas;
- perguntas intermediarias para separar grupos proximos;
- menos de 10% de perguntas extremamente especificas;
- perguntas especificas usadas somente quando a massa probabilistica estiver concentrada no grupo correspondente.

## 9. Fase 5: auditoria da base de conhecimento

Prioridade: alta.

### 9.1 Validacoes estruturais

Ampliar `scripts/validate_content.py` para verificar:

- IDs unicos e estaveis;
- nomes nao vazios;
- categorias validas;
- valores de atributos entre `0.0` e `1.0`;
- referencias de perguntas para atributos existentes;
- texto de pergunta nao vazio;
- imagens referenciadas existentes;
- quantidade minima de pessoas por categoria;
- quantidade minima de atributos discriminativos.

### 9.2 Validacoes estatisticas

Gerar alertas para:

- atributo quase sempre igual;
- atributo ausente na maior parte dos candidatos;
- pares de pessoas com vetores muito semelhantes;
- pessoa sem atributos suficientes;
- pergunta com baixo ganho medio;
- categoria com baixa separabilidade;
- valor `0.5` usado em excesso;
- candidato que nunca aparece entre os primeiros resultados.

### 9.3 Matriz de similaridade

Produzir um relatorio dos pares mais dificeis de distinguir. Para cada par:

- listar atributos iguais ou proximos;
- listar atributos que os diferenciam;
- indicar se existe uma pergunta para cada atributo diferenciador;
- sugerir revisao manual quando nao houver separacao suficiente.

### 9.4 Governanca do conteudo

Cada mudanca na base deve incluir:

- fonte confiavel para fatos objetivos;
- revisao de categoria;
- execucao do validador;
- execucao do simulador;
- comparacao das metricas antes e depois;
- verificacao de licenca e credito da imagem.

## 10. Fase 6: simulador e avaliacao automatizada

Prioridade: critica para evoluir o motor com seguranca.

### 10.1 Simulacao por personalidade

Criar testes ou uma ferramenta que selecione cada pessoa como alvo e responda automaticamente usando os atributos da propria base.

Executar cenarios:

- respostas ideais;
- uma resposta `Nao sei`;
- varias respostas `Nao sei`;
- uma resposta contraditoria;
- respostas `Provavelmente`;
- rejeicao acidental do primeiro palpite;
- restauracao de partida interrompida.

### 10.2 Metricas obrigatorias

- taxa de acerto no primeiro palpite;
- taxa de acerto total;
- media, mediana e percentil 95 de perguntas;
- quantidade de palpites errados por partida;
- taxa de partidas sem palpite;
- taxa de repeticao de pergunta ou atributo;
- desempenho por categoria;
- pessoas nunca identificadas;
- pares frequentemente confundidos.

### 10.3 Relatorio reproduzivel

O avaliador deve gerar JSON e um resumo legivel, por exemplo:

```text
Pessoas avaliadas: 76
Acerto no primeiro palpite: 92%
Acerto total: 98%
Media de perguntas: 9,4
P95 de perguntas: 17
Perguntas repetidas: 0
Pessoas sem identificacao: 2
```

O relatorio JSON deve conter, no minimo:

```json
{
  "knowledgeHash": "sha256-da-base",
  "knowledgeVersion": "2026.09.19",
  "seed": 42,
  "summary": {
    "total": 76,
    "firstGuessAccuracy": 0.92,
    "totalAccuracy": 0.98,
    "meanQuestions": 9.4,
    "p95Questions": 17
  },
  "perPerson": [
    {
      "target": "neymar",
      "category": "Futebol",
      "scenario": "ideal",
      "questions": 9,
      "firstGuess": "neymar",
      "wrongGuesses": 0,
      "trace": [
        { "question": "q-male", "answer": "Sim", "top1": "neymar", "top2": "vinicius-junior", "margin": 0.12 }
      ]
    }
  ],
  "failures": [
    { "target": "lula", "confusedWith": "dilma-rousseff", "reason": "margin < 0.05" }
  ]
}
```

Cada falha deve registrar pessoa alvo, categoria, sequencia de perguntas, respostas, ranking a cada etapa, palpite apresentado e semente usada, para virar caso de teste reproduzivel.

### 10.4 Metas iniciais

Metas sugeridas para uma versao candidata:

- 100% das personalidades executadas no simulador;
- zero travamentos e loops;
- zero repeticoes de candidato rejeitado;
- zero perguntas repetidas por atributo;
- pelo menos 90% de acerto no primeiro palpite com respostas ideais;
- pelo menos 95% de acerto total com respostas ideais;
- degradacao controlada com uma resposta contraditoria;
- media inferior a 15 perguntas;
- nenhuma categoria abaixo do limite minimo definido pela equipe.

As metas devem ser ajustadas depois da primeira medicao real.

## 11. Fase 7: testes automatizados

### 11.1 Testes do motor

Adicionar cobertura para:

- normalizacao depois de cada resposta;
- ausencia de `NaN` e infinito;
- resposta desconhecida nao altera ranking;
- resposta contraditoria nao elimina definitivamente o alvo;
- pergunta escolhida tem ganho positivo;
- atributo nao se repete;
- candidato rejeitado sai do ranking de palpites;
- rejeitar todos os candidatos produz estado definido;
- segundo candidato e margem corretos;
- entropia diminui em um caso informativo;
- indice aleatorio invalido nao causa crash.

### 11.2 Testes da politica de palpite

- nao palpita sem evidencia minima;
- palpita quando lideranca e clara;
- continua perguntando quando os dois primeiros estao proximos;
- respeita limite maximo;
- nao usa apenas numero de perguntas como sinal de confianca;
- `Nao sei` nao libera palpite prematuro;
- rejeicao muda a decisao seguinte.

### 11.3 Testes da sessao

- fluxo completo de vitoria;
- fluxo completo de derrota;
- confirmacao duplicada registra uma unica vitoria;
- resposta duplicada e ignorada;
- acao atrasada nao altera estado terminal;
- reinicio cria uma rodada limpa;
- restauracao recompõe perguntas, respostas e rejeicoes;
- partida concluida nao e restaurada.

### 11.4 Testes da persistencia

- salvar e restaurar versoes compativeis;
- limpar partida ao concluir;
- limitar historico;
- migrar dados antigos;
- lidar com snapshot corrompido sem quebrar o app.

### 11.5 Testes de interface

Adicionar testes de UI para o caminho principal:

- iniciar categoria;
- responder uma pergunta;
- chegar ao palpite;
- confirmar acerto;
- verificar tela de vitoria;
- reiniciar;
- sair e continuar partida;
- testar VoiceOver e tamanhos grandes de texto.

### 11.6 Matriz de cobertura (teste -> arquivo alvo -> criterio)

| Teste | Arquivo alvo | Passa quando |
|---|---|---|
| `testScoresSumToOneAfterApply` | `GameEngine.swift:34-42` | soma `1.0 +- 1e-9`, sem `NaN/Inf` |
| `testContradictoryAnswerKeepsTargetAlive` | `GameEngine.swift:80-86` | alvo com 1 resposta contraria mantem massa `> 0` |
| `testUnknownDoesNotChangeScores` | `GameEngine.swift:34-36` | escores identicos, mas pergunta marcada como feita |
| `testMissingAttributeIsNeutral` | `GameEngine.swift:37` | ausente retorna verossimilhanca uniforme, nao penaliza |
| `testInformationGainPositiveForUseful` | `GameEngine.swift:60-78` | pergunta util tem ganho `> 0.001`, inutil tem `0` |
| `testNoRepeatedAttribute` | `GameEngine.swift:21-32` | 50 rodadas sem repetir atributo |
| `testInvalidRandomIndexFallback` | `GameEngine.swift:27-28` | indice `-1` ou `>= count` nao crasha |
| `testRejectAllReturnsNilGuess` | `GameEngine.swift:18,44-49` | rejeitar todos retorna `bestGuess == nil` |
| `testSecondBestMarginRatioEntropy` | `GameEngine.swift:18-19` | margem, razao, entropia e efetivos corretos |
| `testGuessPolicyEarlyVsLate` | `GuessPolicy` (Fase 3) | sem evidencia nao palpita; lideranca clara palpita |
| `testDoubleConfirmRecordsOneWin` | `GameViews.swift:278-284` | 2 toques rapidos geram 1 vitoria |
| `testAnswerAfterTerminalIgnored` | `GameViews.swift:250-305` | resposta apos `won/lost` ignorada |
| `testRejectedNeverReturns` | `GameViews.swift:286-296` | rejeitado nao reaparece na rodada |
| `testCompletedRoundNotRestored` | `ProgressStore.swift:115-118` | apos vitoria, `interruptedRound == nil` |
| `testStaleRoundInvalidated` | `ProgressModels.swift:18-25` | hash divergente ou expirado invalida salvamento |
| `testCorruptedSnapshotRecovers` | `ProgressStore.swift:188-222` | snapshot corrompido nao perde tudo sem aviso |
| `testFullCatalogSimulation` | simulador Fase 6 | 76/76 sem crash, metricas geradas |

## 12. Fase 8: aprendizado local seguro

Prioridade: posterior a estabilidade e avaliacao.

O aprendizado deve ser opcional, local e conservador. O aplicativo nao deve alterar diretamente a base embarcada.

### 12.1 Dados locais possiveis

- quantidade de vezes que uma pergunta foi exibida;
- quantidade de `Nao sei` por pergunta;
- candidato confirmado ao final;
- respostas dadas em partidas confirmadas;
- candidatos rejeitados;
- numero de perguntas ate o acerto;
- versao da base usada na partida.

### 12.2 Camada de calibracao

Manter a base original imutavel e salvar ajustes em uma camada local separada. Regras:

- exigir varias observacoes antes de ajustar;
- limitar a magnitude de cada ajuste;
- ponderar base original mais fortemente;
- ignorar partidas nao confirmadas;
- permitir apagar toda a calibracao;
- invalidar ou migrar calibracao quando a base mudar;
- nunca sincronizar sem consentimento e implementacao futura explicita.

### 12.3 Protecao contra dados ruins

- detectar sessoes muito contraditorias;
- nao aprender com rodadas abandonadas;
- nao aprender quando o usuario rejeita varios candidatos sem informar o correto;
- limitar influencia de repeticoes consecutivas;
- armazenar agregados, nao um perfil pessoal do jogador.

### 12.4 Transparencia

Se implementado, incluir em ajustes:

- "Melhorar palpites neste aparelho";
- explicacao de que nenhum dado sai do iPhone;
- botao "Apagar aprendizado local".

## 13. Fase 9: quando o motor nao acerta

O fracasso precisa gerar um encerramento claro, nao um loop.

Fluxo recomendado:

1. O motor atinge o limite ou esgota perguntas uteis.
2. Exibe que nao conseguiu descobrir.
3. Permite escolher a pessoa correta em uma lista local filtravel.
4. Se a pessoa existir, registra uma correcao local para diagnostico/calibracao.
5. Se nao existir, permite registrar apenas um nome como sugestao local.
6. A rodada termina e o usuario pode jogar novamente.

Nao adicionar automaticamente uma nova pessoa a base ativa. Novas pessoas precisam de atributos, categoria, revisao e imagem licenciada.

### 13.1 UX do fracasso (componente local)

Quando o motor nao acerta, exibir um componente local `CorrectPersonPicker`:

- lista filtrtravel por nome, categoria e profissao, 100% local;
- ao escolher a pessoa correta, registrar correcao local para diagnostico/calibracao (somente se opt-in da Fase 8);
- se a pessoa nao estiver na lista, permitir apenas "sugerir nome" local, sem criar pessoa ativa;
- sempre encerrar a rodada em `lost`, com botoes "Jogar novamente" e "Escolher outra categoria";
- nunca entrar em loop de novas perguntas apos o limite.

## 14. Fase 10: ferramentas de diagnostico

### 14.1 Modo de depuracao

Somente em builds de desenvolvimento, permitir visualizar:

- ranking dos cinco melhores candidatos;
- confianca e margem;
- entropia;
- ganho de informacao da pergunta atual;
- perguntas ja utilizadas;
- candidatos rejeitados;
- motivo pelo qual o motor decidiu perguntar ou palpitar.

Essas informacoes nao devem aparecer para usuarios na versao da App Store.

### 14.2 Grafo de diagnostico

Criar script opcional que gere DOT/Graphviz com:

- perguntas mais selecionadas nas simulacoes;
- caminhos comuns por categoria;
- pares de candidatos confundidos;
- nos com baixo ganho de informacao.

Graphviz sera uma ferramenta de desenvolvimento, nao uma dependencia do aplicativo.

### 14.3 Reprodutibilidade

Cada falha encontrada no simulador deve registrar:

- pessoa alvo;
- categoria;
- sequencia de perguntas;
- respostas;
- ranking a cada etapa;
- palpite apresentado;
- semente usada no desempate.

Isso transforma cada erro em um caso de teste reproduzivel.

## 15. Fase 11: experiencia, acessibilidade e clareza

### 15.1 Progresso real

O indicador deve diferenciar:

- perguntas respondidas;
- limite maximo de seguranca;
- estado de investigacao;
- momento do palpite.

Evitar exibir "Pergunta 15 de 14" ou manter numero de pergunta durante a tela de resultado.

### 15.2 Prevencao de toque duplicado

- desabilitar botoes imediatamente apos toque;
- aplicar transicao atomica de estado;
- manter areas de toque acessiveis;
- testar toques rapidos no Simulator e aparelho.

### 15.3 VoiceOver e voz opcional

- rotulos completos para pergunta e respostas;
- anunciar mudanca para palpite, vitoria ou derrota;
- ordem de foco previsivel;
- suporte a Dynamic Type;
- no futuro, leitura opcional com `AVSpeechSynthesizer`, totalmente local.

### 15.4 Feedback

- haptico de pergunta somente quando necessario;
- sucesso uma unica vez;
- erro/derrota uma unica vez;
- animacoes respeitando `Reduce Motion`;
- textos sem prometer certeza quando o motor ainda esta inseguro.

## 16. Fase 12: desempenho e confiabilidade

Com a base atual, o calculo pode permanecer em memoria. Mesmo assim, medir:

- tempo para escolher a proxima pergunta;
- tempo para aplicar uma resposta;
- consumo de memoria ao carregar a base;
- tempo de inicializacao da primeira partida;
- desempenho em aparelhos iPhone mais antigos suportados pelo iOS 17.

Metas sugeridas:

- resposta visual imediata;
- selecao de pergunta sem bloquear a interface;
- nenhuma operacao de rede;
- base carregada uma vez e reutilizada;
- simulacao completa executavel no CI.

Se a base crescer muito, avaliar calculos fora da `MainActor`, preservando atualizacoes de interface no ator principal.

## 17. Privacidade e seguranca

- nenhuma permissao de rede necessaria para jogar;
- nenhum identificador de publicidade;
- nenhum rastreamento;
- nenhum texto do usuario enviado para terceiros;
- progresso e calibracao armazenados localmente;
- arquivos persistidos com tamanho limitado;
- decodificacao tolerante a dados corrompidos;
- politica de privacidade atualizada se o aprendizado local for adicionado.

## 18. Itens fora do escopo

Nao incluir no nucleo atual:

- LLM para criar perguntas ou decidir palpites;
- API do Akinator ou servico equivalente;
- backend obrigatorio;
- conta de usuario;
- banco remoto;
- telemetria invasiva;
- aprendizado automatico global sem moderacao;
- copia direta de codigo GPL ou AGPL para o app;
- arvore binaria rigida como substituta do motor probabilistico.

Conceitos de projetos externos podem orientar a implementacao, mas todo codigo deve ser proprio e compativel com a licenca do aplicativo.

## 19. Ordem de implementacao

### Marco 1: partida confiavel

- corrigir maquina de estados;
- impedir eventos duplicados;
- limpar estado terminal;
- testar vitoria, derrota, rejeicao e reinicio.

Resultado esperado: o jogo sempre termina corretamente.

### Marco 2: motor mensuravel

- expor ranking, margem e entropia;
- robustecer normalizacao;
- adicionar politica composta de palpite;
- ampliar testes unitarios.

Resultado esperado: o motor explica internamente por que perguntou ou palpitou.

### Marco 3: avaliacao completa

- simular todas as pessoas;
- gerar metricas por categoria;
- registrar casos de falha;
- definir baseline de qualidade.

Resultado esperado: toda mudanca pode ser comparada objetivamente.

### Marco 4: qualidade da base

- ampliar validador;
- corrigir pares indistinguiveis;
- melhorar cobertura;
- revisar perguntas de baixo ganho.

Resultado esperado: aumento de acerto sem depender de limites artificiais.

### Marco 5: experiencia final

- mensagens claras;
- acessibilidade;
- testes de UI;
- validacao em aparelho real;
- revisao de privacidade e App Store.

Resultado esperado: versao pronta para TestFlight.

### Marco 6: aprendizado local opcional

- coletar somente agregados locais;
- criar camada de calibracao separada;
- permitir desativar e apagar;
- validar ganho no simulador antes de liberar.

Resultado esperado: melhoria gradual sem comprometer privacidade ou base original.

## 20. Checklist de liberacao

Antes de publicar uma nova versao:

- [ ] Projeto compila em configuracao Debug e Release.
- [ ] Todos os testes unitarios passam.
- [ ] Todos os testes de persistencia passam.
- [ ] Simulador executa todas as personalidades.
- [ ] Metricas nao pioram em relacao ao baseline aprovado.
- [ ] Nenhum candidato rejeitado reaparece.
- [ ] Nenhuma pergunta ou atributo se repete na rodada.
- [ ] Vitoria e derrota sao registradas uma unica vez.
- [ ] Partida concluida nao e restaurada.
- [ ] Partida interrompida e restaurada corretamente.
- [ ] Base de conhecimento passa no validador.
- [ ] Imagens e creditos passam na auditoria.
- [ ] Fluxo completo e testado no Simulator.
- [ ] Fluxo completo e testado em iPhone real.
- [ ] VoiceOver e Dynamic Type foram verificados.
- [ ] Modo aviao foi usado no teste final.
- [ ] Nenhuma funcionalidade principal depende de internet.

### 20.1 Comandos executaveis do checklist

```sh
# 1. Validar conteudo e midia
python3 scripts/validate_content.py

# 2. Gerar projeto e compilar Debug (sem assinatura)
cd iosApp
xcodegen generate
xcodebuild -project QuemSouEu.xcodeproj -scheme QuemSouEu -sdk iphonesimulator -configuration Debug build CODE_SIGNING_ALLOWED=NO

# 3. Testes unitarios e de persistencia
xcodebuild -project QuemSouEu.xcodeproj -scheme QuemSouEu -sdk iphonesimulator -destination 'platform=iOS Simulator,name=iPhone 15' test CODE_SIGNING_ALLOWED=NO

# 4. Simulador offline completo (Fase 6, quando implementado)
swift test --filter OfflineSimulatorTests
# ou: python3 scripts/evaluate_offline.py --seed 42 --report eval.json

# 5. Comparar com baseline aprovado
python3 scripts/compare_baseline.py --current eval.json --baseline baselines/aprovado.json

# 6. Teste final em modo aviao: ativar modo aviao no aparelho/Simulator e repetir o fluxo
# Jogar -> palpite -> Acertou! -> vitoria -> jogar novamente -> sair e continuar partida
```

## 21. Definicao de pronto

O fortalecimento principal do motor estara concluido quando:

1. Toda rodada chegar a um estado terminal claro.
2. Um resultado for persistido exatamente uma vez.
3. A politica de palpite usar confianca, margem e incerteza.
4. Palpites rejeitados nao se repetirem.
5. Todas as pessoas forem avaliadas automaticamente.
6. Os principais casos de ruido forem cobertos por testes.
7. A base possuir relatorio de cobertura e separabilidade.
8. O jogo funcionar integralmente em modo aviao.
9. Nenhum LLM, API ou servico remoto for necessario.
10. As metricas minimas acordadas forem atingidas por categoria e no total.

## 22. Referencias conceituais avaliadas

- `Aaklon/akinator`: estado probabilistico, EIG, suavizacao e aprendizado moderado.
- `Mohammed-Darrige/ai-akinator`: belief state, margem entre candidatos, numero efetivo de candidatos e avaliacao reproduzivel.
- `leagerl1/Akinator`: arvore classica como referencia didatica e de visualizacao, nao como substituta do motor.
- `Mikipaw/Akinator`: Graphviz e voz como ferramentas opcionais de diagnostico e acessibilidade.
- projetos web semelhantes: separacao entre interface, estado da sessao e base de conhecimento.

As referencias servem para comparar abordagens. A implementacao do aplicativo deve continuar nativa, offline e propria.

## 23. Apendice A: catalogo de modos de falha offline

Cada falha abaixo e reproduzivel sem internet e deve virar caso de teste.

| # | Falha | Reproducao | Mitigacao | Teste |
|---|---|---|---|---|
| F1 | soma zero apos rejeicoes | rejeitar todos os 76 candidatos | redistribuir `1/N` sobre nao-rejeitados; `bestGuess == nil` | `testRejectAllReturnsNilGuess` |
| F2 | underflow apos muitas respostas | 20 respostas contraditorias seguidas | espaco logaritmico + `epsilon = 1e-9` + clamp finito | `testScoresStayFiniteAfterManyAnswers` |
| F3 | crash por indice invalido | injetar `randomIndex = { _ in 99 }` | `guard 0..<count` + fallback ordenado por ID | `testInvalidRandomIndexFallback` |
| F4 | duplo toque confirma 2 vitorias | 2 toques em "Acertou!" em <300ms | `isTransitioning` + `.disabled` + guarda de fase | `testDoubleConfirmRecordsOneWin` |
| F5 | resposta apos vitoria | responder pergunta antiga apos `won` | guardas `canRespond` por estado + ID da pergunta | `testAnswerAfterTerminalIgnored` |
| F6 | pergunta obsoleta salva | confirmar palpite e reler `currentQuestionID` | `question = nil` em `presentBestGuess`/`won`/`lost` | `testQuestionClearedOnGuess` |
| F7 | restauracao de base antiga | salvar na v1, atualizar para v2, reabrir | `knowledgeHash` + `expiresAt 7d`; invalidar divergente | `testStaleRoundInvalidated` |
| F8 | `nil` prematuro no modo Todos | jogar Todos com atributos esparsos | cobertura por contagem + minimo; limite 20-24 como protecao | `testSparseCategoryKeepsAsking` |
| F9 | base vazia ou corrompida | `knowledge.json` ausente ou invalido | `do/catch` com erro tipado + tela `unavailable` | `testEmptyBaseShowsUnavailable` |
| F10 | relogio do aparelho para tras | concluir hoje, voltar relogio 2 dias, concluir | `completedDay < previousDay` zera streak para 1 | `testClockRollbackResetsStreak` |
| F11 | snapshot corrompido | gravar bytes aleatorios em `progress.snapshot.v1` | backup + reset seletivo + aviso, sem perder tudo silenciosamente | `testCorruptedSnapshotRecovers` |
| F12 | rejeicao infinita | rejeitar 10 palpites seguidos | `Set` + `maxRejected = 4` + fluxo da Fase 9 | `testRejectLimitEndsRound` |

## 24. Correcoes de codigo propostas (ordem de risco, sem mudar o modelo)

Fase 0, sem alterar a matematica do produto:

1. `GameEngine.swift:27`: `guard` no indice + fallback deterministico.
2. `GameEngine.swift:40-48`: normalizacao robusta com `finite`, redistribuicao sobre nao-rejeitados, `rejectedSet: Set<String>`.
3. `GameEngine.swift:37`: ausente com verossimilhanca uniforme + `coverageCount` por contagem.
4. `GameEngine.swift:21-28`: cache de `informationGain` em `nextQuestion`.
5. `GameEngine.swift:18-19`: expor `ranked`, `secondBest`, `margin`, `ratio`, `entropy`, `effectiveCandidates`.
6. `GameViews.swift:114`: estado `loading` + guardas `canRespond/canConfirm` + `isTransitioning` + debounce 250ms.
7. `GameViews.swift:270`: `question = nil` ao palpitar; `rejectedIDs` como `Set`; `maxRejected = 4`.
8. `ProgressModels.swift:18`: `knowledgeVersion/hash`, `expiresAt`; validar em `loadRound`.
9. `KnowledgeStore.swift:9-18`: `do/catch` com erro tipado, sem `try?` silencioso.
10. `ProgressStore.swift:166`: relogio para tras zera streak; limitar `categoryHistory` a 100; datas ISO8601 com fallback.
