import re
from pathlib import Path
from typing import Dict, List, Any

def parse_cns_files(cns_paths: List[Path]) -> Dict[int, Dict[str, Any]]:
    """
    Parses a list of CNS / ST state files and extracts basic attributes for each state:
    - state_number
    - move_type (from type = A/S/L or general inferences)
    - damage (if HitDef is found inside the state)
    - hitstun (if found in HitDef)
    """
    states_data: Dict[int, Dict[str, Any]] = {}

    for path in cns_paths:
        if not path or not path.exists():
            continue

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Split file by [Statedef ...] sections
        sections = re.split(r'(?i)\[\s*Statedef\s+(-?\d+)\]', content)
        
        # re.split with capturing parentheses alternates: [pre, state_id_1, body_1, state_id_2, body_2, ...]
        for i in range(1, len(sections), 2):
            try:
                state_num = int(sections[i].strip())
            except ValueError:
                continue
                
            body = sections[i + 1]
            state_info: Dict[str, Any] = {
                "state_number": state_num,
                "move_type": "unknown",
                "damage": None,
                "hitstun": None
            }

            # Look for type = attack type (e.g., type = S, A, C)
            type_match = re.search(r'(?i)^\s*type\s*=\s*([A-Za-z]+)', body, re.MULTILINE)
            if type_match:
                t_val = type_match.group(1).upper()
                if 'A' in t_val:
                    state_info["move_type"] = "normal" # Default assumption, can refine later

            # Look for HitDef damage fields inside the state body
            damage_match = re.search(r'(?i)damage\s*=\s*(\d+)', body)
            if damage_match:
                state_info["damage"] = int(damage_match.group(1))
                state_info["move_type"] = "special" # Often attacks with hitdefs are specials/normals

            # Look for guard.ctrltime or hitstun parameters if explicitly set
            hitstun_match = re.search(r'(?i)guard\.ctrltime\s*=\s*(\d+)', body)
            if hitstun_match:
                state_info["hitstun"] = int(hitstun_match.group(1))

            states_data[state_num] = state_info

    return states_data


def map_commands_to_states(commands_data: List[Any], cns_paths: List[Path], cmd_content_raw: str) -> List[Any]:
    """
    Tries to link command names to trigger states inside the .cmd file state-controller blocks,
    and enriches them with data extracted from CNS state definition files.
    """
    states_dict = parse_cns_files(cns_paths)

    # Read raw .cmd content to search for triggers like: trigger1 = command = "movename" ... changeState = XXX
    # MUGEN state controllers for commands look like:
    # [State -1, Fireball]
    # type = ChangeState
    # value = 1000
    # trigger1 = command = "fireball"
    
    for move in commands_data:
        move_name_lower = move.name.lower()
        
        # Search pattern in .cmd text for a ChangeState targeting a value associated with this command name
        # We look for blocks containing the command name and a value assignment
        pattern = rf'(?i)\[\s*State\s*[^\]]+\][^\[]*command\s*=\s*"{re.escape(move_name_lower)}"[^\[]*value\s*=\s*(-?\d+)'
        match = re.search(pattern, cmd_content_raw, re.DOTALL)
        
        if not match:
            # Try alternate pattern (single quotes or variable variations)
            pattern_alt = rf'(?i)command\s*=\s*"{re.escape(move_name_lower)}".*?value\s*=\s*(-?\d+)'
            match = re.search(pattern_alt, cmd_content_raw, re.DOTALL | re.IGNORECASE)

        if match:
            try:
                s_num = int(match.group(1))
                move.state_number = s_num
                
                # Enrich with CNS parsed data if available
                if s_num in states_dict:
                    cns_info = states_dict[s_num]
                    if cns_info["damage"] is not None:
                        move.damage = cns_info["damage"]
                    if cns_info["hitstun"] is not None:
                        move.hitstun = cns_info["hitstun"]
                    if move.move_type == "unknown":
                        move.move_type = cns_info["move_type"]
            except ValueError:
                pass

        # Heuristic categorization based on command types if still unknown
        if move.move_type == "unknown":
            cmd_str = move.command.lower()
            if any(k in cmd_str for k in ["~d, df, f", "~d, db, b", "f, d, df", "b, d, db"]):
                move.move_type = "special"
            elif any(k in cmd_str for k in ["2$f", "2$b", "~2$d", "d, d"]):
                move.move_type = "super"
            elif any(k in cmd_str for k in ["x", "y", "z", "a", "b", "c"]):
                move.move_type = "normal"

    return commands_data