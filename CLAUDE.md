# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Shiny web app that generates PDF and DOCX forms ("fichas") for the PNATRANS (Plano Nacional de Redução de Acidentes e Segurança Viária). The project uses Python to dynamically generate structured documents with information about traffic safety management pillars, actions, and products.

## Running the Shiny App

```bash
uv run shiny run app
```

The app allows uploading the Excel mapping spreadsheet, previewing processed data, and exporting all fichas as a .zip (PDF or DOCX).

## Project Structure

- `app/` — Shiny web application
  - `app.py` — UI and server logic
  - `processing.py` — Data processing functions (clean_names, unite_columns, etc.)
  - `pdf_generator.py` — PDF generation (Quarto/Typst) and CSV/zip export
  - `docx_generator.py` — Native DOCX generation via python-docx
- `main.qmd` — Quarto/Typst PDF template
- `data/arquivos_pnatrans.xlsx` — PNATRANS dictionary (bundled)
- `logo.png` — Header logo for PDFs

## Key Dependencies

- Python 3.12+ (managed with uv)
- Python packages: `pandas`, `openpyxl`, `shiny`, `python-docx`
- Quarto 1.7.29+
- Typst (via Quarto for PDF rendering)
