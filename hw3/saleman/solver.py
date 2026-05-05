from __future__ import annotations

import math
import random
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence


def _parse_dataset(dataset_path: str | Path) -> dict[int, tuple[float, float]]:
    coordinates: dict[int, tuple[float, float]] = {}
    for raw_line in Path(dataset_path).read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        city_id_text, x_text, y_text = line.split()
        coordinates[int(city_id_text)] = (float(x_text), float(y_text))
    if not coordinates:
        raise ValueError(f"Dataset {dataset_path!s} does not contain any city coordinates.")
    return coordinates


class TSPProblem:
    def __init__(
        self,
        coordinates: dict[int, tuple[float, float]],
        start_city: int = 1,
        forbidden_edges: Iterable[tuple[int, int]] | None = None,
    ) -> None:
        self.coordinates = coordinates
        self.start_city = start_city
        self.city_ids = sorted(coordinates)
        self.other_cities = [city for city in self.city_ids if city != start_city]
        self.forbidden_edges = {
            frozenset(edge) for edge in (forbidden_edges or {(1, 22), (1, 32)})
        }
        self.forbidden_start_neighbors = self._compute_forbidden_start_neighbors()
        self.distance_matrix = self._build_distance_matrix()

        if start_city not in coordinates:
            raise ValueError(f"Start city {start_city} is not present in the dataset.")

    @classmethod
    def from_dataset(cls, dataset_path: str | Path) -> "TSPProblem":
        return cls(_parse_dataset(dataset_path))

    def _compute_forbidden_start_neighbors(self) -> set[int]:
        neighbors: set[int] = set()
        for edge in self.forbidden_edges:
            if self.start_city in edge:
                other_cities = tuple(edge - {self.start_city})
                if other_cities:
                    neighbors.add(other_cities[0])
        return neighbors

    def _build_distance_matrix(self) -> dict[int, dict[int, float]]:
        matrix: dict[int, dict[int, float]] = {}
        for city_a in self.city_ids:
            matrix[city_a] = {}
            x_a, y_a = self.coordinates[city_a]
            for city_b in self.city_ids:
                if city_a == city_b:
                    matrix[city_a][city_b] = 0.0
                    continue
                x_b, y_b = self.coordinates[city_b]
                matrix[city_a][city_b] = math.hypot(x_a - x_b, y_a - y_b)
        return matrix

    def distance(self, city_a: int, city_b: int) -> float:
        return self.distance_matrix[city_a][city_b]

    def is_forbidden_edge(self, city_a: int, city_b: int) -> bool:
        return frozenset((city_a, city_b)) in self.forbidden_edges

    def route_with_start(self, genes: Sequence[int]) -> list[int]:
        return [self.start_city, *genes, self.start_city]

    def is_feasible(self, genes: Sequence[int]) -> bool:
        return math.isfinite(self.route_length(genes))

    def route_length(self, genes: Sequence[int]) -> float:
        genes = list(genes)
        if len(genes) != len(self.other_cities):
            return math.inf
        if set(genes) != set(self.other_cities):
            return math.inf
        return self._constrained_distance(genes)

    def _base_route_distance(self, genes: Sequence[int]) -> float:
        genes = list(genes)
        if not genes:
            return 0.0

        total_distance = self.distance(self.start_city, genes[0])
        for city_a, city_b in zip(genes, genes[1:]):
            if self.is_forbidden_edge(city_a, city_b):
                return math.inf
            total_distance += self.distance(city_a, city_b)
        total_distance += self.distance(genes[-1], self.start_city)
        return total_distance

    def _constrained_distance(self, genes: Sequence[int]) -> float:
        if not genes:
            return 0.0
        if genes[0] in self.forbidden_start_neighbors:
            return math.inf
        if genes[-1] in self.forbidden_start_neighbors:
            return math.inf
        return self._base_route_distance(genes)

    def fitness(self, genes: Sequence[int]) -> float:
        route_cost = self.route_length(genes)
        if not math.isfinite(route_cost):
            return 0.0
        return 1.0 / (1.0 + route_cost)

    def repair_endpoints(self, genes: Sequence[int]) -> list[int]:
        repaired = list(genes)
        if not repaired:
            return repaired

        endpoint_indices = (0, len(repaired) - 1)
        for endpoint_index in endpoint_indices:
            if repaired[endpoint_index] not in self.forbidden_start_neighbors:
                continue

            best_swap_index = None
            best_cost = math.inf
            for swap_index in range(len(repaired)):
                if swap_index == endpoint_index:
                    continue
                if repaired[swap_index] in self.forbidden_start_neighbors:
                    continue
                candidate = repaired.copy()
                candidate[endpoint_index], candidate[swap_index] = (
                    candidate[swap_index],
                    candidate[endpoint_index],
                )
                candidate_cost = self._base_route_distance(candidate)
                if candidate[0] in self.forbidden_start_neighbors:
                    candidate_cost += 1_000_000
                if candidate[-1] in self.forbidden_start_neighbors:
                    candidate_cost += 1_000_000
                if candidate_cost < best_cost:
                    best_cost = candidate_cost
                    best_swap_index = swap_index

            if best_swap_index is None:
                raise ValueError("Unable to repair route endpoints for forbidden start edges.")

            repaired[endpoint_index], repaired[best_swap_index] = (
                repaired[best_swap_index],
                repaired[endpoint_index],
            )

        return repaired

    def random_feasible_genes(self, rng: random.Random) -> list[int]:
        genes = self.other_cities.copy()
        rng.shuffle(genes)
        return self.repair_endpoints(genes)

    def nearest_neighbor_genes(self) -> list[int]:
        remaining = set(self.other_cities)
        genes: list[int] = []
        current_city = self.start_city

        while remaining:
            candidates = [
                city
                for city in remaining
                if not (
                    current_city == self.start_city
                    and city in self.forbidden_start_neighbors
                )
                and not (
                    len(remaining) == 1 and city in self.forbidden_start_neighbors
                )
            ]
            if not candidates:
                candidates = list(remaining)

            next_city = min(candidates, key=lambda city: (self.distance(current_city, city), city))
            genes.append(next_city)
            remaining.remove(next_city)
            current_city = next_city

        return self.repair_endpoints(genes)


