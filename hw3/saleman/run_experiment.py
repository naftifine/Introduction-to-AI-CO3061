from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.image as mpimg
import matplotlib.pyplot as plt

from .solver import GAConfig, RunResult, SAConfig, TSPProblem, solve_with_ga, solve_with_sa


def _ensure_output_dir(output_dir: str | Path) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def _plot_route(problem: TSPProblem, result: RunResult, image_path: str | Path) -> None:
    image_path = Path(image_path)
    route = result.best_route
    x_values = [problem.coordinates[city][0] for city in route]
    y_values = [problem.coordinates[city][1] for city in route]

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.plot(x_values, y_values, color="#1f77b4", linewidth=1.3, alpha=0.85)
    ax.scatter(x_values[:-1], y_values[:-1], c=range(len(route) - 1), cmap="viridis", s=42)
    ax.scatter(
        [problem.coordinates[problem.start_city][0]],
        [problem.coordinates[problem.start_city][1]],
        s=140,
        marker="*",
        color="crimson",
        label="Start / End city 1",
        zorder=5,
    )

    for city_id, (x_coord, y_coord) in problem.coordinates.items():
        ax.text(x_coord + 0.55, y_coord + 0.55, str(city_id), fontsize=6.5)

    ax.set_title(f"{result.algorithm} best tour | distance = {result.best_distance:.2f}")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.grid(alpha=0.2)
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(image_path, dpi=180)
    plt.close(fig)


def _plot_ga_history(result: RunResult, image_path: str | Path) -> None:
    image_path = Path(image_path)
    generations = range(1, len(result.history_best) + 1)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(generations, result.history_best, label="Best distance", linewidth=2.0, color="#d62728")
    ax.plot(generations, result.history_aux, label="Average distance", linewidth=1.5, color="#1f77b4")
    ax.set_title("Genetic Algorithm convergence")
    ax.set_xlabel("Generation")
    ax.set_ylabel("Tour distance")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(image_path, dpi=180)
    plt.close(fig)


def _plot_sa_history(result: RunResult, image_path: str | Path) -> None:
    image_path = Path(image_path)
    iterations = range(1, len(result.history_best) + 1)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(iterations, result.history_aux, label="Current distance", linewidth=1.0, alpha=0.55, color="#1f77b4")
    ax.plot(iterations, result.history_best, label="Best-so-far distance", linewidth=2.0, color="#d62728")
    ax.set_title("Simulated Annealing convergence")
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Tour distance")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(image_path, dpi=180)
    plt.close(fig)


def _plot_comparison(ga_result: RunResult, sa_result: RunResult, image_path: str | Path) -> None:
    image_path = Path(image_path)
    fig, axes = plt.subplots(ncols=2, figsize=(11, 5.5))

    axes[0].bar(["GA", "SA"], [ga_result.best_distance, sa_result.best_distance], color=["#4c78a8", "#f58518"])
    axes[0].set_title("Best tour distance")
    axes[0].set_ylabel("Distance")
    axes[0].grid(axis="y", alpha=0.25)

    axes[1].bar(["GA", "SA"], [ga_result.runtime_seconds, sa_result.runtime_seconds], color=["#4c78a8", "#f58518"])
    axes[1].set_title("Runtime")
    axes[1].set_ylabel("Seconds")
    axes[1].grid(axis="y", alpha=0.25)

    fig.tight_layout()
    fig.savefig(image_path, dpi=180)
    plt.close(fig)


def _serialize_result(result: RunResult) -> dict[str, object]:
    return result.to_dict()


def _serialize_trial_overview(result: RunResult) -> dict[str, object]:
    return {
        "algorithm": result.algorithm,
        "best_distance": result.best_distance,
        "runtime_seconds": result.runtime_seconds,
        "seed": result.config.get("seed"),
    }


def load_results(results_path: str | Path) -> dict[str, object]:
    return json.loads(Path(results_path).read_text(encoding="utf-8"))


def run_experiment(
    dataset_path: str | Path = "TSP51_dataset.txt",
    output_dir: str | Path = "outputs",
    ga_trials: int = 4,
    sa_trials: int = 4,
    base_seed: int = 42,
    reuse_existing: bool = False,
) -> dict[str, object]:
    output_path = _ensure_output_dir(output_dir)
    results_path = output_path / "results.json"
    if reuse_existing and results_path.exists():
        return load_results(results_path)

    dataset_path = Path(dataset_path)
    problem = TSPProblem.from_dataset(dataset_path)

    ga_runs = [
        solve_with_ga(problem, GAConfig(seed=base_seed + trial_index * 97))
        for trial_index in range(ga_trials)
    ]
    sa_runs = [
        solve_with_sa(problem, SAConfig(seed=base_seed + trial_index * 97))
        for trial_index in range(sa_trials)
    ]

    best_ga = min(ga_runs, key=lambda result: result.best_distance)
    best_sa = min(sa_runs, key=lambda result: result.best_distance)

    _plot_ga_history(best_ga, output_path / "ga_history.png")
    _plot_sa_history(best_sa, output_path / "sa_history.png")
    _plot_route(problem, best_ga, output_path / "ga_route.png")
    _plot_route(problem, best_sa, output_path / "sa_route.png")
    _plot_comparison(best_ga, best_sa, output_path / "comparison.png")

    summary = {
        "dataset": str(dataset_path),
        "city_count": len(problem.city_ids),
        "forbidden_edges": sorted([sorted(edge) for edge in problem.forbidden_edges]),
        "ga": _serialize_result(best_ga),
        "ga_trials": [_serialize_trial_overview(result) for result in ga_runs],
        "sa": _serialize_result(best_sa),
        "sa_trials": [_serialize_trial_overview(result) for result in sa_runs],
    }
    results_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def _print_summary(summary: dict[str, object]) -> None:
    ga = summary["ga"]
    sa = summary["sa"]
    print("=== Homework 3 - TSP Summary ===")
    print(f"Dataset: {summary['dataset']}")
    print(f"Cities: {summary['city_count']}")
    print(f"Forbidden edges: {summary['forbidden_edges']}")
    print(f"GA best distance: {ga['best_distance']:.2f} | runtime: {ga['runtime_seconds']:.2f}s")
    print(f"SA best distance: {sa['best_distance']:.2f} | runtime: {sa['runtime_seconds']:.2f}s")
    print("Output directory: outputs")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run GA and SA experiments for Homework 3 TSP.")
    parser.add_argument("--dataset", default="TSP51_dataset.txt", help="Path to the dataset text file.")
    parser.add_argument("--output-dir", default="outputs", help="Directory used to save results and figures.")
    parser.add_argument("--ga-trials", type=int, default=4, help="Number of GA runs.")
    parser.add_argument("--sa-trials", type=int, default=4, help="Number of SA runs.")
    parser.add_argument("--base-seed", type=int, default=42, help="Base random seed.")
    parser.add_argument(
        "--reuse-existing",
        action="store_true",
        help="Load outputs/results.json if it already exists.",
    )
    args = parser.parse_args()

    summary = run_experiment(
        dataset_path=args.dataset,
        output_dir=args.output_dir,
        ga_trials=args.ga_trials,
        sa_trials=args.sa_trials,
        base_seed=args.base_seed,
        reuse_existing=args.reuse_existing,
    )
    _print_summary(summary)


if __name__ == "__main__":
    main()
