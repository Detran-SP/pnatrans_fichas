# PNATRANS — Gerador de Fichas

App Shiny (Python) que gera fichas em PDF e DOCX para os produtos e ações do PNATRANS (Plano Nacional de Redução de Acidentes e Segurança Viária) reportados pelo Detran-SP.

## Funcionalidades

- Upload da planilha de mapeamento (`.xlsx`)
- Pré-visualização dos dados processados
- Seleção de fichas específicas para exportar
- Exportação em lote como `.zip`:
  - Fichas em **PDF** (renderizadas via Quarto/Typst)
  - Fichas em **DOCX** (geradas nativamente via `python-docx`)
  - **CSVs** prontos para o Painel PNATRANS (produtos do Plano de Ação e Produtos Novos)

## Como executar

```bash
uv run shiny run app
```

## Requisitos

- Python 3.12+ (gerenciado com [uv](https://github.com/astral-sh/uv))
- [Quarto](https://quarto.org/) 1.7.29+ (com Typst, usado para renderizar os PDFs)
- Dependências Python declaradas em `pyproject.toml`: `pandas`, `openpyxl`, `shiny`, `python-docx`

## Estrutura

- `app/` — aplicação Shiny
  - `app.py` — UI e lógica do servidor
  - `processing.py` — leitura e transformação dos dados
  - `pdf_generator.py` — geração de PDFs (Quarto) e exportação dos CSVs
  - `docx_generator.py` — geração nativa de DOCX
- `main.qmd` — template Quarto/Typst do PDF
- `data/arquivos_pnatrans.xlsx` — dicionário PNATRANS (bundled)
- `logo.png` — logo usada no cabeçalho dos documentos
