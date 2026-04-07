import asyncio
import tempfile
from pathlib import Path

import pandas as pd
from shiny import App, Inputs, Outputs, Session, reactive, render, ui

from app.pdf_generator import (
    PROJECT_ROOT,
    create_zip,
    generate_csvs_zip,
    generate_documents,
)
from app.__version__ import __release_date__, __version__
from app.processing import process_input

DICT_PATH = PROJECT_ROOT / "data" / "arquivos_pnatrans.xlsx"

PREVIEW_COLS = [
    "tipo_de_produto_a_ser_enviado",
    "pilar",
    "acao",
    "nome_acao",
    "produto",
    "nome_produto",
    "titulo_do_produto_detran",
]

NOTIFICATION_ID = "pdf_progress"

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.tags.span(
            ui.tags.i(class_="material-icons", style="vertical-align:middle;"),
            ui.h4(
                "PNATRANS",
                style="display:inline; vertical-align:middle; margin-left:4px;",
            ),
            style="display:flex; align-items:center;",
        ),
        ui.p("Gerador de Fichas", class_="text-muted"),
        ui.hr(),
        ui.tags.label(
            ui.tags.i(
                "upload_file",
                class_="material-icons",
                style="font-size:18px; vertical-align:middle;",
            ),
            " Planilha de mapeamento",
            style="font-weight:600; margin-bottom:8px; display:block;",
        ),
        ui.input_file(
            "file_upload",
            label="",
            accept=[".xlsx"],
        ),
        ui.hr(),
        ui.output_ui("download_section"),
        ui.div(
            ui.tags.small(
                f"v{__version__} · {__release_date__}",
                class_="text-muted",
            ),
            style="position:absolute; bottom:12px; left:0; width:100%; text-align:center;",
        ),
        width="320px",
    ),
    ui.card(
        ui.card_header(
            ui.tags.i(
                "table_chart",
                class_="material-icons",
                style="font-size:18px; vertical-align:middle; margin-right:6px;",
            ),
            "Dados Processados",
        ),
        ui.output_ui("table_or_placeholder"),
        full_screen=True,
        style="flex:1; min-height:0;",
    ),
    ui.tags.head(
        ui.tags.link(
            href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap",
            rel="stylesheet",
        ),
        ui.tags.link(
            href="https://fonts.googleapis.com/icon?family=Material+Icons",
            rel="stylesheet",
        ),
        ui.tags.style("""
            body, .sidebar, .card, .btn, input, select, table {
                font-family: 'Open Sans', sans-serif !important;
            }
            .shiny-data-grid { height: 100% !important; }
        """),
    ),
    title="PNATRANS - Gerador de Fichas",
    fillable=True,
)


def server(input: Inputs, output: Outputs, session: Session):
    @reactive.calc
    def processed_data() -> pd.DataFrame | None:
        file_info: list[dict] | None = input.file_upload()
        if file_info is None:
            return None
        uploaded_path = Path(file_info[0]["datapath"])
        return process_input(uploaded_path, DICT_PATH)

    @render.ui
    def table_or_placeholder():
        df = processed_data()
        if df is None:
            return ui.div(
                ui.tags.i(
                    "description",
                    class_="material-icons",
                    style="font-size:48px; color:#adb5bd;",
                ),
                ui.p(
                    "Envie a planilha para visualizar os dados.",
                    class_="text-muted mt-2",
                ),
                style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; padding:60px 0;",
            )
        return ui.output_data_frame("preview_table")

    @render.data_frame
    def preview_table():
        df = processed_data()
        if df is None:
            return pd.DataFrame()
        display_cols = [c for c in PREVIEW_COLS if c in df.columns]
        return render.DataGrid(
            df[display_cols],
            width="100%",
            height="100%",
            selection_mode="rows",
        )

    @reactive.calc
    def export_data() -> pd.DataFrame | None:
        """DataFrame a ser exportado: subset selecionado ou todas as linhas."""
        df = processed_data()
        if df is None:
            return None
        selection = preview_table.cell_selection()
        if selection is not None:
            rows = list(selection.get("rows", ()))
            if rows:
                return df.iloc[rows].reset_index(drop=True)
        return df

    @render.ui
    def download_section():
        df = processed_data()
        if df is None:
            return ui.p(
                "Envie a planilha para habilitar a exportação.",
                class_="text-muted",
            )

        export_df = export_data()
        n_export = 0 if export_df is None else len(export_df)
        n_total = len(df)
        if n_export == n_total:
            selection_label = f"Exportando todas as {n_total} fichas"
        else:
            selection_label = f"Exportando {n_export} de {n_total} fichas selecionadas"

        return ui.div(
            ui.p(
                selection_label,
                class_="text-muted small",
                style="margin-bottom:8px;",
            ),
            ui.download_button(
                "download_pdfs",
                ui.tags.span(
                    ui.tags.i(
                        "download",
                        class_="material-icons",
                        style="font-size:18px; vertical-align:middle; margin-right:6px;",
                    ),
                    "Exportar PDFs (.zip)",
                ),
                class_="btn-primary w-100",
            ),
            ui.download_button(
                "download_docxs",
                ui.tags.span(
                    ui.tags.i(
                        "description",
                        class_="material-icons",
                        style="font-size:18px; vertical-align:middle; margin-right:6px;",
                    ),
                    "Exportar DOCX (.zip)",
                ),
                class_="btn-primary w-100 mt-2",
            ),
            ui.download_button(
                "download_csvs",
                ui.tags.span(
                    ui.tags.i(
                        "table_view",
                        class_="material-icons",
                        style="font-size:18px; vertical-align:middle; margin-right:6px;",
                    ),
                    "Exportar CSVs (.zip)",
                ),
                class_="btn-outline-primary w-100 mt-2",
            ),
        )

    async def _generate_and_zip(fmt: str, zip_name: str):
        df = export_data()
        if df is None or df.empty:
            return

        n = len(df)
        ui.notification_show(
            f"Gerando fichas... 0/{n}",
            id=NOTIFICATION_ID,
            duration=None,
            close_button=False,
            type="message",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            docs_dir = tmpdir_path / "docs"

            loop = asyncio.get_running_loop()

            def on_progress(current, total):
                async def _notify():
                    ui.notification_show(
                        f"Gerando fichas... {current}/{total}",
                        id=NOTIFICATION_ID,
                        duration=None,
                        close_button=False,
                        type="message",
                    )

                asyncio.run_coroutine_threadsafe(_notify(), loop)

            doc_files = await asyncio.to_thread(
                generate_documents, df, docs_dir, fmt, on_progress
            )

            zip_path = tmpdir_path / zip_name
            create_zip(doc_files, zip_path)

            ui.notification_remove(NOTIFICATION_ID)
            ui.notification_show(
                f"{len(doc_files)} fichas geradas com sucesso!",
                duration=5,
                type="message",
            )

            with open(zip_path, "rb") as f:
                yield f.read()

    @render.download(filename="fichas_pnatrans_pdf.zip")
    async def download_pdfs():
        async for chunk in _generate_and_zip("pdf", "fichas_pnatrans_pdf.zip"):
            yield chunk

    @render.download(filename="fichas_pnatrans_docx.zip")
    async def download_docxs():
        async for chunk in _generate_and_zip("docx", "fichas_pnatrans_docx.zip"):
            yield chunk

    @render.download(filename="produtos_pnatrans.zip")
    async def download_csvs():
        df = export_data()
        if df is None or df.empty:
            return

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "produtos_pnatrans.zip"
            generate_csvs_zip(df, zip_path)

            with open(zip_path, "rb") as f:
                yield f.read()


app = App(app_ui, server)
