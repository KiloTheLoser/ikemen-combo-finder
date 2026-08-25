import sys
import json
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import yaml
from rich import print
from rich.console import Console
from rich.table import Table

from src.parser.def_parser import parse_def_file
from src.parser.cmd_parser import parse_cmd_file
from src.parser.cns_parser import map_commands_to_states
from src.model.character import Character

console = Console()

def main():
    # 1. Read configuration
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
    output_dir = Path(config.get("output_paths", {}).get("moves", "results/moves/"))
    output_dir.mkdir(parents=True, exist_ok=True)

    if not char_dir.exists():
        console.print(f"[bold red]Character path does not exist: {char_dir}[/bold red]")
        return

    # 2. Locate and Parse .def file
    def_files = list(char_dir.glob("*.def"))
    if not def_files:
        console.print(f"[bold red]No .def files found in directory: {char_dir}[/bold red]")
        return

    target_def = def_files[0]
    console.print(f"[cyan]Found character definition (.def):[/cyan] {target_def.name}")

    try:
        def_data = parse_def_file(target_def)
    except Exception as e:
        console.print(f"[bold red]Failed to parse .def file: {e}[/bold red]")
        raise e

    # 3. Locate and Parse .cmd file
    target_cmd = def_data.get("cmd")
    if not target_cmd or not isinstance(target_cmd, Path) or not target_cmd.exists():
        fallback_cmds = list(char_dir.glob("*.cmd"))
        if not fallback_cmds:
            console.print("[bold red]No .cmd files found.[/bold red]")
            return
        target_cmd = fallback_cmds[0]

    console.print(f"[green]Using command file:[/green] {target_cmd.name}")
    
    with open(target_cmd, "r", encoding="utf-8", errors="ignore") as f:
        cmd_content_raw = f.read()

    moves = parse_cmd_file(target_cmd)

    # 4. Collect all state paths (.cns and .st) referenced in .def for CNS parsing
    cns_paths = []
    
    # Check single cns or st keys
    for key in ["cns", "st"]:
        p = def_data.get(key)
        if isinstance(p, Path) and p.exists():
            cns_paths.append(p)
            
    # Check multi-state files list (st_files)
    st_list = def_data.get("st_files", [])
    for p in st_list:
        if isinstance(p, Path) and p.exists():
            cns_paths.append(p)

    # Fallback to scan directory for all .cns and .st files if none explicitly registered
    if not cns_paths:
        cns_paths = list(char_dir.glob("*.cns")) + list(char_dir.glob("*.st"))

    console.print(f"[cyan]Found {len(cns_paths)} state files to cross-reference.[/cyan]")

    # 5. Map commands to states & enrich attributes
    moves = map_commands_to_states(moves, cns_paths, cmd_content_raw)

    # 6. Build Character Model instance
    character = Character(
        name=char_dir.name,
        character_path=char_dir,
        moves=moves
    )

    console.print(f"[bold cyan]Successfully parsed character '{character.name}' with {len(character.moves)} moves.[/bold cyan]")

    # 7. Print formatted Rich table
    table = Table(title=f"Parsed Character Moves: {character.name}")
    table.add_column("Name", style="magenta", no_wrap=True)
    table.add_column("Type", style="cyan")
    table.add_column("Command", style="green")
    table.add_column("State", justify="right", style="yellow")
    table.add_column("Dmg", justify="right", style="red")
    table.add_column("Stun", justify="right", style="blue")

    for move in character.moves:
        table.add_row(
            move.name,
            move.move_type,
            move.command,
            str(move.state_number) if move.state_number is not None else "-",
            str(move.damage) if move.damage is not None else "-",
            str(move.hitstun) if move.hitstun is not None else "-"
        )

    console.print(table)

    # 8. Save character model output as JSON to results/moves/
    output_json_path = output_dir / f"{character.name}_profile.json"
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(character.model_dump(mode='json'), f, indent=4)

    console.print(f"[bold green]Saved complete character profile to:[/bold green] {output_json_path}")

if __name__ == "__main__":
    main()