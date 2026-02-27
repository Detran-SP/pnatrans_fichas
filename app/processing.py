import re
import unicodedata
from pathlib import Path

import pandas as pd


def clean_names(df: pd.DataFrame) -> pd.DataFrame:
    """Converte nomes de colunas para snake_case (equivalente ao janitor::clean_names)."""

    def to_snake(name: str) -> str:
        name = name.strip()
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
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\n•", "\n\n•")
    text = re.sub(r"\. \n(?=[A-Z](?!•))", ". \n\n", text)
    return text


def sanitize_filename(name: str, max_len: int = 50) -> str:
    """Remove acentos e caracteres especiais de um nome para uso em arquivo."""
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_text = nfkd.encode("ascii", "ignore").decode("ascii")
    ascii_text = re.sub(r"[^\w\s-]", "", ascii_text)
    ascii_text = re.sub(r"\s+", "_", ascii_text)
    return ascii_text[:max_len]


UNITE_MAP = {
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


def process_input(input_file_path: Path, dict_file_path: Path) -> pd.DataFrame:
    """Lê o Excel de input + dicionário, aplica todas as transformações e retorna o DataFrame."""
    df_dic = pd.read_excel(dict_file_path, sheet_name=3)
    df_input = pd.read_excel(input_file_path)
    df_input = clean_names(df_input)

    for prefix, new_name in UNITE_MAP.items():
        df_input = unite_columns(df_input, prefix, new_name)

    df_input["descricao_e_justificativa"] = df_input[
        "descricao_e_justificativa"
    ].apply(clean_text)

    df_input["links_comprovatorios"] = df_input["links_comprovatorios"].str.replace(
        "\r\n", "", regex=False
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

    return df_input
