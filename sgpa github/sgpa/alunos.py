#!/usr/bin/env python3
# alunos.py - SGPA 2026
# Sistema de cadastro, edição e consulta de alunos

import sys
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import box
from rich.text import Text

console = Console()

ABA_ALUNOS = "BASE_ALUNOS"

CAMPOS = [
    ("nome",        "Nome completo"),
    ("rg",          "RG"),
    ("turma",       "Turma (ex: 1A, 2B)"),
    ("professor",   "Professor responsável"),
    ("responsavel", "Nome do responsável"),
    ("contato",     "Contato do responsável (tel/email)"),
    ("necessidades","Necessidades especiais (PEI) [deixe em branco se não houver]"),
    ("observacoes", "Observações"),
]

CABECALHO = ["ID", "Nome", "RG", "Turma", "Professor", "Responsável", "Contato", "Necessidades", "Observações", "Cadastrado em"]


def autenticar():
    from config import CONFIG
    from drive_scanner import autenticar as auth
    _, sheets = auth(CONFIG["CREDENCIAIS_JSON"])
    return sheets, CONFIG["SPREADSHEET_ID"]


def garantir_cabecalho(sheets, spreadsheet_id: str):
    """Garante que a aba tem cabeçalho correto."""
    try:
        resp = sheets.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f"{ABA_ALUNOS}!A1:J1"
        ).execute()
        valores = resp.get("values", [])
        if not valores or valores[0][0] != "ID":
            sheets.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{ABA_ALUNOS}!A1",
                valueInputOption="RAW",
                body={"values": [CABECALHO]}
            ).execute()
    except Exception as e:
        console.print(f"[red]Erro ao verificar cabeçalho: {e}[/]")


def listar_alunos(sheets, spreadsheet_id: str) -> list:
    """Retorna todos os alunos cadastrados."""
    try:
        resp = sheets.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f"{ABA_ALUNOS}!A2:J1000"
        ).execute()
        return resp.get("values", [])
    except Exception as e:
        console.print(f"[red]Erro ao listar alunos: {e}[/]")
        return []


def proximo_id(alunos: list) -> int:
    """Gera o próximo ID sequencial."""
    if not alunos:
        return 1
    ids = []
    for a in alunos:
        try:
            ids.append(int(a[0]))
        except:
            pass
    return max(ids) + 1 if ids else 1


def exibir_tabela(alunos: list, titulo: str = "📋 Alunos Cadastrados"):
    if not alunos:
        console.print(Panel("[yellow]Nenhum aluno cadastrado ainda.[/]", border_style="yellow"))
        return

    table = Table(box=box.ROUNDED, show_header=True,
                  header_style="bold white on grey23", expand=True)
    table.add_column("ID",          width=5,  justify="center")
    table.add_column("Nome",        min_width=20)
    table.add_column("RG",          min_width=10)
    table.add_column("Turma",       width=7,  justify="center")
    table.add_column("Professor",   min_width=14)
    table.add_column("Responsável", min_width=16)
    table.add_column("Contato",     min_width=16)
    table.add_column("PEI",         width=5,  justify="center")
    table.add_column("Cadastrado",  min_width=12, justify="center")

    for a in alunos:
        while len(a) < 10:
            a.append("")
        pei = "✅" if a[7].strip() else "—"
        table.add_row(
            Text(a[0], style="dim"),
            Text(a[1], style="bold"),
            Text(a[2], style="dim"),
            Text(a[3], style="bold cyan"),
            Text(a[4], style="green"),
            Text(a[5], style="dim"),
            Text(a[6], style="dim"),
            Text(pei),
            Text(a[9][:10] if len(a) > 9 else "—", style="dim"),
        )

    console.print()
    console.print(Panel(table, title=f"[bold white]{titulo}[/]", border_style="cyan"))
    console.print(f"[dim]  Total: {len(alunos)} aluno(s)[/]\n")


def cadastrar_aluno(sheets, spreadsheet_id: str, alunos: list):
    console.print()
    console.print(Panel("[bold cyan]Novo Cadastro de Aluno[/]", border_style="cyan"))
    console.print()

    dados = {}
    for campo, label in CAMPOS:
        valor = Prompt.ask(f"  [cyan]{label}[/]").strip()
        dados[campo] = valor

    novo_id = proximo_id(alunos)
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")

    linha = [
        str(novo_id),
        dados["nome"],
        dados["rg"],
        dados["turma"].upper(),
        dados["professor"].upper(),
        dados["responsavel"],
        dados["contato"],
        dados["necessidades"],
        dados["observacoes"],
        agora,
    ]

    console.print()
    console.print(Panel(
        f"[bold]Nome:[/] {dados['nome']}\n"
        f"[bold]RG:[/] {dados['rg']}\n"
        f"[bold]Turma:[/] {dados['turma'].upper()}\n"
        f"[bold]Professor:[/] {dados['professor'].upper()}\n"
        f"[bold]Responsável:[/] {dados['responsavel']}\n"
        f"[bold]Contato:[/] {dados['contato']}\n"
        f"[bold]PEI:[/] {'Sim' if dados['necessidades'] else 'Não'}",
        title="[bold]Confirmar cadastro?[/]",
        border_style="yellow"
    ))

    if Confirm.ask("  Confirmar?", default=True):
        try:
            sheets.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=f"{ABA_ALUNOS}!A2",
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body={"values": [linha]}
            ).execute()
            console.print(f"\n[bold green]✅ Aluno cadastrado com ID #{novo_id}![/]\n")
        except Exception as e:
            console.print(f"[red]Erro ao cadastrar: {e}[/]")
    else:
        console.print("[yellow]Cadastro cancelado.[/]\n")


