from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import zipfile
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import pandas as pd

from app.docx_generator import generate_docx_documents
from app.processing import sanitize_filename

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def generate_documents(
    df: pd.DataFrame,
    output_dir: Path,
    fmt: str = "pdf",
    on_progress: Callable | None = None,
) -> list[Path]:
    """Gera documentos para cada linha do DataFrame e retorna lista de caminhos.

    `fmt` aceita "pdf" (renderizado via Quarto/Typst) ou "docx" (via python-docx).
    """
    if fmt == "docx":
        return generate_docx_documents(df, output_dir, on_progress=on_progress)
    if fmt != "pdf":
        raise ValueError(f"Formato não suportado: {fmt!r}. Use 'pdf' ou 'docx'.")

    output_dir.mkdir(parents=True, exist_ok=True)
    datetime_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    generated_files: list[Path] = []

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        csv_path = tmpdir_path / "processed_data.csv"
        df.to_csv(csv_path, index=False)

        # Copia main.qmd e logo.png para o dir temporário para isolar cada
        # render — evita conflito no main.quarto_ipynb em sessões concorrentes.
        shutil.copy(PROJECT_ROOT / "main.qmd", tmpdir_path / "main.qmd")
        logo_src = PROJECT_ROOT / "logo.png"
        if logo_src.exists():
            shutil.copy(logo_src, tmpdir_path / "logo.png")

        for i in range(len(df)):
            row = df.iloc[i]
            produto = str(row.get("produto", "")).strip()
            id_remessa = sanitize_filename(str(row.get("id_remessa", datetime_stamp)))
            output_filename = f"{produto}-{id_remessa}.pdf"

            try:
                subprocess.run(
                    [
                        "quarto",
                        "render",
                        "main.qmd",
                        "--output",
                        output_filename,
                        "--output-dir",
                        str(output_dir),
                        "--execute-param",
                        f"row_index:{i + 1}",
                        "--execute-param",
                        f"csv_path:{csv_path}",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                    cwd=str(tmpdir_path),
                )

                generated = output_dir / output_filename
                if generated.exists():
                    generated_files.append(generated)
            except subprocess.CalledProcessError as e:
                print(f"Erro ao gerar {output_filename}: {e.stderr}")

            if on_progress:
                on_progress(i + 1, len(df))

    return generated_files


def create_zip(file_paths: list[Path], zip_path: Path) -> Path:
    """Empacota os arquivos em um .zip."""
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in file_paths:
            zf.write(file, file.name)
    return zip_path


def generate_csvs_zip(df: pd.DataFrame, zip_path: Path) -> Path:
    """Gera CSVs de produtos para o Painel PNATRANS e empacota em um zip."""

    def extract_pilar_number(pilar: str) -> str:
        match = re.search(r"\d+", str(pilar))
        return match.group() if match else str(pilar)

    def extract_produto_number(produto: str) -> str:
        return str(produto).lstrip("P")

    def format_ano(ano) -> str:
        try:
            return str(int(float(ano)))
        except (ValueError, TypeError):
            return str(ano)

    def format_valor(valor) -> str:
        try:
            return str(int(float(valor)))
        except (ValueError, TypeError):
            return str(valor)

    zip_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Produtos do Plano de Ação
        mask_plano = df["tipo_de_produto_a_ser_enviado"] == "Plano de Ação"
        df_plano = df[mask_plano].copy()

        if not df_plano.empty:
            csv_plano = pd.DataFrame(
                {
                    "esfera": "E",
                    "uf": "SP",
                    "municipio": "",
                    "regiao": "",
                    "pilar": df_plano["pilar"].apply(extract_pilar_number),
                    "produto": df_plano["produto"].apply(extract_produto_number),
                    "ano": df_plano["ano_referencia"].apply(format_ano),
                    "quantidade": df_plano["valor_resultado"].apply(format_valor),
                    "link": df_plano["link_drive"].fillna("").astype(str).str.strip(),
                }
            )
        else:
            csv_plano = pd.DataFrame(
                columns=[
                    "esfera",
                    "uf",
                    "municipio",
                    "regiao",
                    "pilar",
                    "produto",
                    "ano",
                    "quantidade",
                    "link",
                ]
            )

        # Produtos Novos
        mask_novo = df["tipo_de_produto_a_ser_enviado"] == "Produto Novo"
        df_novo = df[mask_novo].copy()

        if not df_novo.empty:
            csv_novo = pd.DataFrame(
                {
                    "pilar": df_novo["pilar"].apply(extract_pilar_number),
                    "produto": df_novo["titulo_do_produto_detran"].fillna(""),
                    "esfera": "E",
                    "regiao": "",
                    "uf": "SP",
                    "municipio": "",
                    "ano": df_novo["ano_referencia"].apply(format_ano),
                    "quantidade": df_novo["valor_resultado"].apply(format_valor),
                    "link": df_novo["link_drive"].fillna("").astype(str).str.strip(),
                }
            )
        else:
            csv_novo = pd.DataFrame(
                columns=[
                    "pilar",
                    "produto",
                    "esfera",
                    "regiao",
                    "uf",
                    "municipio",
                    "ano",
                    "quantidade",
                    "link",
                ]
            )

        CSV_ROW_LIMIT = 30

        def write_csv_chunks(zf: zipfile.ZipFile, df_csv: pd.DataFrame, base_name: str) -> None:
            if len(df_csv) <= CSV_ROW_LIMIT:
                chunk_path = tmpdir_path / base_name
                df_csv.to_csv(chunk_path, sep=";", header=False, index=False)
                zf.write(chunk_path, base_name)
            else:
                stem = base_name.removesuffix(".csv")
                for part, start in enumerate(range(0, len(df_csv), CSV_ROW_LIMIT), start=1):
                    chunk = df_csv.iloc[start : start + CSV_ROW_LIMIT]
                    chunk_name = f"{stem}_{part}.csv"
                    chunk_path = tmpdir_path / chunk_name
                    chunk.to_csv(chunk_path, sep=";", header=False, index=False)
                    zf.write(chunk_path, chunk_name)

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            write_csv_chunks(zf, csv_plano, "produtos.csv")
            write_csv_chunks(zf, csv_novo, "produtos_novos.csv")

    return zip_path
