# QUEM SOU EU? — Especificação Visual e de UX baseada nos mockups de referência

> Documento de handoff para agente de design/UI.
> Objetivo: aproximar o projeto final o máximo possível da linguagem visual, hierarquia, acabamento e sensação premium dos mockups fornecidos, sem copiar literalmente elementos protegidos de terceiros.
> Plataforma principal: iPhone / iOS.
> Estilo: game casual premium, amigável, jovem, altamente gamificado, com forte apelo visual e sensação de produto polido.

---

# 1. DIREÇÃO GERAL DO PROJETO

## 1.1. Personalidade visual

O aplicativo deve parecer:

- divertido;
- imediatamente compreensível;
- amigável;
- premium;
- gamificado;
- “fofo”, porém não infantil demais;
- com forte identidade própria;
- visualmente muito bem acabado;
- próximo da qualidade de apps de grande escala como Duolingo, Kahoot, Headspace, Poki e jogos casuais mobile modernos.

O visual deve transmitir que o usuário está entrando em um jogo inteligente de adivinhação de personalidades.

A interface não deve parecer um app genérico montado com componentes padrão.

Cada tela deve possuir:

- composição visual própria;
- personagem/mascote recorrente;
- microilustrações;
- sombras suaves;
- blocos com profundidade;
- bordas arredondadas;
- ícones 3D ou pseudo-3D;
- alto contraste entre CTA e fundo;
- hierarquia tipográfica muito clara.

---

# 2. DESIGN SYSTEM GLOBAL

## 2.1. Paleta principal

### Roxo profundo
Uso:
- marca;
- background escuro;
- botões premium;
- títulos;
- contornos e detalhes.

Sugestão:
`#21104F`

### Roxo vibrante
Uso:
- CTA principal;
- destaques;
- efeitos de glow;
- cartões selecionados.

Sugestão:
`#6C22E8`

### Verde-limão
Uso:
- confirmação;
- estados positivos;
- botões;
- detalhes do mascote;
- indicadores de progresso.

Sugestão:
`#B8FF35`

### Verde vibrante secundário
Sugestão:
`#66E91C`

### Amarelo / ouro
Uso:
- moedas;
- conquistas;
- crown;
- recompensa;
- elementos premium.

Sugestão:
`#FFC92F`

### Rosa / magenta
Uso:
- XP;
- efeitos;
- destaques sociais.

Sugestão:
`#E82AAF`

### Azul
Uso:
- cards de categorias mundiais;
- elementos auxiliares.

Sugestão:
`#1FA7FF`

### Fundo claro
Sugestão:
`#FAFAFC`

### Texto escuro
Sugestão:
`#101637`

---

## 2.2. Tipografia

A tipografia deve possuir peso visual forte e arredondado.

### Recomendações
- SF Pro Rounded
- Nunito ExtraBold
- Baloo 2
- Fredoka
- Poppins ExtraBold
- Avenir Next Rounded

### Títulos principais
- peso: 800–900;
- tamanho: 36–52 px;
- line-height reduzido;
- tracking levemente negativo;
- bordas visualmente arredondadas.

### Subtítulos
- peso: 600–700;
- tamanho: 19–26 px.

### Labels e botões
- peso: 700–800;
- tamanho: 18–24 px.

### Números de pontuação
- peso: 900;
- tamanho: 24–36 px.

---

## 2.3. Bordas e raios

A linguagem visual depende fortemente de curvas.

Usar:

- cards grandes: `24–32 px`;
- botões CTA: `24–30 px`;
- cards pequenos: `18–24 px`;
- ícones dentro de caixas: `16–22 px`;
- nav bottom: `30–36 px`.

Evitar cantos quadrados.

---

## 2.4. Sombras

As sombras devem ser delicadas, mas visíveis.

### Cards claros
- blur alto;
- baixa opacidade;
- deslocamento vertical de 8–14 px.

Exemplo CSS:
```css
box-shadow: 0 12px 30px rgba(40, 20, 100, 0.12);
```

### CTA roxo
```css
box-shadow:
  0 12px 28px rgba(90, 35, 220, 0.30),
  inset 0 2px 0 rgba(255,255,255,0.20);
```

### Elementos 3D
Aplicar:
- highlight superior;
- shadow inferior;
- borda interna luminosa.

---

# 3. MASCOTE

O mascote é central para a identidade do projeto.

Características:

- pequeno personagem branco ou verde;
- formato orgânico;
- cabeça grande;
- olhos expressivos;
- blush rosa;
- gestos exagerados;
- acessórios ligados à lógica de “descoberta”:
  - lupa;
  - coroa;
  - ponto de interrogação;
  - confete;
  - troféu.

O mascote deve aparecer em vários estados:

1. curioso;
2. comemorando;
3. investigando;
4. pensando;
5. confiante;
6. surpreso.

A repetição do mascote cria coerência entre as telas.

---

# 4. TELA 01 — HOME / DASHBOARD

## 4.1. Objetivo

A Home deve comunicar instantaneamente:

- que existe um jogo;
- que o app vai tentar descobrir em quem o usuário pensou;
- que existem recompensas;
- que existem desafios e conquistas;
- que existe continuidade de progresso.

---

## 4.2. Estrutura visual

### Header

No topo:

- logo `Olá!` ou logo oficial do jogo;
- slogan curto:
  `Pronto para descobrir quem você pensou?`
- botão de configurações no canto superior direito.

O botão deve ser:
- quadrado;
- fundo lilás muito claro;
- ícone roxo;
- aproximadamente 52x52 px;
- radius 18–20 px.

---

## 4.3. Bloco de progresso

Logo abaixo:

3 mini-cards lado a lado.

### Card 1 — sequência
Conteúdo:
- ícone 🔥;
- número grande;
- label `sequência`.

### Card 2 — moedas
Conteúdo:
- moeda dourada 3D;
- quantidade;
- label `moedas`.

### Card 3 — pontos
Conteúdo:
- coroa;
- pontuação;
- label `pontos`.

Todos devem ter:

- background pastel individual;
- radius 22–26 px;
- sombra leve;
- centralização total;
- números muito evidentes.

---

## 4.4. Área principal do mascote

O centro da tela deve ser dominado por uma ilustração grande do mascote.

Exemplo:

- mascote com lupa;
- coroa;
- expressão simpática;
- formas abstratas verdes e lilases no fundo.

Adicionar balão lateral com frase:
`Grandes personagens começam com uma pergunta!`

O balão deve parecer uma speech bubble real, não apenas um card.

---

## 4.5. CTA principal

Texto:
`Jogar agora`

Características:

- largura quase total;
- fundo roxo com gradiente;
- altura aproximada: 90–110 px;
- radius: 30 px;
- texto branco;
- fonte muito bold;
- seta dentro de círculo verde-limão;
- sombra pronunciada.

A seta deve ficar no canto direito.

O botão precisa ser o elemento de maior destaque da tela.

---

## 4.6. Bloco secundário

3 cards lado a lado:

### Continuar desafio
- ícone gamepad;
- fundo lilás.

### Minhas conquistas
- ícone troféu;
- fundo amarelo claro.

### Desafios diários
- ícone calendário;
- fundo rosa claro.

Cards:
- quadrados;
- ícones grandes;
- texto em duas linhas;
- seta pequena no canto.

---

## 4.7. Navegação inferior

Itens:
- Início
- Categorias
- Conquistas
- Perfil

Item ativo:
- fundo verde-limão;
- label escuro;
- radius grande.

Os demais:
- ícone roxo/cinza;
- label menor.

A bottom nav deve parecer uma peça flutuante dentro da tela.

---

# 5. TELA 02 — ESCOLHA DE CATEGORIA

## 5.1. Objetivo

Permitir que o usuário escolha rapidamente o universo de personalidades que deseja jogar.

---

## 5.2. Header

Topo com:

- botão voltar em box arredondado;
- título:
  `Escolha uma categoria`
- subtítulo:
  `Pense em alguém e eu descubro!`
- mascote parcialmente visível à direita.

O mascote invade visualmente o header e quebra a rigidez da interface.

---

## 5.3. Grid de categorias

Grid 2x3.

Cada categoria ocupa um card quase quadrado.

### Card TikTok
- fundo preto / grafite;
- logo do TikTok;
- texto branco;
- detalhes verde-limão ao redor.

### Card Instagram
- fundo gradiente rosa, laranja, roxo;
- ícone Instagram 3D;
- texto branco.

### Jogadores de Futebol
- fundo verde;
- bola 3D;
- texto branco.

### Artistas Brasileiros
- fundo amarelo;
- nota musical 3D;
- texto roxo/preto.

### Políticos
- fundo roxo;
- púlpito estilizado;
- texto branco.

### Personalidades Mundiais
- fundo azul;
- globo 3D;
- texto branco.

---

## 5.4. Tratamento dos cards

Todos os cards devem ter:

- radius 24–30 px;
- sombra;
- ícone central grande;
- texto centralizado;
- altura consistente;
- pequenas ilustrações ou traços decorativos.

Usar pequenas “linhas de energia” próximas ao ícone para aumentar dinamismo.

Não usar cards planos.

---

## 5.5. Bottom navigation

A mesma estrutura da Home.

Aqui `Categorias` é o item ativo.

Ativo:
- fundo verde-limão;
- ícone escuro;
- label escuro.

---

# 6. TELA 03 — SPLASH / APRESENTAÇÃO

## 6.1. Objetivo

Criar impacto visual imediato.

Essa tela deve funcionar como:

- splash screen;
- abertura da experiência;
- branding;
- tela de loading.

---

## 6.2. Background

Cor base:
- roxo profundo.

Adicionar:
- blobs roxos mais claros;
- gradientes radiais;
- partículas verdes;
- pequenas linhas decorativas.

O fundo precisa parecer ilustrado, não simplesmente uma cor sólida.

---

## 6.3. Logo central

Estrutura:

- mascote dentro de um círculo ou moldura;
- ponto de interrogação verde;
- marca:
  `QUEM SOU EU?`

Hierarquia:

`QUEM`
em branco.

`SOU EU?`
em verde-limão.

Adicionar sombra forte atrás do título para dar aparência 3D.

---

## 6.4. Tagline

Texto:
`PENSE EM ALGUÉM, EU DESCUBRO!`

Características:

- caixa alta;
- branco;
- tracking maior;
- centralizado;
- peso bold.

---

## 6.5. Rodapé ilustrado

Adicionar uma onda orgânica verde-limão ocupando cerca de 20–25% do rodapé.

Dentro:

`GRANDES PERSONAGENS COMEÇAM COM UMA PERGUNTA!`

Usar tipografia manuscrita ou divertida para diferenciar do título.

Adicionar seta desenhada à mão.

---

# 7. TELA 04 — RESULTADO / ACERTO

## 7.1. Objetivo

Ser a tela de maior sensação de recompensa de todo o app.

O usuário precisa sentir:
- surpresa;
- celebração;
- progresso;
- satisfação.

---

## 7.2. Top bar

Topo minimalista.

Esquerda:
- botão `Início`.

Direita:
- saldo de moedas;
- ícone `+`.

O saldo deve parecer uma pequena pill.

---

## 7.3. Estado de vitória

Mascote verde em pose de comemoração.

Ao redor:
- confetes;
- coroa;
- pequenos shapes;
- partículas.

Texto principal:

`ACERTEI!`

Criar contraste:

`ACER`
em azul-marinho / roxo profundo.

`TEI!`
em verde.

Subtítulo:
`Eu descobri quem você pensou!`

---

## 7.4. Card de personagem

Card branco grande.

Dividido aproximadamente em:
- 55% imagem;
- 45% dados.

### Lado esquerdo

Foto grande da personalidade.

Overlay superior:
`CONFIRMADO`

com:
- fundo amarelo;
- ícone coroa;
- pill arredondada.

### Lado direito

Nome da personalidade.

Exemplo:
`Neymar Jr.`

Abaixo, lista de informações:

- nacionalidade;
- categoria;
- seguidores;
- relevância;
- curiosidade;
- seleção/time.

Cada informação deve possuir:
- ícone pequeno;
- texto curto;
- espaçamento confortável.

---

# 8. MÉTRICAS DO RESULTADO

Logo abaixo do card principal:

3 mini-cards horizontais.

### Perguntas
- ícone `?`;
- número grande;
- label `perguntas`;
- selo adicional:
  `Muito bom!`

### Moedas
- moeda dourada;
- recompensa, ex.: `+80`;
- label `moedas`.

### XP
- estrela rosa;
- recompensa, ex.: `+120`;
- label `pontos de XP`.

Os cards precisam parecer componentes de recompensa de game.

---

# 9. FEEDBACK DO MASCOTE

Criar um banner horizontal lilás claro.

Conteúdo:
- mini mascote à esquerda;
- texto:
  `Mais uma no meu currículo!`
- subtítulo:
  `Vamos para a próxima?`

Isso ajuda a humanizar o resultado.

---

# 10. CTAs DA TELA DE RESULTADO

## CTA principal

Texto:
`Jogar novamente`

Características:
- fundo verde-limão;
- texto preto;
- ícone play;
- largura quase total;
- 70–90 px de altura;
- radius 24–30 px.

---

## CTA secundário

Texto:
`Compartilhar resultado`

