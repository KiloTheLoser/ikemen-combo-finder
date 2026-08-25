import re
from pathlib import Path
from typing import Dict, List, Union

def parse_def_file(def_path: Union[str, Path]) -> Dict[str, Union[str, List[str]]]:
    """
    Parses a MUGEN / Ikemen GO .def file and extracts file references 
    (such as cmd, cns, st, sprite, sound, anim, etc.) relative to the character folder.
    """
    path = Path(def_path)
    if not path.exists():
        raise FileNotFoundError(f"Character definition file (.def) not found: {path}")

    char_dir = path.parent
    file_references: Dict[str, Union[str, List[str]]] = {}
    
    # Track multiple 'st' entries since characters can have multiple state files (st1, st2, etc.)
    additional_st: List[str] = []

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            # Strip inline comments and trailing/leading whitespace
            line_clean = line.split(';')[0].strip()
            
            if not line_clean or line_clean.startswith('[') and line_clean.endswith(']'):
                continue
                
            # Parse key = value fields
            match = re.match(r'^([a-zA-Z0-9_-]+)\s*=\s*(.*)$', line_clean)
            if match:
                key = match.group(1).lower()
                val = match.group(2).strip()
                
                # Remove wrapping quotes if present
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                
                # Normalize path separators for cross-platform compatibility
                val = val.replace('\\', '/')

                # Handle multi-state files or general configuration mappings
                if key == "st":
                    additional_st.append(val)
                else:
                    file_references[key] = val

    # If multiple 'st' files were found, keep them as a list alongside singular fields
    if additional_st:
        file_references["st_files"] = additional_st

    # Resolve paths relative to the character directory and store absolute / resolved Paths
    resolved_paths: Dict[str, Union[Path, List[Path], str]] = {}
    
    for key, val in file_references.items():
        if key == "st_files":
            resolved_paths[key] = [char_dir / st_path for st_path in val]
        elif key in ["cmd", "cns", "st", "sprite", "sound", "anim", "common", "pal"]:
            if val:
                resolved_paths[key] = char_dir / val
            else:
                resolved_paths[key] = val
        else:
            resolved_paths[key] = val

    # Expose the character directory helper reference
    resolved_paths["character_dir"] = char_dir
    return resolved_paths