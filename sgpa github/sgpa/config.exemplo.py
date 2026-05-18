# config.exemplo.py - SGPA 2026
# Copie este arquivo para config.py e preencha com seus dados reais
# NUNCA envie o config.py para o GitHub

CONFIG = {
    # IDs das pastas raiz no Google Drive
    "ID_PASTA_MEDIO":       "SEU_ID_PASTA_MEDIO_AQUI",
    "ID_PASTA_FUNDAMENTAL": "SEU_ID_PASTA_FUNDAMENTAL_AQUI",

    # Quantos dias um arquivo pode ter para ser considerado "no prazo"
    "DIAS_LIMITE": 7,

    # ID da planilha Google Sheets
    "SPREADSHEET_ID": "SEU_SPREADSHEET_ID_AQUI",

    # Nome da aba com a lista de professores
    "ABA_PROFESSORES": "CONFERENCIA_DOCS",

    # Coluna e linha dos dados (0-indexed)
    "COLUNA_NOMES": 0,
    "LINHA_INICIO": 1,

    # Arquivo de credenciais OAuth2 Google
    "CREDENCIAIS_JSON": "credenciais.json",

    # Chave API da Anthropic para análise de perfil com IA
    "ANTHROPIC_API_KEY": "SUA_CHAVE_ANTHROPIC_AQUI",
}
