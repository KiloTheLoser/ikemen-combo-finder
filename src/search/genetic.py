import random
from typing import List, Dict, Any
import numpy as np
from deap import base, creator, tools, algorithms

from src.model.move import Move
from src.model.cancel_graph import CancelGraph
from src.search.fitness import evaluate_combo

# Setup DEAP fitness and individual structure globally if not already created
if not hasattr(creator, "FitnessMax"):
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
if not hasattr(creator, "Individual"):
    creator.create("Individual", list, fitness=creator.FitnessMax)

def run_genetic_search(
    moves: List[Move],
    cancel_graph: CancelGraph,
    max_combo_length: int = 8,
    population_size: int = 100,
    generations: int = 40,
    mutation_rate: float = 0.2
) -> List[Dict[str, Any]]:
    """
    Executes a Genetic Algorithm to discover high-scoring combo sequences.
    """
    if not moves:
        return []

    moves_map = {m.name.lower(): m for m in moves}
    move_names = [m.name for m in moves]

    toolbox = base.Toolbox()

    # Attribute generator: pick a random move name from available pool
    toolbox.register("attr_move", random.choice, move_names)

    # Structure initializers: individual is a list of move names of random size (1 to max_combo_length)
    toolbox.register(
        "individual",
        tools.initRepeat,
        creator.Individual,
        toolbox.attr_move,
        n=random.randint(2, max_combo_length)
    )
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    # Fitness evaluation wrapper
    toolbox.register("evaluate", evaluate_combo, moves_map=moves_map, cancel_graph=cancel_graph)

    # Genetic Operators
    toolbox.register("mate", tools.cxTwoPoint)
    
    def mutate_individual(individual):
        """Custom mutation: can swap items, replace an item, or resize sequence."""
        mutation_type = random.choice(["replace", "add", "remove", "swap"])
        
        if mutation_type == "replace" and len(individual) > 0:
            idx = random.randrange(len(individual))
            individual[idx] = random.choice(move_names)
        elif mutation_type == "add" and len(individual) < max_combo_length:
            individual.append(random.choice(move_names))
        elif mutation_type == "remove" and len(individual) > 2:
            del individual[random.randrange(len(individual))]
        elif mutation_type == "swap" and len(individual) > 1:
            idx1, idx2 = random.sample(range(len(individual)), 2)
            individual[idx1], individual[idx2] = individual[idx2], individual[idx1]
            
        return individual,

    toolbox.register("mutate", mutate_individual)
    
    # PERBAIKAN: DEAP algorithms.eaSimple secara internal mencari toolbox.select, bukan toolbox.selection
    toolbox.register("select", tools.selTournament, tournsize=3)

    # Initialize population
    pop = toolbox.population(n=population_size)
    
    # Statistics tracking setup
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("max", np.max)
    stats.register("avg", np.mean)

    # Run standard eaSimple genetic algorithm loop
    population, logbook = algorithms.eaSimple(
        pop, toolbox,
        cxpb=0.5,
        mutpb=mutation_rate,
        ngen=generations,
        stats=stats,
        verbose=False
    )

    # Extract top unique resulting combos
    seen_combos = set()
    top_results = []

    # Sort population by fitness descending
    best_individuals = sorted(population, key=lambda ind: ind.fitness.values[0], reverse=True)

    for ind in best_individuals:
        combo_tuple = tuple(ind)
        if combo_tuple not in seen_combos:
            seen_combos.add(combo_tuple)
            
            # Compute final damage & profile context
            seq_moves = [moves_map[n.lower()] for n in ind if n.lower() in moves_map]
            est_dmg = sum(m.damage if m.damage else 20 for m in seq_moves)
            
            top_results.append({
                "sequence": list(ind),
                "length": len(ind),
                "estimated_damage": est_dmg,
                "fitness_score": float(ind.fitness.values[0])
            })
            
            if len(top_results) >= 15: # Keep top 15 unique sequences
                break

    return top_results