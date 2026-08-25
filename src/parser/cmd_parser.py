import re
from pathlib import Path
from typing import List
from src.model.move import Move

def parse_cmd_file(file_path: str | Path) -> List[Move]:
    """
    Parses a MUGEN / Ikemen GO .cmd file and extracts all [Command] blocks.
    Ignores comments (lines starting with ;) and handles messy formatting.
    Returns a list of Move models.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Command file not found: {path}")

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    moves: List[Move] = []
    
    # Split file sections based on [Command] tags (case-insensitive)
    sections = re.split(r'(?i)\[\s*Command\s*\]', content)

    for section in sections[1:]: # Skip the part before the first [Command]
        current_data = {}
        
        lines = section.splitlines()
        for line in lines:
            # Strip inline comments and trailing/leading spaces
            line_clean = line.split(';')[0].strip()
            
            if not line_clean:
                continue
            
            # If we hit another section header block, break out of this command block
            if line_clean.startswith('[') and line_clean.endswith(']'):
                break
                
            # Parse key = value fields inside the [Command] block
            match = re.match(r'^([a-zA-Z0-9_-]+)\s*=\s*(.*)$', line_clean)
            if match:
                key = match.group(1).lower()
                val = match.group(2).strip()
                
                # Remove wrapping quotes if present around name or command strings
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                    
                current_data[key] = val

        # If a valid command name and sequence string are found, construct the Move model
        if "name" in current_data and "command" in current_data:
            try:
                time_val = int(current_data.get("time", 15))
            except ValueError:
                time_val = 15

            buffer_time_val = None
            if "buffer_time" in current_data:
                try:
                    buffer_time_val = int(current_data["buffer_time"])
                except ValueError:
                    pass

            moves.append(
                Move(
                    name=current_data["name"],
                    command=current_data["command"],
                    time=time_val,
                    # buffer_time bisa disimpan di notes jika model Move tidak memiliki field buffer_time terpisah, 
                    # atau kita biarkan/abaikan jika tidak wajib. Mari masukkan ke notes agar aman:
                    notes=f"buffer_time: {buffer_time_val}" if buffer_time_val is not None else None
                )
            )

    return moves