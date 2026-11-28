# Introduction to Artificial Intelligence - Final Project

## Project Overview

This project is developed for the Introduction to Artificial Intelligence course.

## Project Tasks

### Task 1: N-Queens
- Propositional Logic
- CNF
- Glucose3 SAT Solver
- Min-Conflicts

### Task 2: Tank Battle Game
- Zero-Sum Game
- Minimax Search
- Alpha-Beta Pruning
- Heuristic Minimax
- PyGame

### Task 3: Kakuro
- Constraint Satisfaction Problems
- Constraint Propagation
- Backtracking Search
- Heuristics
- Graphical User Interface

## Technologies

- Python
- PySAT
- PyGame
- Visual Studio Code
- Git and GitHub

## Project Structure

- source/task1: N-Queens
- source/task2: Tank Battle
- source/task3: Kakuro
- source/data: Test data
- source/notebooks: Jupyter notebooks
- source/results: Experimental results
- report: IEEE report files
- docs: Project documentation

## Installation

Create and activate a virtual environment, then install dependencies:

    pip install -r requirements.txt

## Team Contributions

To be updated.

## Project Status

- Task 1: N-Queens implementation and experimental evaluation completed.
- Task 2: Tank Battle implementation, GUI integration, and testing completed.
- Task 3: Kakuro CSP solver, GUI, and experimental evaluation completed.

Task-specific setup instructions, test commands, and experimental
results are documented in the corresponding task README files.

## Testing

Run Task 3 tests:

    python -m pytest source/task3/tests -v

Run Task 2 tests:

    python -m pytest source/task2/tests -q

Some Task 1 Glucose3 tests may require a Windows environment
that permits loading the PySAT native solver extension.

## Experimental Results

Experimental data and figures are stored under:

    source/results/task1/
    source/results/task2/
    source/results/task3/

## Documentation

- Task 3: source/task3/README.md
- IEEE report: report/ieee/
- Project documentation: docs/