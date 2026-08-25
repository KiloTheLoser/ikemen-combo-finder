from typing import List
from src.model.move import Move
from src.model.cancel_graph import CancelGraph

def evaluate_combo(combo_sequence: List[str], moves_map: dict, cancel_graph: CancelGraph) -> tuple:
    """
    Evaluates a sequence of move names and returns a fitness score tuple.
    Components scored:
    - Length of combo (+ points per successful move)
    - Total estimated damage (+ points per point of damage)
    - Cancel graph validity (+ bonus for valid edges, severe penalty for invalid transitions)
    
    DEAP uses maximization conventions, so higher is better.
    """
    if not combo_sequence:
        return (0.0,)

    score = 0.0
    total_damage = 0.0
    valid_transitions = 0
    invalid_transitions = 0

    # Resolve names into Move instances
    resolved_moves: List[Move] = []
    for name in combo_sequence:
        move_obj = moves_map.get(name.lower())
        if move_obj:
            resolved_moves.append(move_obj)

    if not resolved_moves:
        return (0.0,)

    # Base score per move length
    score += len(resolved_moves) * 10.0

    # Evaluate sequence step-by-step
    for i in range(len(resolved_moves)):
        move = resolved_moves[i]
        
        # Add damage factor (fallback default if damage is None)
        dmg = move.damage if move.damage is not None else 20.0
        total_damage += dmg

        # Check connectivity with the previous move via CancelGraph
        if i > 0:
            prev_move = resolved_moves[i - 1]
            prev_key = prev_move.name.lower()
            curr_key = move.name.lower()

            if cancel_graph.graph.has_edge(prev_key, curr_key):
                valid_transitions += 1
                score += 25.0  # Bonus for following valid cancel paths
            else:
                invalid_transitions += 1
                score -= 40.0  # Penalty for breaking rules / un-cancelable transitions

    score += total_damage * 0.5

    # Slight penalty if consecutive duplicate moves are spammed (anti-spam heuristic)
    duplicates = sum(1 for i in range(1, len(resolved_moves)) if resolved_moves[i].name == resolved_moves[i-1].name)
    score -= duplicates * 15.0

    return (max(score, 0.0),)