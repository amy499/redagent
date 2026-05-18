import argparse
from dotenv import load_dotenv
load_dotenv()

from rich.console import Console
from rich.table import Table

from app.core.attack_generator import generate_all, CANONICAL_CATEGORIES, _normalise, _generate
from app.core.executor import execute
from app.core.judge import judge
from app.core.reporter import generate_report
from seed.jailbreak import jailbreak
from seed.jailbreak_extensions import ALL_EXTENSIONS

console = Console()


def run_single(category):
    console.print(f"\n[bold cyan]Tracer bullet:[/bold cyan] {category}\n")

    seeds = _normalise(jailbreak + ALL_EXTENSIONS)
    category_seeds = [s for s in seeds if s["category"] == category]
    examples = category_seeds[:3] if len(category_seeds) >= 3 else []
    attacks = _generate(category, examples)[:1]

    console.print(f"[blue]Attack:[/blue] {attacks[0]['prompt']}\n")

    executed = execute(attacks)
    console.print(f"[yellow]Response:[/yellow] {executed[0]['response'][:300]}\n")

    judged = judge(executed)
    result = judged[0]

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Success", str(result.get("success")))
    table.add_row("Severity", str(result.get("severity")))
    table.add_row("Reason", result.get("reason", ""))
    table.add_row("Leaked markers", ", ".join(result.get("leaked_markers", [])) or "none")
    console.print(table)


def run_full():
    console.print("\n[bold green]RedAgent — Full Pipeline[/bold green]\n")

    console.print("[cyan]Generating attacks...[/cyan]")
    attacks = generate_all()
    console.print(f"  {len(attacks)} prompts across {len(CANONICAL_CATEGORIES)} categories\n")

    console.print("[cyan]Executing attacks against WealthGuard AI...[/cyan]")
    executed = execute(attacks)
    console.print(f"  {len(executed)} responses collected\n")

    console.print("[cyan]Judging results...[/cyan]")
    judged = judge(executed)
    successes = [r for r in judged if r.get("success")]
    console.print(f"  {len(successes)} / {len(judged)} attacks succeeded\n")

    console.print("[cyan]Generating report...[/cyan]")
    path = generate_report(judged)

    console.print("\n[bold green]Pipeline complete.[/bold green]")
    console.print(f"[green]{len(successes)} successful attacks. Report saved to {path}[/green]\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--single-attack", action="store_true")
    parser.add_argument("--category", default="social_engineering")
    args = parser.parse_args()

    if args.single_attack:
        run_single(args.category)
    else:
        run_full()
