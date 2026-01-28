# Sistema de Automação de Relatórios PNATRANS

Este sistema gera automaticamente fichas em PDF para cada produto/ação registrado no sistema PNATRANS.

## Como funciona

O sistema:
1. Lê e processa os dados Excel uma única vez (evitando duplicação)
2. Salva os dados processados em formato RDS intermediário
3. Gera um PDF para cada linha da planilha
4. Cada PDF usa os dados já processados do arquivo RDS

**Vantagem:** O processamento de dados (leitura, limpeza, joins) acontece apenas uma vez no início, tornando a geração dos PDFs mais eficiente.

## Arquitetura do sistema

```
┌─────────────────────────────────────────────────────────────┐
│                        render.R                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 1. Lê arquivos Excel                                 │    │
│  │ 2. Processa e limpa dados (unite, mutate, joins)    │    │
│  │ 3. Salva → data/processed_data.rds                   │    │
│  │ 4. Loop: Para cada linha                             │    │
│  │    └─> Chama quarto_render(row_index = i)           │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                       main.qmd                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 1. Lê data/processed_data.rds                        │    │
│  │ 2. Seleciona linha params$row_index                  │    │
│  │ 3. Formata links (format_links)                      │    │
│  │ 4. Gera PDF com dados formatados                     │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                   output/{arquivo}.pdf
```

**Divisão de responsabilidades:**
- `render.R` = Processamento de dados + Orquestração
- `main.qmd` = Template de apresentação

## Estrutura de arquivos

- `main.qmd` - Template do relatório (aceita parâmetro `row_index`)
- `render.R` - Script de automação que:
  - Lê e processa os dados Excel
  - Salva dados processados em `data/processed_data.rds`
  - Gera todos os PDFs
- `data/` - Pasta com os arquivos de entrada
  - `arquivos_pnatrans.xlsx` - Dicionário de ações e produtos
  - `Mapeamento de produtos e ações realizados pelo Detran-SP para o Painel Pnatrans.xlsx` - Dados de entrada
  - `processed_data.rds` - Dados processados (gerado pelo `render.R`)
- `output/` - Pasta onde os PDFs gerados são salvos (criada automaticamente)

## Como executar

### Opção 1: Gerar todos os relatórios

Execute o script de automação:

```bash
Rscript render.R
```

Isso irá:
1. Ler todos os dados da planilha
2. Gerar um PDF para cada linha
3. Salvar os arquivos na pasta `output/` com o padrão de nome:
   `{acao}_{produto}_{titulo_produto}_{timestamp}.pdf`

### Opção 2: Gerar um relatório específico

Para gerar apenas uma linha específica (ex: linha 3), você precisa primeiro garantir que os dados estão processados:

```bash
# Opção A: Processar os dados primeiro (se ainda não foi feito)
Rscript -e "source('render.R'); saveRDS(df_input, 'data/processed_data.rds')"

# Opção B: Usar o arquivo RDS já existente (se já rodou render.R antes)
quarto render main.qmd -P row_index:3
```

**Nota:** O arquivo `data/processed_data.rds` é criado automaticamente quando você executa `Rscript render.R`.

## Padrão de nomenclatura

Os arquivos gerados seguem o padrão:
```
{acao_id}_{produto_id}_{titulo_produto_detran}_{timestamp}.pdf
```

Exemplo:
```
A1001_P1003_Curso_de_Capacitacao_em_Fiscalizacao_20260128_143025.pdf
```

Onde:
- `A1001` = ID da ação
- `P1003` = ID do produto
- `Curso_de_Capacitacao_em_Fiscalizacao` = Título do produto (sanitizado)
- `20260128_143025` = Timestamp (YYYYMMDD_HHMMSS)

## Requisitos

Pacotes R necessários:
- tidyverse
- readxl
- janitor
- quarto
- lubridate
- glue

Instalar com:
```r
install.packages(c("tidyverse", "readxl", "janitor", "quarto", "lubridate", "glue"))
```

## Arquivos de entrada

O sistema espera dois arquivos Excel na pasta `data/`:
1. `arquivos_pnatrans.xlsx` - Dicionário de ações e produtos
2. `Mapeamento de produtos e ações realizados pelo Detran-SP para o Painel Pnatrans.xlsx` - Dados de entrada

## Saída

Todos os PDFs são salvos na pasta `output/` com:
- ✅ Bullets formatados corretamente
- ✅ Parágrafos separados adequadamente
- ✅ Links clicáveis (azul e sublinhado)
- ✅ Nomes de arquivo decodificados

## Exemplo de execução

```
$ Rscript render.R

Gerando 6 relatórios...

Processando linha 1/6...
  -> Gerando: A1001_P1003_Curso_de_Capacitacao_em_Fiscalizacao_20260128_143025.pdf
  ✓ Sucesso: A1001_P1003_Curso_de_Capacitacao_em_Fiscalizacao_20260128_143025.pdf

Processando linha 2/6...
  -> Gerando: A2002_P2011_Guia_de_Implementacao_de_Vias_Seguras_20260128_143025.pdf
  ✓ Sucesso: A2002_P2011_Guia_de_Implementacao_de_Vias_Seguras_20260128_143025.pdf

...

Concluído! 6 relatórios gerados na pasta 'output/'.
```
