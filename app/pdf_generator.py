from __future__ import annotations

import re
import subprocess
import tempfile
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
    output_dir.mkdir(parents=True, exist_ok=True)
    datetime_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    generated_files: list[Path] = []

    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "processed_data.csv"
        df.to_csv(csv_path, index=False)

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
                    cwd=str(PROJECT_ROOT),
                )

                generated = output_dir / output_filename
                if generated.exists():
                    generated_files.append(generated)
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
            csv_plano = pd.DataFrame({
                "esfera": "E",
                "uf": "SP",
                "municipio": "",
                "regiao": "",
                "pilar": df_plano["pilar"].apply(extract_pilar_number),
                "produto": df_plano["produto"].apply(extract_produto_number),
                "ano": df_plano["ano_referencia"].apply(format_ano),
                "quantidade": df_plano["valor_resultado"].apply(format_valor),
                "link": df_plano["links_comprovatorios"].fillna(""),
            })
        else:
            csv_plano = pd.DataFrame(
                columns=["esfera", "uf", "municipio", "regiao", "pilar",
                         "produto", "ano", "quantidade", "link"]
            )

        plano_path = tmpdir_path / "produtos.csv"
        csv_plano.to_csv(plano_path, sep=";", header=False, index=False)

        # Produtos Novos
        mask_novo = df["tipo_de_produto_a_ser_enviado"] == "Produto Novo"
        df_novo = df[mask_novo].copy()

        if not df_novo.empty:
            csv_novo = pd.DataFrame({
                "pilar": df_novo["pilar"].apply(extract_pilar_number),
                "produto": df_novo["titulo_do_produto_detran"].fillna(""),
                "esfera": "E",
                "regiao": "",
                "uf": "SP",
                "municipio": "",
                "ano": df_novo["ano_referencia"].apply(format_ano),
                "quantidade": df_novo["valor_resultado"].apply(format_valor),
                "link": df_novo["links_comprovatorios"].fillna(""),
            })
        else:
            csv_novo = pd.DataFrame(
                columns=["pilar", "produto", "esfera", "regiao", "uf",
                         "municipio", "ano", "quantidade", "link"]
            )

        novo_path = tmpdir_path / "produtos_novos.csv"
        csv_novo.to_csv(novo_path, sep=";", header=False, index=False)

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(plano_path, "produtos.csv")
            zf.write(novo_path, "produtos_novos.csv")

    return zip_path
