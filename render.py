import re
import subprocess
import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd


def clean_names(df: pd.DataFrame) -> pd.DataFrame:
    """Converte nomes de colunas para snake_case (equivalente ao janitor::clean_names)."""

    def to_snake(name: str) -> str:
        name = name.strip()
        # Remove acentos (equivalente ao iconv ASCII//TRANSLIT)
        nfkd = unicodedata.normalize("NFKD", name)
        name = nfkd.encode("ascii", "ignore").decode("ascii")
        name = re.sub(r"[^\w\s]", "", name)
        name = re.sub(r"\s+", "_", name)
        name = name.lower()
        return name

    return df.rename(columns=to_snake)


def unite_columns(df: pd.DataFrame, prefix: str, new_name: str) -> pd.DataFrame:
    """Concatena colunas que começam com o prefixo, removendo NAs (equivalente ao tidyr::unite)."""
    cols = [c for c in df.columns if c.startswith(prefix)]
    if not cols:
        return df

    def concat_row(row):
        values = [str(v) for v in row if pd.notna(v) and str(v).strip() != ""]
        return "_".join(values) if values else ""

    df[new_name] = df[cols].apply(concat_row, axis=1)
    df = df.drop(columns=[c for c in cols if c != new_name])
    return df


def clean_text(text: str) -> str:
    """Limpa e normaliza texto de descrição/justificativa."""
    if pd.isna(text) or text == "":
        return text
    # Normalizar quebras de linha
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Adicionar quebra dupla antes de bullets
    text = text.replace("\n•", "\n\n•")
    # Adicionar quebra dupla após último bullet antes de novo parágrafo
    text = re.sub(r"\. \n(?=[A-Z](?!•))", ". \n\n", text)
    return text


def sanitize_filename(name: str, max_len: int = 50) -> str:
    """Remove acentos e caracteres especiais de um nome para uso em arquivo."""
    # Normaliza Unicode e converte para ASCII
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_text = nfkd.encode("ascii", "ignore").decode("ascii")
    # Remove caracteres especiais, mantém alfanuméricos, espaços e hifens
    ascii_text = re.sub(r"[^\w\s-]", "", ascii_text)
    # Substitui espaços por underscore
    ascii_text = re.sub(r"\s+", "_", ascii_text)
    return ascii_text[:max_len]


def main():
    # Ler os dados
    path_dic = Path("data/arquivos_pnatrans.xlsx")
    path_input = Path(
        "data/Mapeamento de produtos e ações realizados pelo Detran-SP "
        "para o Painel Pnatrans.xlsx"
    )

    df_dic = pd.read_excel(path_dic, sheet_name=3)
    df_input = pd.read_excel(path_input)
    df_input = clean_names(df_input)

    # Unir colunas com mesmo prefixo
    unite_map = {
        "acao": "acao",
        "produto": "produto",
        "titulo_do_produto_detran": "titulo_do_produto_detran",
        "descricao_e_justificativa": "descricao_e_justificativa",
        "indicador": "indicador",
        "ano_referencia": "ano_referencia",
        "valor_resultado": "valor_resultado",
        "area_responsavel": "area_responsavel",
        "links_comprovatorios": "links_comprovatorios",
        "arquivos_comprovatorios": "arquivos_comprovatorios",
    }

    for prefix, new_name in unite_map.items():
        df_input = unite_columns(df_input, prefix, new_name)

    # Limpar texto da justificativa
    df_input["descricao_e_justificativa"] = df_input[
        "descricao_e_justificativa"
    ].apply(clean_text)

    # Remover \r\n dos links
    df_input["links_comprovatorios"] = (
        df_input["links_comprovatorios"]
        .str.replace("\r\n", "", regex=False)
    )

    # Joins com o dicionário
    dic_acao = df_dic[["codigo_acao", "nome_acao"]].drop_duplicates()
    dic_produto = df_dic[["codigo_acao", "codigo_produto", "nome_produto"]]

    df_input = df_input.merge(
        dic_acao, left_on="acao", right_on="codigo_acao", how="left"
    ).drop(columns=["codigo_acao"])

    df_input = df_input.merge(
        dic_produto,
        left_on=["acao", "produto"],
        right_on=["codigo_acao", "codigo_produto"],
        how="left",
    ).drop(columns=["codigo_acao", "codigo_produto"])

    # Salvar dados processados como CSV
    processed_path = Path("data/processed_data.csv")
    df_input.to_csv(processed_path, index=False)
    print(f"Dados processados e salvos em {processed_path}")

    # Criar diretório de output
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Timestamp para esta execução
    datetime_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Iterar e gerar PDFs
    n_rows = len(df_input)
    print(f"Gerando {n_rows} relatórios...")

    for i in range(n_rows):
        row = df_input.iloc[i]
        print(f"\nProcessando linha {i + 1}/{n_rows}...")

        # Criar nome do arquivo
        produto_detran_clean = sanitize_filename(
            str(row.get("titulo_do_produto_detran", ""))
        )
        produto_clean = re.sub(r"\s+", "_", str(row.get("produto", "")))

        output_filename = (
            f"{row['acao']}_{produto_clean}_{produto_detran_clean}"
            f"_{datetime_stamp}.pdf"
        )
        output_path = output_dir / output_filename

        print(f"  -> Gerando: {output_filename}")

        try:
            result = subprocess.run(
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
            )

            # Mover o arquivo gerado para output/
            generated = Path(output_filename)
            if generated.exists():
                generated.rename(output_path)

            print(f"  ✓ Sucesso: {output_filename}")
        except subprocess.CalledProcessError as e:
            print(f"  ✗ Erro ao gerar {output_filename}: {e.stderr}")

    print(f"\n\nConcluído! {n_rows} relatórios gerados na pasta 'output/'.")


if __name__ == "__main__":
    main()
