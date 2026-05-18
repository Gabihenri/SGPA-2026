# dashboard.py - SGPA 2026
import json
import os
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import box
from rich.text import Text

console = Console()
HISTORICO_FILE = "historico.json"

NIVEIS = {
    "ADIANTADO":  {"label": "🚀 ADIANTADO",  "cor": "bold cyan"},
    "REGULAR":    {"label": "👍 REGULAR",     "cor": "bold green"},
    "ULTIMO DIA": {"label": "🔔 ÚLTIMO DIA",  "cor": "bold yellow"},
    "PENDENTE":   {"label": "❌ PENDENTE",    "cor": "bold red"},
}

DOC_CONFIG = {
    "ENTREGUE":  {"label": "✅ ENTREGUE",  "cor": "bold green"},
    "PENDENTE":  {"label": "⏳ PENDENTE",  "cor": "bold yellow"},
    "ATRASADO":  {"label": "❌ ATRASADO",  "cor": "bold red"},
    "SEM PASTA": {"label": "📁 SEM PASTA", "cor": "dim"},
    "ERRO":      {"label": "⚠️ ERRO",      "cor": "bold red"},
}

EV_CONFIG = {
    "ATIVO":              {"cor": "bold green"},
    "SEM EVIDENCIA MES":  {"cor": "bold magenta"},
    "PENDENTE":           {"cor": "bold yellow"},
    "ATRASADO":           {"cor": "bold red"},
    "SEM PASTA":          {"cor": "dim"},
    "ERRO":               {"cor": "bold red"},
}


def semana_atual() -> str:
    hoje = datetime.now()
    return f"{hoje.year}-W{hoje.isocalendar()[1]:02d}"