@dataclass
class GAConfig:
    population_size: int = 320
    generations: int = 700
    crossover_rate: float = 0.95
    mutation_rate: float = 0.35
    tournament_size: int = 5
    elite_size: int = 16
    immigrant_count: int = 12
    seed: int = 42


@dataclass
class SAConfig:
    cooling_rate: float = 0.99995
    iterations_per_temperature: int = 1
    max_steps: int = 100000
    min_temperature: float = 1e-4
    target_acceptance: float = 0.8
    initial_perturbations: int = 0
    initial_temperature: float | None = None
    seed: int = 1234


@dataclass
class RunResult:
    algorithm: str
    best_genes: list[int]
    best_distance: float
    history_best: list[float]
    history_aux: list[float]
    runtime_seconds: float
    config: dict[str, int | float | None]
    temperature_history: list[float] | None = None

    @property
    def best_route(self) -> list[int]:
        return [1, *self.best_genes, 1]

    def to_dict(self) -> dict[str, object]:
        return {
            "algorithm": self.algorithm,
            "best_distance": self.best_distance,
            "best_route": self.best_route,
            "runtime_seconds": self.runtime_seconds,
            "history_best": self.history_best,
            "history_aux": self.history_aux,
            "temperature_history": self.temperature_history,
            "config": self.config,
        }


def _tournament_select(
    population: Sequence[Sequence[int]],
    costs: Sequence[float],
    tournament_size: int,
    rng: random.Random,
) -> list[int]:
    competitors = rng.sample(range(len(population)), k=tournament_size)
    winner_index = min(competitors, key=lambda index: costs[index])
    return list(population[winner_index])


def _order_crossover(parent_a: Sequence[int], parent_b: Sequence[int], rng: random.Random) -> list[int]:
    size = len(parent_a)
    left, right = sorted(rng.sample(range(size), k=2))
    child: list[int | None] = [None] * size
    child[left : right + 1] = parent_a[left : right + 1]

    fill_values = [city for city in parent_b if city not in child]
    fill_iter = iter(fill_values)
    for index, value in enumerate(child):
        if value is None:
            child[index] = next(fill_iter)

    return [int(city) for city in child]


def _mutate_genes(genes: Sequence[int], rng: random.Random) -> list[int]:
    mutated = list(genes)
    move_type = rng.choice(("swap", "insert", "invert"))
    index_a, index_b = rng.sample(range(len(mutated)), k=2)

    if move_type == "swap":
        mutated[index_a], mutated[index_b] = mutated[index_b], mutated[index_a]
    elif move_type == "insert":
        city = mutated.pop(index_a)
        mutated.insert(index_b, city)
    else:
        left, right = sorted((index_a, index_b))
        mutated[left : right + 1] = reversed(mutated[left : right + 1])

    if rng.random() < 0.2:
        left, right = sorted(rng.sample(range(len(mutated)), k=2))
        mutated[left : right + 1] = reversed(mutated[left : right + 1])

    return mutated


