library(tidyverse)
library(readxl)
library(janitor)
library(quarto)
library(lubridate)

# Ler os dados
path_dic_pnatrans = "data/arquivos_pnatrans.xlsx"
path_input_respostas = "data/Mapeamento de produtos e ações realizados pelo Detran-SP para o Painel Pnatrans.xlsx"

df_dic_pnatrans <- read_excel(path_dic_pnatrans, sheet = 4)
df_input_respostas <- read_excel(path_input_respostas) |>
    clean_names()

# Processar dados
df_input_clean <- df_input_respostas |>
    unite("acao", starts_with("acao"), na.rm = TRUE) |>
    unite("produto", starts_with("produto"), na.rm = TRUE) |>
    unite(
        "titulo_do_produto_detran",
        starts_with("titulo_do_produto_detran"),
        na.rm = TRUE
    ) |>
    unite(
        "descricao_e_justificativa",
        starts_with("descricao_e_justificativa"),
        na.rm = TRUE
    ) |>
    unite("indicador", starts_with("indicador"), na.rm = TRUE) |>
    unite("ano_referencia", starts_with("ano_referencia"), na.rm = TRUE) |>
    unite("valor_resultado", starts_with("valor_resultado"), na.rm = TRUE) |>
    unite("area_responsavel", starts_with("area_responsavel"), na.rm = TRUE) |>
    unite(
        "links_comprovatorios",
        starts_with("links_comprovatorios"),
        na.rm = TRUE
    ) |>
    unite(
        "arquivos_comprovatorios",
        starts_with("arquivos_comprovatorios"),
        na.rm = TRUE
    ) |>
    mutate(
        # Normalizar quebras de linha
        descricao_e_justificativa = str_replace_all(
            descricao_e_justificativa,
            "\r\n",
            "\n"
        ),
        descricao_e_justificativa = str_replace_all(
            descricao_e_justificativa,
            "\r",
            "\n"
        ),
        # Adicionar quebra dupla antes de bullets para criar lista em markdown
        descricao_e_justificativa = str_replace_all(
            descricao_e_justificativa,
            "\n•",
            "\n\n•"
        ),
        # Adicionar quebra dupla após o último bullet (antes de iniciar novo parágrafo)
        descricao_e_justificativa = str_replace_all(
            descricao_e_justificativa,
            "\\. \n(?=[A-Z](?!•))",
            "\\. \n\n"
        ),
        links_comprovatorios = str_remove_all(
            links_comprovatorios,
            "\r\n"
        )
    )

df_input <- df_input_clean |>
    # Primeiro, pegar o nome da ação (join apenas por acao)
    left_join(
        df_dic_pnatrans |>
            select(codigo_acao, nome_acao) |>
            distinct(),
        by = c("acao" = "codigo_acao")
    ) |>
    # Depois, tentar pegar o nome do produto (join por acao + produto)
    left_join(
        df_dic_pnatrans |>
            select(codigo_acao, codigo_produto, nome_produto),
        by = c("acao" = "codigo_acao", "produto" = "codigo_produto")
    )

# Salvar dados processados para o main.qmd usar
saveRDS(df_input, "data/processed_data.rds")
message("Dados processados e salvos em data/processed_data.rds")

# Criar diretório de output se não existir
if (!dir.exists("output")) {
    dir.create("output")
}

# Timestamp para esta execução
datetime_stamp <- format(now(), "%Y%m%d_%H%M%S")

# Iterar sobre cada linha e gerar PDF
message(glue::glue("Gerando {nrow(df_input)} relatórios..."))

for (i in 1:nrow(df_input)) {
    message(glue::glue("\nProcessando linha {i}/{nrow(df_input)}..."))

    # Extrair informações da linha atual
    row_data <- df_input[i, ]

    # Criar nome do arquivo
    # Limpar caracteres especiais do nome do produto detran
    produto_detran_clean <- row_data$titulo_do_produto_detran |>
        iconv(from = "UTF-8", to = "ASCII//TRANSLIT") |>  # Converte acentos
        str_replace_all("[^[:alnum:][:space:]-]", "") |>  # Remove caracteres especiais
        str_replace_all("\\s+", "_") |>  # Substitui espaços por underscore
        str_trunc(50, ellipsis = "")  # Limita a 50 caracteres

    # Limpar o código do produto também
    produto_clean <- row_data$produto |>
        str_replace_all("\\s+", "_")

    output_filename <- glue::glue(
        "{row_data$acao}_{produto_clean}_{produto_detran_clean}_{datetime_stamp}.pdf"
    )

    output_path <- file.path("output", output_filename)

    message(glue::glue("  -> Gerando: {output_filename}"))

    # Renderizar o documento com parâmetro row_index
    tryCatch({
        quarto_render(
            input = "main.qmd",
            output_file = output_filename,
            output_format = "typst",
            execute_params = list(row_index = i),
            quiet = TRUE
        )

        # Mover o arquivo gerado para a pasta output
        if (file.exists(output_filename)) {
            file.rename(output_filename, output_path)
        }

        message(glue::glue("  ✓ Sucesso: {output_filename}"))
    }, error = function(e) {
        message(glue::glue("  ✗ Erro ao gerar {output_filename}: {e$message}"))
    })
}

message(glue::glue("\n\nConcluído! {nrow(df_input)} relatórios gerados na pasta 'output/'."))
