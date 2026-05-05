# Homework 3 - Salesman / TSP

This project solves **Topic 1** of Homework 3:

- Traveling Salesman Problem with **51 cities**
- Forbidden edges: **(1, 22)** and **(1, 32)**
- Main solver: **Genetic Algorithm**
- Comparison solver: **Simulated Annealing**

## Structure

- `saleman/solver.py`: core TSP, GA, and SA implementation
- `saleman/run_experiment.py`: runs experiments and saves plots/results
- `saleman/build_report.py`: creates `HW3_TSP_report.pdf`
- `saleman/make_submission_notebook.py`: creates `salesman_hw3.ipynb`
- `outputs/`: generated plots and result summary

## Run

```bash
python -m saleman.run_experiment
python -m saleman.build_report
python -m saleman.make_submission_notebook
```

## Expected outputs

- `outputs/results.json`
- `outputs/ga_history.png`
- `outputs/sa_history.png`
- `outputs/ga_route.png`
- `outputs/sa_route.png`
- `outputs/comparison.png`
- `salesman_hw3.ipynb`
- `HW3_TSP_report.pdf`
