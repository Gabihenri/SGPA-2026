# drive_scanner.py - SGPA 2026
import os
from datetime import datetime, timezone, timedelta
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]
TOKEN_FILE = "token.json"

FUSO_BR = timezone(timedelta(hours=-3))
PRAZO_PEI   = datetime(2026, 5, 31, 23, 59, 59, tzinfo=FUSO_BR)
PRAZO_GUIA  = datetime(2026, 6, 30, 23, 59, 59, tzinfo=FUSO_BR)


def autenticar(caminho_credenciais: str):
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(caminho_credenciais, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    drive = build("drive", "v3", credentials=creds)
    sheets = build("sheets", "v4", credentials=creds)
    return drive, sheets


def mapear_pastas(drive, ids_raiz: list[str]) -> dict[str, dict]:
    mapa = {}

    def _varrer(pasta_id: str):
        query = (
            f"'{pasta_id}' in parents "
            f"and mimeType = 'application/vnd.google-apps.folder' "
            f"and trashed = false"
        )
        page_token = None
        while True:
            resp = drive.files().list(
                q=query,
                fields="nextPageToken, files(id, name)",
                pageToken=page_token,
            ).execute()
            for f in resp.get("files", []):
                nome = f["name"].upper()
                mapa[nome] = {"id": f["id"], "parent_id": pasta_id}
                _varrer(f["id"])
            page_token = resp.get("nextPageToken")
            if not page_token:
                break

    for rid in ids_raiz:
        try:
            _varrer(rid)
        except Exception as e:
            print(f"[AVISO] Falha ao acessar pasta raiz {rid}: {e}")

    return mapa


def buscar_pasta_professor(nome_professor: str, mapa: dict) -> str | None:
    nome_busca = nome_professor.strip().upper()
    for nome_pasta, info in mapa.items():
        if nome_busca in nome_pasta:
            return info["id"]
    return None


def buscar_subpasta(drive, pasta_id: str, nome_subpasta: str) -> str | None:
    query = (
        f"'{pasta_id}' in parents "
        f"and mimeType = 'application/vnd.google-apps.folder' "
        f"and trashed = false"
    )
    try:
        resp = drive.files().list(q=query, fields="files(id, name)").execute()
        for f in resp.get("files", []):
            if nome_subpasta.upper() in f["name"].upper():
                return f["id"]
    except Exception as e:
        print(f"[AVISO] Erro ao buscar subpasta: {e}")
    return None


def inicio_semana_atual() -> datetime:
    agora_local = datetime.now(FUSO_BR)
    dias_ate_segunda = agora_local.weekday()
    segunda = agora_local - timedelta(days=dias_ate_segunda)
    segunda_meia_noite = segunda.replace(hour=0, minute=0, second=0, microsecond=0)
    return segunda_meia_noite.astimezone(timezone.utc)


def classificar_proatividade(weekday: int) -> str:
    if weekday <= 1:
        return "ADIANTADO"
    elif weekday <= 3:
        return "REGULAR"
    else:
        return "ULTIMO DIA"


def verificar_recencia(drive, pasta_id: str, dias_limite: int) -> dict | None:
    inicio = inicio_semana_atual()
    inicio_str = inicio.strftime("%Y-%m-%dT%H:%M:%SZ")
    query = (
        f"'{pasta_id}' in parents "
        f"and modifiedTime >= '{inicio_str}' "
        f"and trashed = false "
        f"and mimeType != 'application/vnd.google-apps.folder'"
    )
    try:
        resp = drive.files().list(
            q=query,
            fields="files(id, name, modifiedTime)",
            orderBy="modifiedTime desc",
            pageSize=10,
        ).execute()
        for f in resp.get("files", []):
            data_utc = datetime.strptime(f["modifiedTime"], "%Y-%m-%dT%H:%M:%S.%fZ")
            data_local = data_utc.replace(tzinfo=timezone.utc).astimezone(FUSO_BR)
            if data_local.weekday() <= 4:
                return {
                    "nome": f["name"],
                    "data": data_local.strftime("%d/%m/%Y %H:%M"),
                    "proatividade": classificar_proatividade(data_local.weekday()),
                }
    except Exception as e:
        print(f"[AVISO] Erro ao verificar pasta {pasta_id}: {e}")
    return None


def verificar_pei(drive, pasta_professor_id: str) -> dict:
    agora = datetime.now(FUSO_BR)
    prazo_ok = agora <= PRAZO_PEI
    pasta_elegiveis_id = buscar_subpasta(drive, pasta_professor_id, "elegiveis")

    if not pasta_elegiveis_id:
        return {"pei_status": "SEM PASTA", "pei_arquivo": "—", "pei_data": "—"}

    query = (
        f"'{pasta_elegiveis_id}' in parents "
        f"and trashed = false "
        f"and mimeType != 'application/vnd.google-apps.folder'"
    )
    try:
        resp = drive.files().list(
            q=query,
            fields="files(id, name, modifiedTime)",
            orderBy="modifiedTime desc",
            pageSize=1,
        ).execute()
        arquivos = resp.get("files", [])
        if arquivos:
            f = arquivos[0]
            data_utc = datetime.strptime(f["modifiedTime"], "%Y-%m-%dT%H:%M:%S.%fZ")
            data_local = data_utc.replace(tzinfo=timezone.utc).astimezone(FUSO_BR)
            return {
                "pei_status":  "ENTREGUE",
                "pei_arquivo": f["name"],
                "pei_data":    data_local.strftime("%d/%m/%Y %H:%M"),
            }
        else:
            return {
                "pei_status":  "PENDENTE" if prazo_ok else "ATRASADO",
                "pei_arquivo": "—",
                "pei_data":    "—",
            }
    except Exception as e:
        print(f"[AVISO] Erro ao verificar PEI: {e}")
        return {"pei_status": "ERRO", "pei_arquivo": "—", "pei_data": "—"}


def verificar_guia(drive, pasta_professor_id: str) -> dict:
    """
    Busca recursivamente qualquer arquivo com 'GUIA DE APRENDIZAGEM' no nome
    dentro da pasta do professor. Prazo: 30/06/2026.
    """
    agora = datetime.now(FUSO_BR)
    prazo_ok = agora <= PRAZO_GUIA

    # Busca em toda a árvore da pasta do professor via fullText/name
    query = (
        f"'{pasta_professor_id}' in parents "
        f"and name contains 'GUIA' "
        f"and trashed = false "
        f"and mimeType != 'application/vnd.google-apps.folder'"
    )

    def _buscar_em(pasta_id: str) -> dict | None:
        """Busca recursiva por arquivo com GUIA DE APRENDIZAGEM no nome."""
        # Busca arquivos diretos com GUIA no nome
        q_files = (
            f"'{pasta_id}' in parents "
            f"and trashed = false "
            f"and mimeType != 'application/vnd.google-apps.folder'"
        )
        try:
            resp = drive.files().list(
                q=q_files,
                fields="files(id, name, modifiedTime)",
            ).execute()
            for f in resp.get("files", []):
                if "GUIA DE APRENDIZAGEM" in f["name"].upper():
                    data_utc = datetime.strptime(f["modifiedTime"], "%Y-%m-%dT%H:%M:%S.%fZ")
                    data_local = data_utc.replace(tzinfo=timezone.utc).astimezone(FUSO_BR)
                    return {
                        "guia_status":  "ENTREGUE",
                        "guia_arquivo": f["name"],
                        "guia_data":    data_local.strftime("%d/%m/%Y %H:%M"),
                    }
        except Exception:
            pass

        # Busca nas subpastas recursivamente
        q_folders = (
            f"'{pasta_id}' in parents "
            f"and mimeType = 'application/vnd.google-apps.folder' "
            f"and trashed = false"
        )
        try:
            resp = drive.files().list(q=q_folders, fields="files(id)").execute()
            for sub in resp.get("files", []):
                resultado = _buscar_em(sub["id"])
                if resultado:
                    return resultado
        except Exception:
            pass

        return None

    resultado = _buscar_em(pasta_professor_id)
    if resultado:
        return resultado

    return {
        "guia_status":  "PENDENTE" if prazo_ok else "ATRASADO",
        "guia_arquivo": "—",
        "guia_data":    "—",
    }




def verificar_pdi(drive, pasta_professor_id: str) -> dict:
    """
    Verifica a pasta PDI dentro da pasta do professor.
    Qualquer arquivo vale. Prazo: 30/06/2026.
    """
    agora = datetime.now(FUSO_BR)
    prazo_ok = agora <= PRAZO_GUIA  # mesmo prazo 30/06

    pasta_id = buscar_subpasta(drive, pasta_professor_id, 'pdi')

    if not pasta_id:
        return {'pdi_status': 'SEM PASTA', 'pdi_arquivo': '—', 'pdi_data': '—'}

    query = (
        f"'{pasta_id}' in parents "
        f"and trashed = false "
        f"and mimeType != 'application/vnd.google-apps.folder'"
    )
    try:
        resp = drive.files().list(
            q=query,
            fields='files(id, name, modifiedTime)',
            orderBy='modifiedTime desc',
            pageSize=1,
        ).execute()
        arquivos = resp.get('files', [])
        if arquivos:
            f = arquivos[0]
            data_utc = datetime.strptime(f['modifiedTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
            data_local = data_utc.replace(tzinfo=timezone.utc).astimezone(FUSO_BR)
            return {
                'pdi_status':  'ENTREGUE',
                'pdi_arquivo': f['name'],
                'pdi_data':    data_local.strftime('%d/%m/%Y %H:%M'),
            }
        else:
            return {
                'pdi_status':  'PENDENTE' if prazo_ok else 'ATRASADO',
                'pdi_arquivo': '—',
                'pdi_data':    '—',
            }
    except Exception as e:
        print(f'[AVISO] Erro ao verificar PDI: {e}')
        return {'pdi_status': 'ERRO', 'pdi_arquivo': '—', 'pdi_data': '—'}


def verificar_planejamento(drive, pasta_professor_id: str) -> dict:
    """
    Verifica a pasta PLANEJAMENTO dentro da pasta do professor.
    Qualquer arquivo vale. Prazo: 30/06/2026.
    """
    agora = datetime.now(FUSO_BR)
    prazo_ok = agora <= PRAZO_GUIA

    pasta_id = buscar_subpasta(drive, pasta_professor_id, 'planejamento')

    if not pasta_id:
        return {'plan_status': 'SEM PASTA', 'plan_arquivo': '—', 'plan_data': '—'}

    query = (
        f"'{pasta_id}' in parents "
        f"and trashed = false "
        f"and mimeType != 'application/vnd.google-apps.folder'"
    )
    try:
        resp = drive.files().list(
            q=query,
            fields='files(id, name, modifiedTime)',
            orderBy='modifiedTime desc',
            pageSize=1,
        ).execute()
        arquivos = resp.get('files', [])
        if arquivos:
            f = arquivos[0]
            data_utc = datetime.strptime(f['modifiedTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
            data_local = data_utc.replace(tzinfo=timezone.utc).astimezone(FUSO_BR)
            return {
                'plan_status':  'ENTREGUE',
                'plan_arquivo': f['name'],
                'plan_data':    data_local.strftime('%d/%m/%Y %H:%M'),
            }
        else:
            return {
                'plan_status':  'PENDENTE' if prazo_ok else 'ATRASADO',
                'plan_arquivo': '—',
                'plan_data':    '—',
            }
    except Exception as e:
        print(f'[AVISO] Erro ao verificar Planejamento: {e}')
        return {'plan_status': 'ERRO', 'plan_arquivo': '—', 'plan_data': '—'}
def obter_professores(sheets, spreadsheet_id: str, aba: str, coluna: int, linha_inicio: int) -> list[str]:
    result = sheets.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{aba}!A:A",
    ).execute()
    valores = result.get("values", [])
    nomes = []
    for i, linha in enumerate(valores):
        if i < linha_inicio:
            continue
        nome = linha[coluna].strip() if linha else ""
        nomes.append(nome)
    return nomes


def verificar_evidencias(drive, pasta_professor_id: str) -> dict:
    """
    Verifica a pasta 'evidencias' dentro da pasta do professor.
    Conta quantos arquivos existem. Prazo: 30/06/2026.
    Qualquer quantidade já indica que está desenvolvendo.
    """
    agora = datetime.now(FUSO_BR)
    prazo_ok = agora <= PRAZO_GUIA  # mesmo prazo: 30/06/2026

    pasta_ev_id = buscar_subpasta(drive, pasta_professor_id, "evidencias")

    if not pasta_ev_id:
        return {
            "ev_status":    "SEM PASTA",
            "ev_quantidade": 0,
            "ev_data":      "—",
        }

    query = (
        f"'{pasta_ev_id}' in parents "
        f"and trashed = false "
        f"and mimeType != 'application/vnd.google-apps.folder'"
    )
    try:
        # Busca todos os arquivos para contar
        arquivos = []
        page_token = None
        while True:
            resp = drive.files().list(
                q=query,
                fields="nextPageToken, files(id, name, modifiedTime)",
                pageToken=page_token,
            ).execute()
            arquivos.extend(resp.get("files", []))
            page_token = resp.get("nextPageToken")
            if not page_token:
                break

        quantidade = len(arquivos)

        if quantidade > 0:
            # Pega a data do mais recente
            mais_recente = max(arquivos, key=lambda f: f["modifiedTime"])
            data_utc = datetime.strptime(mais_recente["modifiedTime"], "%Y-%m-%dT%H:%M:%S.%fZ")
            data_local = data_utc.replace(tzinfo=timezone.utc).astimezone(FUSO_BR)
            return {
                "ev_status":     "ATIVO",
                "ev_quantidade":  quantidade,
                "ev_data":        data_local.strftime("%d/%m/%Y"),
            }
        else:
            return {
                "ev_status":     "PENDENTE" if prazo_ok else "ATRASADO",
                "ev_quantidade":  0,
                "ev_data":        "—",
            }
    except Exception as e:
        print(f"[AVISO] Erro ao verificar evidências: {e}")
        return {"ev_status": "ERRO", "ev_quantidade": 0, "ev_data": "—"}
