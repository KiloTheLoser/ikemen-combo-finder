import sys
from pathlib import Path

# Automatically append project root directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import json
import yaml
from rich import print
from rich.console import Console
from rich.table import Table

from src.model.move import Move
from src.model.cancel_graph import CancelGraph
from src.search.genetic import run_genetic_search
from src.validation.simulator import filter_and_validate_combos

console = Console()

def main():
    # 1. Load configuration settings
    config_path = Path("config.yaml")
    if not config_path.exists():
        console.print("[bold red]Error: config.yaml not found![/bold red]")
        return

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    char_path_str = config.get("character_path")
    if not char_path_str:
        console.print("[bold red]Error: 'character_path' not specified in config.yaml[/bold red]")
        return

    char_dir = Path(char_path_str)
    char_name = char_dir.name
    
    moves_output_dir = Path(config.get("output_paths", {}).get("moves", "results/moves/"))
    combos_output_dir = Path(config.get("output_paths", {}).get("combos", "results/combos/"))
    combos_output_dir.mkdir(parents=True, exist_ok=True)

    profile_path = moves_output_dir / f"{char_name}_profile.json"
    if not profile_path.exists():
        console.print(f"[bold red]Character profile JSON not found at {profile_path}. Run extract_moves.py first![/bold red]")
        return

    # 2. Load character profile moves
    with open(profile_path, "r", encoding="utf-8") as f:
        profile_data = json.load(f)

    moves = [Move(**m_data) for m_data in profile_data.get("moves", [])]
    if not moves:
        console.print("[bold red]No moves found in character profile data.[/bold red]")
        return

    moves_map = {m.name.lower(): m for m in moves}
    console.print(f"[cyan]Loaded {len(moves)} moves for character:[/cyan] {char_name}")

    # 3. Build Cancel Graph
    cancel_graph = CancelGraph(moves)
    console.print(f"[green]Built cancel graph with {cancel_graph.graph.number_of_nodes()} nodes and {cancel_graph.graph.number_of_edges()} heuristic edges.[/green]")

    # 4. Fetch search configuration options
    search_cfg = config.get("search_settings", {})
    max_length = search_cfg.get("max_combo_length", 8)
    pop_size = search_cfg.get("population_size", 100)
    generations = search_cfg.get("generations", 40)
    mutation_rate = search_cfg.get("mutation_rate", 0.2)

    console.print(f"[bold yellow]Running Genetic Algorithm Search (Pop: {pop_size}, Gens: {generations}, Max Len: {max_length})...[/bold yellow]")

    # 5. Execute Genetic Algorithm search
    raw_combos = run_genetic_search(
        moves=moves,
        cancel_graph=cancel_graph,
        max_combo_length=max_length,
        population_size=pop_size,
        generations=generations,
        mutation_rate=mutation_rate
    )

    if not raw_combos:
        console.print("[bold red]No valid combos were discovered by the genetic algorithm.[/bold red]")
        return

    # 6. Validate and filter results using ComboSimulator
    console.print("[cyan]Running ComboSimulator to validate transitions and calculate scaling damage...[/cyan]")
    best_combos = filter_and_validate_combos(raw_combos, cancel_graph, moves_map)

    if not best_combos:
        console.print("[bold red]Combos were found, but none passed the strict simulator validation filter.[/bold red]")
        return

    console.print(f"[bold green]Successfully validated {len(best_combos)} top combo sequences![/bold green]")

    # 7. Display results nicely using Rich Table
    table = Table(title=f"Validated Top Combos for {char_name}")
    table.add_column("Rank", style="cyan", justify="right")
    table.add_column("Combo Chain (Moves)", style="green")
    table.add_column("Length", style="yellow", justify="right")
    table.add_column("Scaled Dmg", style="red", justify="right")
    table.add_column("Fitness Score", style="blue", justify="right")

    for idx, combo in enumerate(best_combos, 1):
        chain_str = " ➔ ".join(combo["sequence"])
        table.add_row(
            str(idx),
            chain_str,
            str(combo.get("length", len(combo["sequence"]))),
            str(combo["estimated_damage"]),
            f"{combo.get('fitness_score', 0.0):.2f}"
        )

    console.print(table)

    # 8. Save validated results to results/combos/
    output_json_path = combos_output_dir / f"{char_name}_combos.json"
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(best_combos, f, indent=4)

    console.print(f"[bold green]Saved validated combos to:[/bold green] {output_json_path}")

if __name__ == "__main__":
    main()