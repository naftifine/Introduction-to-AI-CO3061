from __future__ import annotations

import json
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


def _add_text_page(pdf: PdfPages, summary: dict[str, object]) -> None:
    ga = summary["ga"]
    sa = summary["sa"]
    fig = plt.figure(figsize=(8.27, 11.69))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")

    route_text = textwrap.fill(
        " -> ".join(map(str, ga["best_route"])),
        width=84,
    )

    lines = [
        "Homework 3 - Traveling Salesman Problem",
        "",
        "Dataset:",
        f"{summary['dataset']} with {summary['city_count']} cities",
        f"Forbidden edges: {summary['forbidden_edges']}",
        "",
        "Design choices:",
        "- Chromosome: permutation of 50 cities with city 1 fixed as start/end",
        "- Fitness: 1 / (1 + total route distance)",
        "- Selection: tournament selection",
        "- Crossover: order crossover (OX)",
        "- Mutation: swap / insert / inversion",
        "- Additional solver for comparison: Simulated Annealing",
        "",
        "Best results:",
        f"- GA best distance: {ga['best_distance']:.2f} (runtime {ga['runtime_seconds']:.2f}s)",
        f"- SA best distance: {sa['best_distance']:.2f} (runtime {sa['runtime_seconds']:.2f}s)",
        "",
        "Best GA route:",
        route_text,
    ]

    ax.text(
        0.06,
        0.965,
        "\n".join(lines),
        va="top",
        fontsize=11,
        family="monospace",
    )
    pdf.savefig(fig)
    plt.close(fig)


def _add_image_page(pdf: PdfPages, title: str, left_image: Path, right_image: Path) -> None:
    fig, axes = plt.subplots(ncols=2, figsize=(11.69, 8.27))
    fig.suptitle(title, fontsize=16)

    for axis, image_path, label in zip(
        axes,
        (left_image, right_image),
        ("Left", "Right"),
    ):
        axis.imshow(mpimg.imread(image_path))
        axis.set_title(image_path.stem.replace("_", " ").title())
        axis.axis("off")

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    pdf.savefig(fig)
    plt.close(fig)


def build_report(
    results_path: str | Path = "outputs/results.json",
    output_pdf: str | Path = "HW3_TSP_report.pdf",
) -> Path:
    results_path = Path(results_path)
    output_pdf = Path(output_pdf)
    summary = json.loads(results_path.read_text(encoding="utf-8"))
    output_dir = results_path.parent

    with PdfPages(output_pdf) as pdf:
        _add_text_page(pdf, summary)
        _add_image_page(pdf, "Convergence history", output_dir / "ga_history.png", output_dir / "sa_history.png")
        _add_image_page(pdf, "Best tours", output_dir / "ga_route.png", output_dir / "sa_route.png")
        fig, ax = plt.subplots(figsize=(11.69, 8.27))
        ax.imshow(mpimg.imread(output_dir / "comparison.png"))
        ax.axis("off")
        ax.set_title("Distance and runtime comparison", fontsize=16)
        fig.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)

    return output_pdf


if __name__ == "__main__":
    report_path = build_report()
    print(f"Created report: {report_path}")