def _build_initial_population(problem: TSPProblem, config: GAConfig, rng: random.Random) -> list[list[int]]:
    population: list[list[int]] = []
    seed_route = problem.nearest_neighbor_genes()
    population.append(seed_route.copy())

    seeded_count = max(8, config.population_size // 5)
    while len(population) < config.population_size:
        if len(population) < seeded_count:
            candidate = seed_route.copy()
            for _ in range(rng.randint(1, 4)):
                candidate = problem.repair_endpoints(_mutate_genes(candidate, rng))
            population.append(candidate)
            continue

        population.append(problem.random_feasible_genes(rng))

    return population


def solve_with_ga(problem: TSPProblem, config: GAConfig | None = None) -> RunResult:
    config = config or GAConfig()
    rng = random.Random(config.seed)
    population = _build_initial_population(problem, config, rng)
    best_genes = population[0].copy()
    best_distance = problem.route_length(best_genes)
    history_best: list[float] = []
    history_mean: list[float] = []
    started_at = time.perf_counter()

    for _ in range(config.generations):
        costs = [problem.route_length(individual) for individual in population]
        ranked_indices = sorted(range(len(population)), key=lambda index: costs[index])

        generation_best = costs[ranked_indices[0]]
        if generation_best < best_distance:
            best_distance = generation_best
            best_genes = population[ranked_indices[0]].copy()

        history_best.append(best_distance)
        history_mean.append(statistics.fmean(costs))

        next_population = [population[index].copy() for index in ranked_indices[: config.elite_size]]
        target_size_before_immigrants = config.population_size - config.immigrant_count

        while len(next_population) < target_size_before_immigrants:
            parent_a = _tournament_select(population, costs, config.tournament_size, rng)
            parent_b = _tournament_select(population, costs, config.tournament_size, rng)

            if rng.random() < config.crossover_rate:
                child_a = _order_crossover(parent_a, parent_b, rng)
                child_b = _order_crossover(parent_b, parent_a, rng)
            else:
                child_a = parent_a.copy()
                child_b = parent_b.copy()

            if rng.random() < config.mutation_rate:
                child_a = _mutate_genes(child_a, rng)
            if rng.random() < config.mutation_rate:
                child_b = _mutate_genes(child_b, rng)

            next_population.append(problem.repair_endpoints(child_a))
            if len(next_population) < target_size_before_immigrants:
                next_population.append(problem.repair_endpoints(child_b))

        while len(next_population) < config.population_size:
            next_population.append(problem.random_feasible_genes(rng))

        population = next_population

    runtime_seconds = time.perf_counter() - started_at
    return RunResult(
        algorithm="Genetic Algorithm",
        best_genes=best_genes,
        best_distance=best_distance,
        history_best=history_best,
        history_aux=history_mean,
        runtime_seconds=runtime_seconds,
        config=asdict(config),
    )


def _neighbor(genes: Sequence[int], rng: random.Random) -> list[int]:
    candidate = list(genes)
    left, right = sorted(rng.sample(range(len(candidate)), k=2))
    candidate[left : right + 1] = reversed(candidate[left : right + 1])
    return candidate


def _estimate_initial_temperature(
    problem: TSPProblem,
    genes: Sequence[int],
    rng: random.Random,
    target_acceptance: float,
) -> float:
    current = list(genes)
    current_cost = problem.route_length(current)
    positive_deltas: list[float] = []

    for _ in range(80):
        neighbor = problem.repair_endpoints(_neighbor(current, rng))
        neighbor_cost = problem.route_length(neighbor)
        delta = neighbor_cost - current_cost
        if delta > 0:
            positive_deltas.append(delta)
        current = neighbor
        current_cost = neighbor_cost

    if not positive_deltas:
        return max(1.0, problem.route_length(genes) * 0.05)

    average_positive_delta = statistics.fmean(positive_deltas)
    return -average_positive_delta / math.log(target_acceptance)


def solve_with_sa(problem: TSPProblem, config: SAConfig | None = None) -> RunResult:
    config = config or SAConfig()
    rng = random.Random(config.seed)
    current_genes = problem.nearest_neighbor_genes()
    for _ in range(config.initial_perturbations):
        current_genes = problem.repair_endpoints(_neighbor(current_genes, rng))

    current_cost = problem.route_length(current_genes)
    best_genes = current_genes.copy()
    best_distance = current_cost
    started_at = time.perf_counter()

    temperature = config.initial_temperature or _estimate_initial_temperature(
        problem,
        current_genes,
        rng,
        config.target_acceptance,
    )

    history_best: list[float] = []
    history_current: list[float] = []
    temperature_history: list[float] = []
    steps = 0

    while steps < config.max_steps and temperature > config.min_temperature:
        for _ in range(config.iterations_per_temperature):
            neighbor = problem.repair_endpoints(_neighbor(current_genes, rng))
            neighbor_cost = problem.route_length(neighbor)
            delta = neighbor_cost - current_cost

            if delta < 0 or rng.random() < math.exp(-delta / temperature):
                current_genes = neighbor
                current_cost = neighbor_cost

            if current_cost < best_distance:
                best_distance = current_cost
                best_genes = current_genes.copy()

            history_current.append(current_cost)
            history_best.append(best_distance)
            temperature_history.append(temperature)
            steps += 1

            if steps >= config.max_steps:
                break

        temperature *= config.cooling_rate

    runtime_seconds = time.perf_counter() - started_at
    return RunResult(
        algorithm="Simulated Annealing",
        best_genes=best_genes,
        best_distance=best_distance,
        history_best=history_best,
        history_aux=history_current,
        runtime_seconds=runtime_seconds,
        config=asdict(config),
        temperature_history=temperature_history,
    )
