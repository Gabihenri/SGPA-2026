#!/usr/bin/env python3
# analisar_perfil.py - SGPA 2026

import json
import os
import sys
import re
import webbrowser
from datetime import datetime
import anthropic

HISTORICO_FILE = "historico.json"
RELATORIO_FILE = f"relatorio_perfil_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
DASHBOARD_HTML = "dashboard_perfil.html"


def carregar_historico() -> dict:
    if not os.path.exists(HISTORICO_FILE):
        print("❌ Arquivo historico.json não encontrado. Rode main.py pelo menos uma vez.")
        sys.exit(1)
    with open(HISTORICO_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def carregar_ultimo_resultado() -> list:
    if not os.path.exists("ultimo_resultado.json"):
        return []
    with open("ultimo_resultado.json", "r", encoding="utf-8") as f:
        return json.load(f)


def montar_contexto_professor(nome: str, historico: dict, resultado_atual: dict) -> str:
    linhas = [f"Professor: {nome}"]
    linhas.append(f"Data da análise: {datetime.now().strftime('%d/%m/%Y')}")
    linhas.append("")
    linhas.append("=== SITUAÇÃO ATUAL ===")
    linhas.append(f"Agenda semanal: {resultado_atual.get('status', 'N/A')}")
    linhas.append(f"Proatividade: {resultado_atual.get('proatividade', 'N/A')}")
    linhas.append(f"PEI: {resultado_atual.get('pei_status', 'N/A')}")
    linhas.append(f"Guia de Aprendizagem: {resultado_atual.get('guia_status', 'N/A')}")
    linhas.append(f"Evidências: {resultado_atual.get('ev_status', 'N/A')} ({resultado_atual.get('ev_quantidade', 0)} arquivos)")
    linhas.append("")
    linhas.append("=== HISTÓRICO SEMANAL ===")
    semanas = []
    for semana, dados in sorted(historico.items()):
        semanas.append(
            f"Semana {semana}: Adiantado={dados.get('ADIANTADO',0)}, "
            f"Regular={dados.get('REGULAR',0)}, UltimoDia={dados.get('ULTIMO DIA',0)}, "
            f"Pendente={dados.get('PENDENTE',0)}"
        )
    linhas.extend(semanas if semanas else ["Apenas 1 semana de histórico disponível."])
    return "\n".join(linhas)


def analisar_professor_ia(cliente, contexto: str) -> dict:
    """Retorna análise estruturada em JSON para uso no dashboard."""
    prompt = f"""Você é um especialista em gestão educacional da SEDUC SP.

Analise o perfil do professor e responda APENAS em JSON válido, sem texto adicional:

{{
  "perfil_geral": "2-3 frases sobre o comportamento geral do professor",
  "classificacao": "EXEMPLAR" ou "COMPROMETIDO" ou "EM DESENVOLVIMENTO" ou "REQUER ATENÇÃO",
  "pontos_fortes": ["ponto 1", "ponto 2", "ponto 3"],
  "pontos_atencao": ["ponto 1", "ponto 2"],
  "recomendacao": "1-2 frases de recomendação para o gestor",
  "scores": {{
    "agenda": número de 0 a 100,
    "documentacao": número de 0 a 100,
    "proatividade": número de 0 a 100,
    "evidencias": número de 0 a 100
  }}
}}

DADOS DO PROFESSOR:
{contexto}
"""
    resposta = cliente.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    texto = resposta.content[0].text.strip()
    # Remove markdown se houver
    texto = re.sub(r"```json|```", "", texto).strip()
    try:
        return json.loads(texto)
    except:
        return {
            "perfil_geral": texto,
            "classificacao": "EM DESENVOLVIMENTO",
            "pontos_fortes": ["Dados insuficientes"],
            "pontos_atencao": ["Dados insuficientes"],
            "recomendacao": "Verificar manualmente.",
            "scores": {"agenda": 50, "documentacao": 50, "proatividade": 50, "evidencias": 50}
        }


def gerar_html(analises: list, resultados: list) -> str:
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Mapeia resultado por professor
    res_map = {r["professor"]: r for r in resultados}

    # Cores por classificação
    cores = {
        "EXEMPLAR":         {"bg": "#0d2d1a", "badge": "#00c853", "text": "#00c853", "emoji": "🌟"},
        "COMPROMETIDO":     {"bg": "#0d1f2d", "badge": "#00b0ff", "text": "#00b0ff", "emoji": "✅"},
        "EM DESENVOLVIMENTO":{"bg": "#2d1f0d", "badge": "#ff9800", "text": "#ff9800", "emoji": "⚠️"},
        "REQUER ATENÇÃO":   {"bg": "#2d0d0d", "badge": "#f44336", "text": "#f44336", "emoji": "🔴"},
    }

    contagem = {"EXEMPLAR": 0, "COMPROMETIDO": 0, "EM DESENVOLVIMENTO": 0, "REQUER ATENÇÃO": 0}
    for a in analises:
        cl = a["analise"].get("classificacao", "EM DESENVOLVIMENTO")
        if cl in contagem:
            contagem[cl] += 1

    cards_html = ""
    for a in analises:
        nome = a["professor"]
        an = a["analise"]
        cl = an.get("classificacao", "EM DESENVOLVIMENTO")
        cor = cores.get(cl, cores["EM DESENVOLVIMENTO"])
        scores = an.get("scores", {"agenda": 50, "documentacao": 50, "proatividade": 50, "evidencias": 50})
        fortes = an.get("pontos_fortes", [])
        atencao = an.get("pontos_atencao", [])
        res = res_map.get(nome, {})

        fortes_html = "".join(f'<li>{p}</li>' for p in fortes)
        atencao_html = "".join(f'<li>{p}</li>' for p in atencao)

        pei_icon = "✅" if res.get("pei_status") == "ENTREGUE" else "⏳"
        guia_icon = "✅" if res.get("guia_status") == "ENTREGUE" else "⏳"
        ev_qtd = res.get("ev_quantidade", 0)
        agenda_icon = "✅" if res.get("status") == "NO PRAZO" else "❌"

        cards_html += f"""
        <div class="card" style="background:{cor['bg']}; border-color:{cor['badge']}22">
            <div class="card-header">
                <div class="nome">{nome}</div>
                <div class="badge" style="background:{cor['badge']}22; color:{cor['badge']}; border:1px solid {cor['badge']}44">
                    {cor['emoji']} {cl}
                </div>
            </div>
            <p class="perfil-geral">{an.get('perfil_geral','')}</p>

            <div class="status-pills">
                <span class="pill">📅 Agenda {agenda_icon}</span>
                <span class="pill">📋 PEI {pei_icon}</span>
                <span class="pill">📚 Guia {guia_icon}</span>
                <span class="pill">🗂️ Evidências: {ev_qtd}</span>
            </div>

            <div class="scores-grid">
                <div class="score-item">
                    <div class="score-label">Agenda</div>
                    <div class="score-bar"><div class="score-fill" style="width:{scores.get('agenda',50)}%; background:{cor['badge']}"></div></div>
                    <div class="score-val">{scores.get('agenda',50)}</div>
                </div>
                <div class="score-item">
                    <div class="score-label">Documentação</div>
                    <div class="score-bar"><div class="score-fill" style="width:{scores.get('documentacao',50)}%; background:{cor['badge']}"></div></div>
                    <div class="score-val">{scores.get('documentacao',50)}</div>
                </div>
                <div class="score-item">
                    <div class="score-label">Proatividade</div>
                    <div class="score-bar"><div class="score-fill" style="width:{scores.get('proatividade',50)}%; background:{cor['badge']}"></div></div>
                    <div class="score-val">{scores.get('proatividade',50)}</div>
                </div>
                <div class="score-item">
                    <div class="score-label">Evidências</div>
                    <div class="score-bar"><div class="score-fill" style="width:{scores.get('evidencias',50)}%; background:{cor['badge']}"></div></div>
                    <div class="score-val">{scores.get('evidencias',50)}</div>
                </div>
            </div>

            <div class="pontos-grid">
                <div class="pontos-box fortes">
                    <div class="pontos-title">💪 Pontos Fortes</div>
                    <ul>{fortes_html}</ul>
                </div>
                <div class="pontos-box atencao">
                    <div class="pontos-title">⚠️ Pontos de Atenção</div>
                    <ul>{atencao_html}</ul>
                </div>
            </div>

            <div class="recomendacao">
                <span class="rec-label">🎯 Recomendação:</span> {an.get('recomendacao','')}
            </div>
        </div>
        """

    total = len(analises)
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SGPA 2026 — Perfil dos Professores</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  :root {{
    --bg: #060a0f;
    --surface: #0d1117;
    --border: #1e2d3d;
    --text: #c9d1d9;
    --muted: #6e7681;
    --accent: #00e5ff;
  }}

  body {{
    background: var(--bg);
    color: var(--text);
    font-family: 'Space Grotesk', sans-serif;
    min-height: 100vh;
    padding: 0 0 60px;
  }}

  /* Header */
  .hero {{
    background: linear-gradient(135deg, #060a0f 0%, #0d1f2d 50%, #060a0f 100%);
    border-bottom: 1px solid var(--border);
    padding: 48px 40px 36px;
    position: relative;
    overflow: hidden;
  }}
  .hero::before {{
    content: '';
    position: absolute;
    top: -100px; left: -100px;
    width: 400px; height: 400px;
    background: radial-gradient(circle, #00e5ff11 0%, transparent 70%);
    pointer-events: none;
  }}
  .hero-title {{
    font-size: 2.2rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    color: #fff;
  }}
  .hero-title span {{ color: var(--accent); }}
  .hero-sub {{
    color: var(--muted);
    font-size: 0.9rem;
    margin-top: 6px;
    font-family: 'JetBrains Mono', monospace;
  }}

  /* Resumo cards */
  .resumo {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
    padding: 32px 40px 0;
    max-width: 1400px;
    margin: 0 auto;
  }}
  .resumo-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    transition: transform 0.2s;
  }}
  .resumo-card:hover {{ transform: translateY(-2px); }}
  .resumo-num {{
    font-size: 2.4rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
  }}
  .resumo-label {{ font-size: 0.8rem; color: var(--muted); margin-top: 4px; }}

  /* Grid de cards */
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));
    gap: 24px;
    padding: 32px 40px;
    max-width: 1400px;
    margin: 0 auto;
  }}

  .card {{
    border: 1px solid;
    border-radius: 16px;
    padding: 24px;
    transition: transform 0.2s, box-shadow 0.2s;
    animation: fadeUp 0.4s ease both;
  }}
  .card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 12px 40px #00000066;
  }}
  @keyframes fadeUp {{
    from {{ opacity: 0; transform: translateY(16px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
  }}

  .card-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    flex-wrap: wrap;
    gap: 8px;
  }}
  .nome {{
    font-size: 1.2rem;
    font-weight: 700;
    color: #fff;
    letter-spacing: -0.02em;
  }}
  .badge {{
    font-size: 0.75rem;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 20px;
    letter-spacing: 0.05em;
  }}

  .perfil-geral {{
    font-size: 0.875rem;
    color: var(--muted);
    line-height: 1.6;
    margin-bottom: 16px;
  }}

  .status-pills {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 18px;
  }}
  .pill {{
    background: #ffffff08;
    border: 1px solid #ffffff11;
    border-radius: 20px;
    padding: 4px 10px;
    font-size: 0.75rem;
    color: var(--text);
  }}

  /* Scores */
  .scores-grid {{
    display: grid;
    gap: 10px;
    margin-bottom: 18px;
  }}
  .score-item {{
    display: grid;
    grid-template-columns: 100px 1fr 36px;
    align-items: center;
    gap: 10px;
  }}
  .score-label {{ font-size: 0.78rem; color: var(--muted); }}
  .score-bar {{
    height: 6px;
    background: #ffffff10;
    border-radius: 4px;
    overflow: hidden;
  }}
  .score-fill {{
    height: 100%;
    border-radius: 4px;
    transition: width 0.8s ease;
  }}
  .score-val {{
    font-size: 0.78rem;
    font-family: 'JetBrains Mono', monospace;
    color: var(--muted);
    text-align: right;
  }}

  /* Pontos */
  .pontos-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-bottom: 16px;
  }}
  .pontos-box {{
    border-radius: 10px;
    padding: 14px;
  }}
  .fortes {{ background: #00c85308; border: 1px solid #00c85322; }}
  .atencao {{ background: #ff980008; border: 1px solid #ff980022; }}
  .pontos-title {{
    font-size: 0.78rem;
    font-weight: 600;
    margin-bottom: 8px;
    color: #fff;
  }}
  .pontos-box ul {{
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 5px;
  }}
  .pontos-box li {{
    font-size: 0.78rem;
    color: var(--muted);
    padding-left: 14px;
    position: relative;
    line-height: 1.4;
  }}
  .fortes li::before {{ content: '→'; position: absolute; left: 0; color: #00c853; }}
  .atencao li::before {{ content: '!'; position: absolute; left: 0; color: #ff9800; font-weight: 700; }}

  /* Recomendação */
  .recomendacao {{
    background: #ffffff05;
    border: 1px solid #ffffff0d;
    border-radius: 8px;
    padding: 12px 14px;
    font-size: 0.82rem;
    color: var(--muted);
    line-height: 1.5;
  }}
  .rec-label {{ color: var(--accent); font-weight: 600; }}

  /* Filtros */
  .filtros {{
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    padding: 24px 40px 0;
    max-width: 1400px;
    margin: 0 auto;
  }}
  .filtro-btn {{
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 8px 18px;
    border-radius: 20px;
    font-size: 0.82rem;
    cursor: pointer;
    font-family: 'Space Grotesk', sans-serif;
    transition: all 0.2s;
  }}
  .filtro-btn:hover, .filtro-btn.ativo {{
    background: var(--accent);
    color: #000;
    border-color: var(--accent);
    font-weight: 600;
  }}

  footer {{
    text-align: center;
    color: var(--muted);
    font-size: 0.78rem;
    padding: 40px;
    font-family: 'JetBrains Mono', monospace;
  }}
</style>
</head>
<body>

<div class="hero">
  <div class="hero-title">SGPA <span>2026</span> — Perfil dos Professores</div>
  <div class="hero-sub">Análise gerada por IA · {agora} · {total} professores analisados</div>
</div>

<div class="resumo">
  <div class="resumo-card">
    <div class="resumo-num" style="color:#00c853">{contagem['EXEMPLAR']}</div>
    <div class="resumo-label">🌟 Exemplar</div>
  </div>
  <div class="resumo-card">
    <div class="resumo-num" style="color:#00b0ff">{contagem['COMPROMETIDO']}</div>
    <div class="resumo-label">✅ Comprometido</div>
  </div>
  <div class="resumo-card">
    <div class="resumo-num" style="color:#ff9800">{contagem['EM DESENVOLVIMENTO']}</div>
    <div class="resumo-label">⚠️ Em Desenvolvimento</div>
  </div>
  <div class="resumo-card">
    <div class="resumo-num" style="color:#f44336">{contagem['REQUER ATENÇÃO']}</div>
    <div class="resumo-label">🔴 Requer Atenção</div>
  </div>
  <div class="resumo-card">
    <div class="resumo-num" style="color:#fff">{total}</div>
    <div class="resumo-label">👥 Total</div>
  </div>
</div>

<div class="filtros">
  <button class="filtro-btn ativo" onclick="filtrar('todos', this)">Todos ({total})</button>
  <button class="filtro-btn" onclick="filtrar('EXEMPLAR', this)">🌟 Exemplar</button>
  <button class="filtro-btn" onclick="filtrar('COMPROMETIDO', this)">✅ Comprometido</button>
  <button class="filtro-btn" onclick="filtrar('EM DESENVOLVIMENTO', this)">⚠️ Em Desenvolvimento</button>
  <button class="filtro-btn" onclick="filtrar('REQUER ATENÇÃO', this)">🔴 Requer Atenção</button>
</div>

<div class="grid" id="grid">
{cards_html}
</div>

<footer>SGPA 2026 · Secretaria da Educação do Estado de São Paulo · Gerado automaticamente</footer>

<script>
  function filtrar(tipo, btn) {{
    document.querySelectorAll('.filtro-btn').forEach(b => b.classList.remove('ativo'));
    btn.classList.add('ativo');
    document.querySelectorAll('.card').forEach(card => {{
      if (tipo === 'todos') {{
        card.style.display = '';
      }} else {{
        const badge = card.querySelector('.badge').textContent;
        card.style.display = badge.includes(tipo) ? '' : 'none';
      }}
    }});
  }}

  // Animação escalonada dos cards
  document.querySelectorAll('.card').forEach((card, i) => {{
    card.style.animationDelay = (i * 0.06) + 's';
  }});
</script>
</body>
</html>"""
    return html


def gerar_relatorio_md(analises: list) -> str:
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    linhas = [
        "# SGPA 2026 — Relatório de Perfil dos Professores",
        f"**Gerado em:** {agora}  ",
        f"**Total analisado:** {len(analises)} professores",
        "", "---", "",
    ]
    for item in analises:
        an = item["analise"]
        linhas.append(f"## {item['professor']}")
        linhas.append(f"**Classificação:** {an.get('classificacao','')}")
        linhas.append("")
        linhas.append(an.get("perfil_geral", ""))
        linhas.append("")
        linhas.append("**Pontos Fortes:**")
        for p in an.get("pontos_fortes", []):
            linhas.append(f"- {p}")
        linhas.append("")
        linhas.append("**Pontos de Atenção:**")
        for p in an.get("pontos_atencao", []):
            linhas.append(f"- {p}")
        linhas.append("")
        linhas.append(f"**Recomendação:** {an.get('recomendacao','')}")
        linhas.append("")
        linhas.append("---")
        linhas.append("")
    return "\n".join(linhas)


def main():
    from config import CONFIG
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn

    console = Console()

    api_key = CONFIG.get("ANTHROPIC_API_KEY", "")
    if not api_key or api_key == "SUA_CHAVE_AQUI":
        console.print("[bold red]❌ Chave API da Anthropic não configurada no config.py![/]")
        sys.exit(1)

    console.print()
    console.print(Panel(
        "[bold cyan]SGPA 2026[/] · Análise de Perfil com IA\n"
        "[dim]Analisando comportamento individual de cada professor...[/]",
        style="bold white on dark_blue", expand=False
    ))
    console.print()

    historico = carregar_historico()
    resultados = carregar_ultimo_resultado()

    if not resultados:
        console.print("[yellow]⚠️  Nenhum resultado encontrado. Rode python main.py primeiro.[/]")
        sys.exit(1)

    cliente = anthropic.Anthropic(api_key=api_key)
    analises = []

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Analisando professores...", total=len(resultados))
        for r in resultados:
            nome = r["professor"]
            progress.update(task, description=f"[cyan]Analisando:[/] {nome}")
            contexto = montar_contexto_professor(nome, historico, r)
            analise = analisar_professor_ia(cliente, contexto)
            analises.append({"professor": nome, "analise": analise})
            progress.advance(task)

    # Exibe resumo no terminal
    console.print()
    from rich.table import Table
    from rich import box as rbox
    table = Table(box=rbox.ROUNDED, show_header=True,
                  header_style="bold white on grey23", expand=True)
    table.add_column("Professor", min_width=18)
    table.add_column("Classificação", min_width=20, justify="center")
    table.add_column("Agenda", width=8, justify="center")
    table.add_column("Doc.", width=8, justify="center")
    table.add_column("Proativ.", width=8, justify="center")
    table.add_column("Evidênc.", width=8, justify="center")
    table.add_column("Recomendação", min_width=30)

    cores_term = {
        "EXEMPLAR":          "bold green",
        "COMPROMETIDO":      "bold cyan",
        "EM DESENVOLVIMENTO":"bold yellow",
        "REQUER ATENÇÃO":    "bold red",
    }
    emojis = {
        "EXEMPLAR": "🌟", "COMPROMETIDO": "✅",
        "EM DESENVOLVIMENTO": "⚠️", "REQUER ATENÇÃO": "🔴"
    }

    from rich.text import Text
    for item in analises:
        an = item["analise"]
        cl = an.get("classificacao", "EM DESENVOLVIMENTO")
        scores = an.get("scores", {})
        cor = cores_term.get(cl, "white")
        table.add_row(
            Text(item["professor"], style="bold"),
            Text(f"{emojis.get(cl,'')} {cl}", style=cor),
            Text(str(scores.get("agenda", "—")), style="dim"),
            Text(str(scores.get("documentacao", "—")), style="dim"),
            Text(str(scores.get("proatividade", "—")), style="dim"),
            Text(str(scores.get("evidencias", "—")), style="dim"),
            Text(an.get("recomendacao", "")[:60] + "...", style="dim"),
        )
    console.print(table)
    console.print()

    # Gera HTML e abre no navegador
    html = gerar_html(analises, resultados)
    with open(DASHBOARD_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    # Salva relatório MD
    md = gerar_relatorio_md(analises)
    with open(RELATORIO_FILE, "w", encoding="utf-8") as f:
        f.write(md)

    console.print(Panel(
        f"[bold green]✅ Dashboard HTML:[/] [cyan]{DASHBOARD_HTML}[/]\n"
        f"[bold green]✅ Relatório MD:[/]  [cyan]{RELATORIO_FILE}[/]",
        border_style="green"
    ))

    # Abre automaticamente no navegador
    import os as _os
    abs_path = _os.path.abspath(DASHBOARD_HTML)
    webbrowser.open(f"file:///{abs_path}")
    console.print("[dim]→ Dashboard aberto no navegador![/]\n")


if __name__ == "__main__":
    main()
