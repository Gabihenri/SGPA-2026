#!/usr/bin/env python3
# main.py - SGPA 2026

from config import CONFIG
from drive_scanner import (
    autenticar,
    mapear_pastas,
    buscar_pasta_professor,
    verificar_recencia,
    verificar_pei,
    verificar_guia,
    verificar_evidencias,
    verificar_pdi,
    verificar_planejamento,
    obter_professores,
)
from dashboard import console, exibir_dashboard


def main():
    console.print("\n[bold cyan]SGPA 2026[/] · Iniciando sincronização...\n")

    console.print("[dim]→ Autenticando com Google...[/]")
    drive, sheets = autenticar(CONFIG["CREDENCIAIS_JSON"])

    console.print("[dim]→ Lendo lista de professores...[/]")
    professores = obter_professores(
        sheets,
        spreadsheet_id=CONFIG["SPREADSHEET_ID"],
        aba=CONFIG["ABA_PROFESSORES"],
        coluna=CONFIG["COLUNA_NOMES"],
        linha_inicio=CONFIG["LINHA_INICIO"],
    )
    professores = [p for p in professores if p]

    console.print("[dim]→ Mapeando pastas do Drive (pode levar alguns segundos)...[/]")
    ids_raiz = [CONFIG["ID_PASTA_MEDIO"], CONFIG["ID_PASTA_FUNDAMENTAL"]]
    mapa = mapear_pastas(drive, ids_raiz)
    console.print(f"[dim]   {len(mapa)} pastas encontradas.[/]\n")

    resultados = []
    dias = CONFIG["DIAS_LIMITE"]
    total = len(professores)

    for i, nome in enumerate(professores, start=1):
        console.print(f"[dim]→ Verificando {i}/{total}: {nome}...[/]")
        pasta_id = buscar_pasta_professor(nome, mapa)

        if not pasta_id:
            resultados.append({
                "professor":     nome,
                "status":        "PENDENTE",
                "observacao":    "Pasta não localizada",
                "arquivo":       "—",
                "data":          "—",
                "proatividade":  "PENDENTE",
                "pei_status":    "SEM PASTA",
                "pei_arquivo":   "—",
                "pei_data":      "—",
                "guia_status":   "SEM PASTA",
                "guia_arquivo":  "—",
                "guia_data":     "—",
                "ev_status":     "SEM PASTA",
                "ev_quantidade":  0,
                "ev_data":       "—",
                "pdi_status":    "SEM PASTA",
                "pdi_arquivo":   "—",
                "pdi_data":      "—",
                "plan_status":   "SEM PASTA",
                "plan_arquivo":  "—",
                "plan_data":     "—",
            })
            continue

        info = verificar_recencia(drive, pasta_id, dias)
        pei  = verificar_pei(drive, pasta_id)
        guia = verificar_guia(drive, pasta_id)
        ev   = verificar_evidencias(drive, pasta_id)
        pdi  = verificar_pdi(drive, pasta_id)
        plan = verificar_planejamento(drive, pasta_id)

        if info:
            resultados.append({
                "professor":    nome,
                "status":       "NO PRAZO",
                "arquivo":      info["nome"],
                "data":         info["data"],
                "proatividade": info["proatividade"],
                **pei, **guia, **ev, **pdi, **plan,
            })
        else:
            resultados.append({
                "professor":    nome,
                "status":       "PENDENTE",
                "observacao":   "Sem arquivo esta semana",
                "arquivo":      "—",
                "data":         "—",
                "proatividade": "PENDENTE",
                **pei, **guia, **ev, **pdi, **plan,
            })

    # Salva resultado para uso da análise IA
    import json
    with open("ultimo_resultado.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    exibir_dashboard(resultados, dias)


if __name__ == "__main__":
    main()
