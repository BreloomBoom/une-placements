import csv
import sys
from ortools.linear_solver import pywraplp

if len(sys.argv) != 3:
    print('Usage: python3 placements.py [school file] [student file]')
    sys.exit(1)

schools = list(csv.reader(open(sys.argv[1], 'r'), delimiter=','))
students = list(csv.reader(open(sys.argv[2], 'r'), delimiter=','))
ranks = [[int(rank) for rank in student[1:]] for student in students]

num_students = len(students)
num_schools = len(schools)

solver = pywraplp.Solver.CreateSolver("SCIP")

# x[i, j] is an array of 0-1 variables, which will be 1
# if student i is assigned to school j
x = {}
for i in range(num_students):
    for j in range(num_schools):
        x[i, j] = solver.IntVar(0, 1, "")

# Each student is assigned to exactly 1 school
for i in range(num_students):
    solver.Add(solver.Sum([x[i, j] for j in range(num_schools)]) == 1)

# Each school is assigned to at most the given capacity
for j in range(num_schools):
    solver.Add(solver.Sum([x[i, j] for i in range(num_students)]) <= int(schools[j][1]))

objective_terms = []
for i in range(num_students):
    for j in range(num_schools):
        objective_terms.append(ranks[i][j] * x[i, j])
solver.Minimize(solver.Sum(objective_terms))

status = solver.Solve()

print(f"Sum of Rankings = {int(solver.Objective().Value())}\n")
for i in range(num_students):
    for j in range(num_schools):
        # Test if x[i,j] is 1 (with tolerance for floating point arithmetic).
        if x[i, j].solution_value() > 0.5:
            print(f"{students[i][0]} assigned to {schools[j][0]} which they ranked {ranks[i][j]}")