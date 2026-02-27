from pathlib import Path

from app.pdf_generator import generate_pdfs
from app.processing import process_input


def main():
    path_dic = Path("data/arquivos_pnatrans.xlsx")
    path_input = Path(
        "data/Mapeamento de produtos e ações realizados pelo Detran-SP "
        "para o Painel Pnatrans.xlsx"
    )

    df = process_input(path_input, path_dic)
    print(f"Dados processados: {len(df)} linhas")

    output_dir = Path("output")

    def on_progress(current, total):
        print(f"  [{current}/{total}] concluído")

    pdf_files = generate_pdfs(df, output_dir, on_progress=on_progress)
    print(f"\nConcluído! {len(pdf_files)} relatórios gerados na pasta 'output/'.")


if __name__ == "__main__":
    main()
