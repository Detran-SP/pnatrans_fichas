# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Quarto document project that generates PDF forms ("fichas") for the PNATRANS (Plano Nacional de Redução de Acidentes e Segurança Viária). The project uses Python to dynamically generate structured documents with information about traffic safety management pillars, actions, and products. It includes both a Shiny web app and a CLI script.

## Running the Shiny App

```bash
uv run shiny run app
```

The app allows uploading the Excel mapping spreadsheet, previewing processed data, and exporting all PDFs as a .zip.

## CLI Usage

**Generate all PDFs (processes data + renders each row):**
```bash
uv run python render.py
```

**Render a single document to PDF:**
```bash
quarto render main.qmd
```

## Project Structure

- `app/` — Shiny web application
  - `app.py` — UI and server logic
  - `processing.py` — Data processing functions (clean_names, unite_columns, etc.)
  - `pdf_generator.py` — PDF generation and zip creation
- `render.py` — CLI entry point (imports from `app/`)
- `main.qmd` — Quarto/Typst PDF template
- `data/arquivos_pnatrans.xlsx` — PNATRANS dictionary (bundled)
- `logo.png` — Header logo for PDFs

## Key Dependencies

- Python 3.12+ (managed with uv)
- Python packages: `pandas`, `openpyxl`, `shiny`
- Quarto 1.7.29+
- Typst (via Quarto for PDF rendering)