Características:
- branco;
- borda cinza/lilás;
- ícone share;
- mesma largura;
- menos destaque.

---

## CTA terciário

Texto:
`Ver meu desempenho`

Características:
- branco;
- ícone gráfico;
- seta à direita.

---

# 11. ESPAÇAMENTO E GRID

## Margem lateral

iPhone:
`24–28 px`

## Espaçamento entre cards

`12–18 px`

## Espaçamento entre seções

`24–36 px`

## Padding interno

Cards:
`16–24 px`

Botões:
`18–24 px`

---

# 12. QUALIDADE DOS ÍCONES

Evitar ícones simples “flat” demais.

Preferir:

- 3D suave;
- glossy;
- depth;
- highlights;
- bordas internas;
- sombras coloridas;
- sensação de brinquedo premium.

A estética deve se aproximar de ícones usados em games mobile.

---

# 13. ANIMAÇÕES RECOMENDADAS

### Home
- mascote respira suavemente;
- lupa flutua;
- CTA possui micro-pulse;
- moedas brilham.

### Categorias
- card cresce 3–5% no toque;
- ícone faz bounce;
- sombra aumenta.

### Splash
- logo entra com bounce;
- ponto de interrogação cai;
- mascote pisca.

### Resultado
- confetes caem;
- XP conta de 0 até o total;
- moedas sobem;
- mascote pula;
- card aparece com scale + fade.

---

# 14. O QUE O AGENTE DEVE EVITAR

Não usar:

- cards completamente flat;
- bordas de 8 px;
- botões pequenos;
- textos muito finos;
- excesso de cinza;
- backgrounds totalmente vazios;
- iconografia inconsistente;
- elementos com aparência de template;
- espaçamento apertado;
- fontes corporativas rígidas;
- gradientes exagerados sem motivo.

---

# 15. PRINCÍPIOS DE REFINAMENTO

O redesign deve seguir estes princípios:

1. Cada tela precisa ter um “hero visual”.
2. Cada tela precisa ter apenas 1 CTA dominante.
3. O mascote deve participar da experiência.
4. A gamificação precisa ser visível em todos os momentos.
5. Os cards devem transmitir profundidade.
6. O usuário deve compreender a ação principal em menos de 2 segundos.
7. A interface deve parecer construída especificamente para o jogo.
8. O acabamento precisa ter padrão App Store / produto premium.
9. Os elementos da marca precisam ser consistentes em todas as telas.
10. O visual deve funcionar bem em screenshots de loja.

---

# 16. COMPONENTES REUTILIZÁVEIS

Criar componentes:

```txt
AppHeader
MascotHero
StatCard
CategoryCard
RewardCard
PrimaryCTA
SecondaryCTA
BottomNavigation
CharacterResultCard
CoinCounter
XPBadge
SpeechBubble
AchievementBadge
FloatingDecorations
```

Todos precisam usar tokens globais de:

- cor;
- radius;
- sombra;
- spacing;
- tipografia.

---

# 17. TOKENS SUGERIDOS

```css
--color-purple-900: #21104F;
--color-purple-600: #6C22E8;
--color-lime-400: #B8FF35;
--color-green-500: #66E91C;
--color-yellow-400: #FFC92F;
--color-pink-500: #E82AAF;
--color-blue-500: #1FA7FF;
--color-text: #101637;
--color-bg: #FAFAFC;

--radius-sm: 16px;
--radius-md: 22px;
--radius-lg: 28px;
--radius-xl: 36px;

--space-xs: 8px;
--space-sm: 12px;
--space-md: 18px;
--space-lg: 24px;
--space-xl: 32px;
```

---

# 18. BRIEF FINAL PARA O AGENTE

Redesenhar o app **QUEM SOU EU?** tomando as quatro telas de referência como benchmark visual.

Prioridades:

- aproximar o acabamento aos mockups;
- aumentar o nível de polimento;
- melhorar tipografia;
- adicionar profundidade;
- fortalecer a identidade do mascote;
- usar cards mais robustos;
- melhorar CTAs;
- aprimorar hierarquia visual;
- aumentar a sensação de produto gamificado;
- manter consistência entre as telas.

O resultado deve parecer um aplicativo real lançado na App Store, e não um wireframe ou protótipo.

A referência principal deve ser interpretada em termos de:
- qualidade;
- proporção;
- hierarquia;
- sensação de profundidade;
- distribuição de cor;
- composição;
- uso de mascot;
- gamificação.

Evitar simples cópia pixel a pixel. O objetivo é elevar o design atual para um nível de acabamento equivalente.
