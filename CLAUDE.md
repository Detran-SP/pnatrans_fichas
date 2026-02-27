# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Quarto document project that generates PDF forms ("fichas") for the PNATRANS (Plano Nacional de Redução de Acidentes e Segurança Viária). The project uses Python to dynamically generate structured documents with information about traffic safety management pillars, actions, and products.

## Building and Rendering

**Generate all PDFs (processes data + renders each row):**
```bash
uv run python render.py
```

**Render a single document to PDF:**
```bash
quarto render main.qmd
```

**Preview with live reload:**
```bash
quarto preview main.qmd
```

The output format is Typst, which generates PDF files.

## Document Structure

The `main.qmd` file uses Python code chunks to:
1. Set up dependencies (`pandas`, `re`, `urllib.parse`)
2. Read processed data from `data/processed_data.csv`
3. Select the row based on `row_index` parameter
4. Format links and generate markdown output using f-strings

The `render.py` script:
1. Reads Excel input files and the PNATRANS dictionary
2. Cleans and processes the data (unites columns, normalizes text)
3. Saves processed data as CSV
4. Loops through each row calling `quarto render` with parameters

## Key Dependencies

- Python 3.12+ (managed with uv)
- Python packages: `pandas`, `openpyxl`
- Quarto 1.7.29+
- Typst (via Quarto for PDF rendering)
