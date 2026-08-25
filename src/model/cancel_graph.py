import networkx as nx
from typing import List, Dict, Any
from src.model.move import Move

class CancelGraph:
    """
    Manages the cancel/transition graph between character moves using NetworkX.
    Nodes represent Moves, and Directed Edges represent valid cancel transitions (Move A -> Move B).
    """
    def __init__(self, moves: List[Move]):
        self.graph: nx.DiGraph = nx.DiGraph()
        self.moves_map: Dict[str, Move] = {}
        self._build_graph(moves)

    def _build_graph(self, moves: List[Move]) -> None:
        """Adds all moves as nodes and applies flexible heuristic edge rules."""
        for move in moves:
            node_key = move.name.lower()
            self.moves_map[node_key] = move
            self.graph.add_node(node_key, move_obj=move)

        node_keys = list(self.moves_map.keys())
        
        for src_key in node_keys:
            src_move = self.moves_map[src_key]
            
            for dst_key in node_keys:
                if src_key == dst_key:
                    continue
                dst_move = self.moves_map[dst_key]
                
                if self._is_valid_heuristic_cancel(src_move, dst_move):
                    self.graph.add_edge(src_key, dst_key, rule="heuristic")

    def _is_valid_heuristic_cancel(self, src: Move, dst: Move) -> bool:
        """
        Flexible fighting game cancel rules tailored for messy MUGEN command sets:
        1. Normal -> Special or Unknown
        2. Special -> Super or Special
        3. Unknown/Custom commands can chain freely to provide exploratory results.
        4. Same strength chains or general flow.
        """
        src_type = src.move_type.lower()
        dst_type = dst.move_type.lower()
        src_name = src.name.lower()
        dst_name = dst.name.lower()

        # Rule 0: If it's an AI or custom state command chain, be very lenient
        if "ai_" in src_name or "ai_" in dst_name:
            return True

        # Rule 1: Normal -> Special / Normal -> Unknown
        if src_type == "normal" and dst_type in ["special", "unknown"]:
            return True

        # Rule 2: Special -> Super / Special -> Special
        if src_type == "special" and dst_type in ["super", "special", "unknown"]:
            return True

        # Rule 3: If types are unknown, allow generic flow so the engine doesn't block everything
        if src_type == "unknown" or dst_type == "unknown":
            return True

        # Rule 4: Chain cancels within normals (Light -> Medium -> Heavy)
        if src_type == "normal" and dst_type == "normal":
            return True  # Relaxed: Allow any normal-to-normal chaining for complex characters

        return False

    def add_custom_cancel(self, from_move_name: str, to_move_name: str, rule_name: str = "custom") -> bool:
        src_key = from_move_name.lower()
        dst_key = to_move_name.lower()

        if src_key in self.graph.nodes and dst_key in self.graph.nodes:
            self.graph.add_edge(src_key, dst_key, rule=rule_name)
            return True
        return False

    def get_possible_follow_ups(self, move_name: str) -> List[Move]:
        node_key = move_name.lower()
        if node_key not in self.graph:
            return []
        successor_keys = self.graph.successors(node_key)
        return [self.moves_map[succ] for succ in successor_keys]

    def export_graph_data(self) -> Dict[str, Any]:
        return {
            "nodes": list(self.graph.nodes()),
            "edges": list(self.graph.edges(data=True))
        }