def carregar_historico() -> dict:
    if os.path.exists(HISTORICO_FILE):
        with open(HISTORICO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def salvar_historico(historico: dict):
    with open(HISTORICO_FILE, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)


def registrar_semana(resultados: list[dict]) -> dict:
    historico = carregar_historico()
    semana = semana_atual()
    contadores = {
        "ADIANTADO":    sum(1 for r in resultados if r.get("proatividade") == "ADIANTADO"),
        "REGULAR":      sum(1 for r in resultados if r.get("proatividade") == "REGULAR"),
        "ULTIMO DIA":   sum(1 for r in resultados if r.get("proatividade") == "ULTIMO DIA"),
        "PENDENTE":     sum(1 for r in resultados if r["status"] == "PENDENTE"),
        "PEI_ENTREGUE": sum(1 for r in resultados if r.get("pei_status") == "ENTREGUE"),
        "PEI_PENDENTE": sum(1 for r in resultados if r.get("pei_status") in ("PENDENTE", "ATRASADO")),
        "GUIA_ENTREGUE":sum(1 for r in resultados if r.get("guia_status") == "ENTREGUE"),
        "GUIA_PENDENTE":sum(1 for r in resultados if r.get("guia_status") in ("PENDENTE", "ATRASADO")),
        "total":        len(resultados),
        "data":         datetime.now().strftime("%d/%m/%Y %H:%M"),
    }
    historico[semana] = contadores
    salvar_historico(historico)
    return historico


def exibir_grafico_barras(contadores: dict, titulo: str):
    total = contadores.get("total", 1) or 1
    itens = [
        ("🚀 ADIANTADO",  contadores.get("ADIANTADO", 0),  "cyan"),
        ("👍 REGULAR",    contadores.get("REGULAR", 0),    "green"),
        ("🔔 ÚLTIMO DIA", contadores.get("ULTIMO DIA", 0), "yellow"),
        ("❌ PENDENTE",   contadores.get("PENDENTE", 0),   "red"),
    ]
    table = Table(box=box.SIMPLE, show_header=False, expand=True, padding=(0, 1))
    table.add_column("Status", min_width=16)
    table.add_column("Barra",  min_width=40)
    table.add_column("Qtd",    width=5, justify="right")
    table.add_column("%",      width=6, justify="right")
    for label, qtd, cor in itens:
        pct = qtd / total
        barra = "█" * int(pct * 40)
        table.add_row(
            Text(label, style=f"bold {cor}"),
            Text(barra, style=cor),
            Text(str(qtd), style=f"bold {cor}"),
            Text(f"{pct*100:.0f}%", style="dim"),
        )
    console.print(Panel(table, title=f"[bold white]{titulo}[/]", border_style="white"))


def exibir_historico(historico: dict):
    if len(historico) < 2:
        console.print("[dim]  Histórico disponível a partir da 2ª semana de uso.[/]\n")
        return
    table = Table(box=box.ROUNDED, show_header=True,
                  header_style="bold white on grey23", expand=True)
    table.add_column("Semana",       min_width=10)
    table.add_column("Data",         min_width=14)
    table.add_column("🚀 Adiant.",   width=9, justify="center")
    table.add_column("👍 Regular",   width=9, justify="center")
    table.add_column("🔔 Último",    width=9, justify="center")
    table.add_column("❌ Pendente",  width=9, justify="center")
    table.add_column("✅ PEI",       width=8, justify="center")
    table.add_column("✅ Guia",      width=8, justify="center")
    table.add_column("Conform.",     width=9, justify="center")
    for semana, c in sorted(historico.items()):
        total = c.get("total", 1) or 1
        no_prazo = c.get("ADIANTADO", 0) + c.get("REGULAR", 0) + c.get("ULTIMO DIA", 0)
        taxa = f"{no_prazo/total*100:.0f}%"
        table.add_row(
            semana,
            c.get("data", "—"),
            Text(str(c.get("ADIANTADO", 0)),    style="bold cyan"),
            Text(str(c.get("REGULAR", 0)),      style="bold green"),
            Text(str(c.get("ULTIMO DIA", 0)),   style="bold yellow"),
            Text(str(c.get("PENDENTE", 0)),     style="bold red"),
            Text(str(c.get("GUIA_ENTREGUE", 0)),style="bold green"),
            Text(str(c.get("PEI_ENTREGUE", 0)), style="bold green"),
            Text(taxa, style="bold white"),
        )
    console.print(Panel(table, title="[bold white]📊 Histórico por Semana[/]",
                        border_style="white"))
    console.print()


def exibir_dashboard(resultados: list[dict], dias_limite: int):
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    adiantados    = sum(1 for r in resultados if r.get("proatividade") == "ADIANTADO")
    regulares     = sum(1 for r in resultados if r.get("proatividade") == "REGULAR")
    ultimo_dia    = sum(1 for r in resultados if r.get("proatividade") == "ULTIMO DIA")
    pendentes     = sum(1 for r in resultados if r["status"] == "PENDENTE")
    no_prazo      = sum(1 for r in resultados if r["status"] == "NO PRAZO")
    pei_entregue  = sum(1 for r in resultados if r.get("pei_status") == "ENTREGUE")
    pei_pendente  = sum(1 for r in resultados if r.get("pei_status") in ("PENDENTE", "ATRASADO"))
    guia_entregue = sum(1 for r in resultados if r.get("guia_status") == "ENTREGUE")
    guia_pendente = sum(1 for r in resultados if r.get("guia_status") in ("PENDENTE", "ATRASADO"))
    ev_ativos     = sum(1 for r in resultados if r.get("ev_status") == "ATIVO")
    pdi_entregue  = sum(1 for r in resultados if r.get("pdi_status") == "ENTREGUE")
    pdi_pendente  = sum(1 for r in resultados if r.get("pdi_status") in ("PENDENTE", "ATRASADO", "SEM PASTA"))
    plan_entregue = sum(1 for r in resultados if r.get("plan_status") == "ENTREGUE")
    plan_pendente = sum(1 for r in resultados if r.get("plan_status") in ("PENDENTE", "ATRASADO", "SEM PASTA"))
    ev_pendentes  = sum(1 for r in resultados if r.get("ev_status") in ("PENDENTE", "ATRASADO", "SEM PASTA"))
    ev_total_arq  = sum(r.get("ev_quantidade", 0) for r in resultados)
    total         = len(resultados)

    # ── Cabeçalho ─────────────────────────────────────────────────────────────
    console.print()
    console.print(Panel(
        f"[bold cyan]SGPA 2026[/] · Monitorização de Entregas\n"
        f"[dim]Atualizado em {agora}  ·  Semana: {semana_atual()}  ·  "
        f"Prazo PEI: 31/05/2026  ·  Prazo Guia: 30/06/2026[/]",
        style="bold white on dark_blue", expand=False,
    ))
    console.print()

    # ── Cards agenda ───────────────────────────────────────────────────────────
    taxa = f"{(no_prazo/total*100):.0f}%" if total else "—"
    console.print(Columns([
        Panel(f"[bold white]{total}[/]\n[dim]Total[/]",               style="blue",   expand=True),
        Panel(f"[bold cyan]{adiantados}[/]\n[dim]🚀 Adiantado[/]",    style="cyan",   expand=True),
        Panel(f"[bold green]{regulares}[/]\n[dim]👍 Regular[/]",      style="green",  expand=True),
        Panel(f"[bold yellow]{ultimo_dia}[/]\n[dim]🔔 Último Dia[/]", style="yellow", expand=True),
        Panel(f"[bold red]{pendentes}[/]\n[dim]❌ Pendente[/]",       style="red",    expand=True),
        Panel(f"[bold white]{taxa}[/]\n[dim]Conformidade[/]",          style="white",  expand=True),
    ]))
    console.print()

    # ── Cards PEI e Guia ───────────────────────────────────────────────────────
    taxa_pei  = f"{(pei_entregue/total*100):.0f}%"  if total else "—"
    taxa_guia = f"{(guia_entregue/total*100):.0f}%" if total else "—"
    console.print(Columns([
        Panel(f"[bold green]{pei_entregue}[/]\n[dim]✅ PEI Entregue[/]",    style="green",  expand=True),
        Panel(f"[bold yellow]{pei_pendente}[/]\n[dim]⏳ PEI Pendente[/]",   style="yellow", expand=True),
        Panel(f"[bold white]{taxa_pei}[/]\n[dim]% PEI  · Prazo 31/05[/]",   style="white",  expand=True),
        Panel(f"[bold green]{guia_entregue}[/]\n[dim]✅ Guia Entregue[/]",  style="green",  expand=True),
        Panel(f"[bold yellow]{guia_pendente}[/]\n[dim]⏳ Guia Pendente[/]", style="yellow", expand=True),
        Panel(f"[bold white]{taxa_guia}[/]\n[dim]% Guia · Prazo 30/06[/]",  style="white",  expand=True),
    ]))
    console.print()

    # ── Cards Evidências ──────────────────────────────────────────────────────
    taxa_ev = f"{(ev_ativos/total*100):.0f}%" if total else "—"
    console.print(Columns([
        Panel(f"[bold green]{ev_ativos}[/]\n[dim]Ev. Ativos[/]",       style="green",  expand=True),
        Panel(f"[bold yellow]{ev_pendentes}[/]\n[dim]Ev. Pendentes[/]", style="yellow", expand=True),
        Panel(f"[bold cyan]{ev_total_arq}[/]\n[dim]Total Arquivos[/]",  style="cyan",   expand=True),
        Panel(f"[bold white]{taxa_ev}[/]\n[dim]% Ativos 30/06[/]",      style="white",  expand=True),
    ]))
    console.print()

    # ── Cards PDI e Planejamento ───────────────────────────────────────────────
    taxa_pdi  = f"{(pdi_entregue/total*100):.0f}%" if total else "—"
    taxa_plan = f"{(plan_entregue/total*100):.0f}%" if total else "—"
    console.print(Columns([
        Panel(f"[bold green]{pdi_entregue}[/]\n[dim]PDI Entregue[/]",       style="green",  expand=True),
        Panel(f"[bold yellow]{pdi_pendente}[/]\n[dim]PDI Pendente[/]",      style="yellow", expand=True),
        Panel(f"[bold white]{taxa_pdi}[/]\n[dim]% PDI 30/06[/]",            style="white",  expand=True),
        Panel(f"[bold green]{plan_entregue}[/]\n[dim]Planej. Entregue[/]",  style="green",  expand=True),
        Panel(f"[bold yellow]{plan_pendente}[/]\n[dim]Planej. Pendente[/]", style="yellow", expand=True),
        Panel(f"[bold white]{taxa_plan}[/]\n[dim]% Planej. 30/06[/]",       style="white",  expand=True),
    ]))
    console.print()


    # ── Gráfico agenda ─────────────────────────────────────────────────────────
    exibir_grafico_barras({
        "ADIANTADO": adiantados, "REGULAR": regulares,
        "ULTIMO DIA": ultimo_dia, "PENDENTE": pendentes, "total": total,
    }, f"📊 Agenda Semanal — {semana_atual()}")
    console.print()

    # ── Tabela principal ───────────────────────────────────────────────────────
    table = Table(box=box.ROUNDED, show_header=True,
                  header_style="bold white on grey23", expand=True)
    table.add_column("#",              style="dim", width=4, justify="right")
    table.add_column("Professor",      style="bold", min_width=16)
    table.add_column("Último Arquivo", min_width=22)
    table.add_column("Data",           min_width=14, justify="center")
    table.add_column("Situação",       min_width=12, justify="center")
    table.add_column("Proatividade",   min_width=14, justify="center")
    table.add_column("PEI",            min_width=12, justify="center")
    table.add_column("Guia Aprend.",   min_width=12, justify="center")
    table.add_column("Evidências",     min_width=12, justify="center")
    table.add_column("PDI",            min_width=12, justify="center")
    table.add_column("Planejamento",   min_width=12, justify="center")

    for i, r in enumerate(resultados, start=1):
        status  = r["status"]
        prov    = r.get("proatividade", "PENDENTE")
        nivel   = NIVEIS.get(prov, NIVEIS["PENDENTE"])
        pei_cfg = DOC_CONFIG.get(r.get("pei_status",  "SEM PASTA"), DOC_CONFIG["ERRO"])
        gui_cfg = DOC_CONFIG.get(r.get("guia_status", "SEM PASTA"), DOC_CONFIG["ERRO"])
        ev_st   = r.get("ev_status", "SEM PASTA")
        pdi_cfg = DOC_CONFIG.get(r.get("pdi_status",  "SEM PASTA"), DOC_CONFIG["ERRO"])
        pln_cfg = DOC_CONFIG.get(r.get("plan_status", "SEM PASTA"), DOC_CONFIG["ERRO"])
        ev_qtd  = r.get("ev_quantidade", 0)
        ev_cor  = EV_CONFIG.get(ev_st, EV_CONFIG["ERRO"])["cor"]
        if ev_st == "ATIVO":
            ev_label = f"🗂️ {ev_qtd} arq."
        elif ev_st == "SEM EVIDENCIA MES":
            ev_label = f"⚠️ {ev_qtd} arq. (sem novo)"
        elif ev_st == "PENDENTE":
            ev_label = "⏳ PENDENTE"
        elif ev_st == "SEM PASTA":
            ev_label = "📁 SEM PASTA"
        else:
            ev_label = "❌ ATRASADO"

        if status == "NO PRAZO":
            cor_status, label_status = "bold green", "✅ NO PRAZO"
            cor_prof = "green"
            label_prov, cor_prov = nivel["label"], nivel["cor"]
        else:
            cor_status, label_status = "bold red", "❌ PENDENTE"
            cor_prof = "red"
            label_prov, cor_prov = "—", "dim"

        table.add_row(
            str(i),
            Text(r["professor"], style=cor_prof),
            Text(r.get("arquivo", r.get("observacao", "—")), style="dim"),
            Text(r.get("data", "—"), style="dim"),
            Text(label_status, style=cor_status),
            Text(label_prov, style=cor_prov),
            Text(pei_cfg["label"], style=pei_cfg["cor"]),
            Text(gui_cfg["label"], style=gui_cfg["cor"]),
            Text(ev_label, style=ev_cor),
            Text(pdi_cfg["label"], style=pdi_cfg["cor"]),
            Text(pln_cfg["label"], style=pln_cfg["cor"]),
        )

    console.print(table)
    console.print()

    # ── Pendentes agenda ───────────────────────────────────────────────────────
    p_agenda = [r["professor"] for r in resultados if r["status"] == "PENDENTE"]
    if p_agenda:
        console.print(Panel(
            "\n".join(f"  [red]·[/] {p}" for p in p_agenda),
            title="[bold red]Agenda — Pendentes[/]", border_style="red"))
        console.print()

    # ── Pendentes PEI ─────────────────────────────────────────────────────────
    p_pei = [r["professor"] for r in resultados if r.get("pei_status") in ("PENDENTE", "ATRASADO", "SEM PASTA")]
    if p_pei:
        console.print(Panel(
            "\n".join(f"  [yellow]·[/] {p}" for p in p_pei),
            title="[bold yellow]PEI — Pendentes (Prazo: 31/05/2026)[/]", border_style="yellow"))
        console.print()

    # ── Pendentes Guia ────────────────────────────────────────────────────────
    p_guia = [r["professor"] for r in resultados if r.get("guia_status") in ("PENDENTE", "ATRASADO", "SEM PASTA")]
    if p_guia:
        console.print(Panel(
            "\n".join(f"  [yellow]·[/] {p}" for p in p_guia),
            title="[bold yellow]Guia de Aprendizagem — Pendentes (Prazo: 30/06/2026)[/]", border_style="yellow"))
        console.print()

    # ── Pendentes PDI ─────────────────────────────────────────────────────────
    p_pdi = [r["professor"] for r in resultados if r.get("pdi_status") in ("PENDENTE", "ATRASADO", "SEM PASTA")]
    if p_pdi:
        console.print(Panel(
            "\n".join(f"  [yellow]·[/] {p}" for p in p_pdi),
            title="[bold yellow]PDI — Pendentes (Prazo: 30/06/2026)[/]", border_style="yellow"))
        console.print()

    # ── Pendentes Planejamento ────────────────────────────────────────────────
    p_plan = [r["professor"] for r in resultados if r.get("plan_status") in ("PENDENTE", "ATRASADO", "SEM PASTA")]
    if p_plan:
        console.print(Panel(
            "\n".join(f"  [yellow]·[/] {p}" for p in p_plan),
            title="[bold yellow]Planejamento — Pendentes (Prazo: 30/06/2026)[/]", border_style="yellow"))
        console.print()


    # ── Alerta Evidências PEI SP ──────────────────────────────────────────────
    sem_ev_mes = [r["professor"] for r in resultados if not r.get("ev_mes_ok", True)]
    if sem_ev_mes:
        mes_atual = datetime.now().strftime("%B/%Y").upper()
        console.print(Panel(
            "\n".join(f"  [magenta]·[/] {p}" for p in sem_ev_mes),
            title=f"[bold magenta]⚠️  PEI SP — Sem Evidência em {mes_atual}[/]",
            border_style="magenta"))
        console.print()

    # ── Histórico ─────────────────────────────────────────────────────────────
    historico = registrar_semana(resultados)
    exibir_historico(historico)
