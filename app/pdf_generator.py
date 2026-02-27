from __future__ import annotations

import re
import subprocess
import zipfile
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import pandas as pd

from app.processing import sanitize_filename

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def generate_pdfs(
    df: pd.DataFrame,
    output_dir: Path,
    on_progress: Callable | None = None,
) -> list[Path]:
    """Gera PDFs para cada linha do DataFrame e retorna lista de caminhos."""
    # Escreve CSV onde main.qmd espera
    csv_path = PROJECT_ROOT / "data" / "processed_data.csv"
    df.to_csv(csv_path, index=False)

    output_dir.mkdir(parents=True, exist_ok=True)
    datetime_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    generated_files: list[Path] = []

    for i in range(len(df)):
        row = df.iloc[i]
        produto_detran_clean = sanitize_filename(
            str(row.get("titulo_do_produto_detran", ""))
        )
        produto_clean = re.sub(r"\s+", "_", str(row.get("produto", "")))
        output_filename = (
            f"{row['acao']}_{produto_clean}_{produto_detran_clean}"
            f"_{datetime_stamp}.pdf"
        )

        try:
            subprocess.run(
                [
                    "quarto",
                    "render",
                    "main.qmd",
                    "--output",
                    output_filename,
                    "--execute-param",
                    f"row_index:{i + 1}",
                ],
                capture_output=True,
                text=True,
                check=True,
                cwd=str(PROJECT_ROOT),
            )

            generated = PROJECT_ROOT / output_filename
            target = output_dir / output_filename
            if generated.exists():
                generated.rename(target)
                generated_files.append(target)
        except subprocess.CalledProcessError as e:
            print(f"Erro ao gerar {output_filename}: {e.stderr}")

        if on_progress:
            on_progress(i + 1, len(df))

    return generated_files


def create_zip(pdf_paths: list[Path], zip_path: Path) -> Path:
    """Empacota os PDFs em um arquivo .zip."""
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for pdf in pdf_paths:
            zf.write(pdf, pdf.name)
    return zip_path
