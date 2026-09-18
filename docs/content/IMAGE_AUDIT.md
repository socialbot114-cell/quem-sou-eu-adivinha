# Auditoria inicial de imagens

Data da revisao: 2026-09-18

## Escopo e criterio

- Fonte local: `/home/richard/Imagens/famosos`.
- Creditos considerados exclusivamente de `CREDITOS.txt`; nenhuma licenca foi presumida ou ampliada.
- Inclusao limitada a pessoa claramente identificavel, enquadramento aproveitavel e credito com origem, autor e licenca claros.
- Exclusao de montagens, graficos, caricaturas, objetos, placas, fotos coletivas ambiguas, imagens sem entrada em `CREDITOS.txt`, baixa resolucao e casos em que o sujeito nao era inequívoco.
- A presenca neste conjunto significa apenas aprovacao editorial e tecnica desta rodada. As obrigacoes de atribuicao e compartilhamento pela mesma licenca continuam aplicaveis conforme cada item.

## Resultado

Foram aprovados 10 retratos: 3 de `atores`, 4 de `jogadores`, 2 de `politicos` e 1 de `youtubers`. Os metadados completos e as modificacoes por arquivo estao em `image-credits.json`.

| ID | Pessoa | Fonte | Antes (bytes) | Depois (bytes) | Revisao |
| --- | --- | --- | ---: | ---: | --- |
| `rodrigo-santoro` | Rodrigo Santoro | `atores/Rodrigo_Santoro.jpg` | 1.424.997 | 156.630 | Aprovado |
| `wagner-moura` | Wagner Moura | `atores/Wagner_Moura.jpg` | 1.874.259 | 191.374 | Aprovado |
| `tais-araujo` | Taís Araújo | `atores/Tais_Araujo.jpg` | 1.173.747 | 220.978 | Aprovado |
| `alisson-becker` | Alisson Becker | `jogadores/Alisson_Becker.jpg` | 881.356 | 249.025 | Aprovado |
| `casemiro` | Casemiro | `jogadores/Casemiro.jpg` | 1.321.578 | 194.906 | Aprovado |
| `gabriel-jesus` | Gabriel Jesus | `jogadores/Gabriel_Jesus.jpg` | 1.226.194 | 141.206 | Aprovado |
| `vinicius-junior` | Vinícius Júnior | `jogadores/Vinicius_Junior.jpg` | 1.546.968 | 258.065 | Aprovado |
| `sergio-moro` | Sergio Moro | `politicos/Sergio_Moro.jpg` | 322.085 | 218.945 | Aprovado |
| `marina-silva` | Marina Silva | `politicos/Marina_Silva.jpg` | 746.957 | 155.789 | Aprovado |
| `nathalia-arcuri` | Nathalia Arcuri | `youtubers/Nathalia_Arcuri.jpg` | 1.631.298 | 175.786 | Aprovado |
| **Total** |  |  | **12.149.439** | **1.962.704** | **83,85% menor** |

## Processamento e validacao

- Corte manual quadrado por sujeito, sem esticar a imagem e preservando rosto e cabelo.
- Redimensionamento Lanczos com FFmpeg 7.0.2 para 1024x1024.
- Recompressao JPEG em qualidade 85 e conversao/incorporacao de perfil ICC sRGB com `jpgicc` (Little CMS 2.14).
- Todos os 10 arquivos foram reabertos e inspecionados visualmente depois do processamento.
- `ffprobe` confirmou 1024x1024 em todos os arquivos; a presenca do marcador `ICC_PROFILE` foi confirmada nos 10 JPEGs.

## Exclusoes representativas

- `politicos/Jair_Bolsonaro.jpg` e `politicos/Lula.jpg`: graficos eleitorais, nao retratos.
- `politicos/Alexandre_de_Moraes.jpg`: caricatura/arte politica.
- `jogadores/Neymar.jpg`: foto de bola autografada, sem retrato utilizavel.
- `jogadores/Kaka.jpg`: foto de chuteira, sem retrato utilizavel.
- `jogadores/Ronaldo.jpg`: exibicao de museu, sem retrato utilizavel.
- `jogadores/Pele.jpg`: placa/arte urbana, sem retrato utilizavel.
- `jogadores/Marta.jpg`: foto coletiva com sujeito ambiguo para este uso.
- `atores/Sonia_Braga.jpg`: foto coletiva com outras pessoas em destaque.
- Arquivos existentes na fonte mas ausentes de `CREDITOS.txt`: excluidos sem tentativa de inferir direitos.
- Demais candidatos nao aprovados nesta rodada: fora do conjunto inicial por composicao, nitidez, escala do rosto ou ambiguidade conservadora.
