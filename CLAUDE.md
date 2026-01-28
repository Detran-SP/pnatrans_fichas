# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Quarto document project that generates PDF forms ("fichas") for the PNATRANS (Plano Nacional de Redução de Acidentes e Segurança Viária). The project uses R to dynamically generate structured documents with information about traffic safety management pillars, actions, and products.

## Building and Rendering

**Render the main document to PDF:**
```bash
quarto render main.qmd
```

**Preview with live reload:**
```bash
quarto preview main.qmd
```

The output format is Typst, which generates a PDF file (`main.pdf`).

## Document Structure

The `main.qmd` file uses R code chunks to:
1. Set up dependencies (`dplyr`, `glue`, `knitr`)
2. Define input parameters (pilar ID/name, ação ID/name, produto details, justification)
3. Generate formatted output sections using `glue()` for string interpolation

Input variables follow this structure:
- `input_pilar_id` and `input_pilar_name`: Traffic safety pillar identification
- `input_acao_id` and `input_acao_name`: Action identification
- `input_prod_id` and `input_prod_name`: Product identification
- `input_prod_detran_name`: DETRAN-specific product title
- `input_justificativa`: Multi-paragraph justification text

## Key Dependencies

- R packages: `dplyr`, `glue`, `knitr`
- Quarto 1.7.29+
- Typst (via Quarto for PDF rendering)