def consultar_aluno(alunos: list):
    console.print()
    termo = Prompt.ask("  [cyan]Buscar por nome, RG ou turma[/]").strip().upper()

    encontrados = [
        a for a in alunos
        if termo in (a[1].upper() if len(a) > 1 else "") or
           termo in (a[2].upper() if len(a) > 2 else "") or
           termo in (a[3].upper() if len(a) > 3 else "")
    ]

    if encontrados:
        exibir_tabela(encontrados, f"🔍 Resultado para '{termo}'")
    else:
        console.print(f"\n[yellow]Nenhum aluno encontrado para '{termo}'.[/]\n")


def editar_aluno(sheets, spreadsheet_id: str, alunos: list):
    console.print()
    busca_id = Prompt.ask("  [cyan]ID do aluno para editar[/]").strip()

    linha_idx = None
    aluno_atual = None
    for i, a in enumerate(alunos):
        if a[0] == busca_id:
            linha_idx = i + 2  # +2 por causa do cabeçalho e indexação 1
            aluno_atual = a
            break

    if not aluno_atual:
        console.print(f"[yellow]Aluno ID #{busca_id} não encontrado.[/]\n")
        return

    while len(aluno_atual) < 10:
        aluno_atual.append("")

    console.print(Panel(
        f"[bold]Editando:[/] {aluno_atual[1]} (ID #{busca_id})\n"
        f"[dim]Deixe em branco para manter o valor atual[/]",
        border_style="cyan"
    ))
    console.print()

    labels = ["Nome", "RG", "Turma", "Professor", "Responsável", "Contato", "Necessidades", "Observações"]
    novos = list(aluno_atual[:10])

    for i, label in enumerate(labels):
        atual = aluno_atual[i + 1] if i + 1 < len(aluno_atual) else ""
        valor = Prompt.ask(f"  [cyan]{label}[/] [dim](atual: {atual or '—'})[/]").strip()
        if valor:
            novos[i + 1] = valor.upper() if i in [2, 3] else valor

    try:
        sheets.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{ABA_ALUNOS}!A{linha_idx}:J{linha_idx}",
            valueInputOption="RAW",
            body={"values": [novos]}
        ).execute()
        console.print(f"\n[bold green]✅ Aluno ID #{busca_id} atualizado![/]\n")
    except Exception as e:
        console.print(f"[red]Erro ao editar: {e}[/]")


def menu_principal():
    console.print()
    console.print(Panel(
        "[bold cyan]SGPA 2026[/] · Cadastro de Alunos\n"
        "[dim]Sistema de gestão de alunos integrado ao Google Sheets[/]",
        style="bold white on dark_blue", expand=False
    ))

    console.print("[dim]→ Conectando ao Google Sheets...[/]")
    sheets, spreadsheet_id = autenticar()
    garantir_cabecalho(sheets, spreadsheet_id)
    console.print("[dim]→ Conexão estabelecida![/]\n")

    while True:
        console.print(Panel(
            "[1] 📋 Listar todos os alunos\n"
            "[2] ➕ Cadastrar novo aluno\n"
            "[3] 🔍 Consultar aluno\n"
            "[4] ✏️  Editar aluno\n"
            "[0] 🚪 Sair",
            title="[bold white]Menu[/]",
            border_style="white"
        ))

        opcao = Prompt.ask("  [cyan]Escolha[/]", choices=["0","1","2","3","4"])

        alunos = listar_alunos(sheets, spreadsheet_id)

        if opcao == "1":
            exibir_tabela(alunos)
        elif opcao == "2":
            cadastrar_aluno(sheets, spreadsheet_id, alunos)
        elif opcao == "3":
            consultar_aluno(alunos)
        elif opcao == "4":
            exibir_tabela(alunos)
            editar_aluno(sheets, spreadsheet_id, alunos)
        elif opcao == "0":
            console.print("\n[dim]Até logo![/]\n")
            break


if __name__ == "__main__":
    menu_principal()
