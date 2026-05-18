# SGPA 2026 — Sistema de Gestão Pedagógica e Aprendizagem

> Solução de engenharia de dados para o setor público, unindo automação em nuvem e gestão de indicadores de performance.
> Escola Estadual República do Suriname — SEDUC SP

---

## 📋 O que o sistema faz

Monitora automaticamente as entregas pedagógicas dos professores via Google Drive, gerando dashboards, análises com IA e alertas automáticos.

### Documentos monitorados
| Documento | Frequência | Prazo |
|---|---|---|
| 📅 Agenda de Trabalho | Semanal (seg–sex) | Toda semana |
| 📋 PEI (Elegíveis) | Semestral | 31/05/2026 |
| 📚 Guia de Aprendizagem | Semestral | 30/06/2026 |
| 📄 PDI | Semestral | 30/06/2026 |
| 📁 Planejamento | Semestral | 30/06/2026 |
| 🗂️ Evidências PEI SP | Mensal | 30/06/2026 |

### Indicadores de proatividade
- 🚀 **ADIANTADO** — entregou na segunda ou terça
- 👍 **REGULAR** — entregou na quarta ou quinta
- 🔔 **ÚLTIMO DIA** — entregou na sexta
- ❌ **PENDENTE** — não entregou na semana

---

## 🗂️ Estrutura do projeto

```
sgpa/
├── main.py                # Dashboard principal no terminal
├── analisar_perfil.py     # Análise de perfil com IA (Claude)
├── alunos.py              # Cadastro de alunos
├── alertar_evidencias.py  # Alertas mensais por e-mail
├── drive_scanner.py       # Acesso ao Google Drive e Sheets
├── dashboard.py           # Renderização do dashboard (rich)
├── requirements.txt       # Dependências Python
├── .gitignore             # Arquivos ignorados pelo Git
├── config.py              # ⚠️ NÃO versionar (chaves e IDs)
└── credenciais.json       # ⚠️ NÃO versionar (OAuth2 Google)
```

---

## ⚙️ Setup

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar credenciais Google
- Acesse https://console.cloud.google.com
- Ative **Google Drive API** e **Google Sheets API**
- Crie credencial **OAuth2 → App para computador**
- Baixe o JSON e salve como `credenciais.json`

### 3. Criar `config.py`
```python
CONFIG = {
    "ID_PASTA_MEDIO":       "seu_id_aqui",
    "ID_PASTA_FUNDAMENTAL": "seu_id_aqui",
    "DIAS_LIMITE":          7,
    "SPREADSHEET_ID":       "seu_id_aqui",
    "ABA_PROFESSORES":      "CONFERENCIA_DOCS",
    "COLUNA_NOMES":         0,
    "LINHA_INICIO":         1,
    "CREDENCIAIS_JSON":     "credenciais.json",
    "ANTHROPIC_API_KEY":    "sk-ant-...",
}
```

---

## 🚀 Uso

```bash
# Dashboard completo
python main.py

# Análise de perfil com IA + HTML no navegador
python analisar_perfil.py

# Cadastro de alunos
python alunos.py

# Alertas de evidências por e-mail
python alertar_evidencias.py
```

---

## 🛠️ Tecnologias

- **Python 3.13**
- **Google Drive API v3** — acesso às pastas dos professores
- **Google Sheets API v4** — lista de professores
- **OAuth2** — autenticação com conta Google pessoal
- **Rich** — dashboard colorido no terminal
- **Anthropic Claude** — análise de perfil com IA
- **SMTP Gmail** — envio de alertas por e-mail

---

## ⚠️ Segurança

Nunca versione os arquivos:
- `credenciais.json` — credenciais OAuth2 Google
- `token.json` — token de acesso
- `config.py` — IDs e chave API Anthropic

Esses arquivos estão no `.gitignore` por segurança.

---

*SGPA 2026 · Escola Estadual República do Suriname · SEDUC SP*
