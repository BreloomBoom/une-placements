import csv
import sys
from ortools.linear_solver import pywraplp

# Scaling for preference between Year 4, Year 5 and Pathways
scaling = [1, 1.2, 1.5]

if len(sys.argv) != 4:
    print('Usage: python3 placements.py [school file] [pathway file] [student file]')
    sys.exit(1)

schools = list(csv.reader(open(sys.argv[1], 'r'), delimiter=','))
pathways = list(csv.reader(open(sys.argv[2], 'r'), delimiter=','))
students = list(csv.reader(open(sys.argv[3], 'r'), delimiter=','))

num_students = len(students)
num_pathways = len(pathways)
num_schools = len(schools)

y4_ranks = [[int(rank) * scaling[int(student[2 * num_schools + num_pathways + 1]) - 1] for rank in student[1:num_schools + 1]] for student in students]
y5_ranks = [[int(rank) * scaling[int(student[2 * num_schools + num_pathways + 2]) - 1] for rank in student[num_schools + 1:2 * num_schools + 1]] for student in students]
path_ranks = [[int(rank) * scaling[int(student[2 * num_schools + num_pathways + 3]) - 1] for rank in student[2 * num_schools + 1:2 * num_schools + num_pathways + 1]] for student in students]

if num_students > sum([int(capacity[1]) for capacity in schools]):
    print('There are more students than school spots available')
    sys.exit(1)

if num_students > sum([int(capacity[1]) for capacity in pathways]):
    print('There are more students than pathway spots available')
    sys.exit(1)

if any(len(student) <= 2 * num_schools + num_pathways for student in students):
    print('Students needs to have a ranking for all schools and pathways')
    sys.exit(1)

solver = pywraplp.Solver.CreateSolver("SCIP")

# Having the solver assign either 0 or 1 where 1 means  the option is chosen
y4, y5, path = {}, {}, {}
for i in range(num_students):
    for j in range(num_schools):
        y4[i, j] = solver.IntVar(0, 1, "")
        y5[i, j] = solver.IntVar(0, 1, "")
    
    for j in range(num_pathways):
        path[i, j] = solver.IntVar(0, 1, "")

# Constraints

# Each student is assigned to exactly 1 school in y4, y5 and 1 pathway
for i in range(num_students):
    solver.Add(solver.Sum([y4[i, j] for j in range(num_schools)]) == 1)
    solver.Add(solver.Sum([y5[i, j] for j in range(num_schools)]) == 1)
    solver.Add(solver.Sum([path[i, j] for j in range(num_pathways)]) == 1)
    # There must be at least 1 metro school between y4 and y5
    solver.Add(solver.Sum([y4[i, j] * int(schools[j][2] == 'M') for j in range(num_schools)]) + 
               solver.Sum([y5[i, j] * int(schools[j][2] == 'M') for j in range(num_schools)]) >= 1)

# Each school and pathway is assigned to at most the given capacity
for j in range(num_schools):
    solver.Add(solver.Sum([y4[i, j] for i in range(num_students)]) <= int(schools[j][1]))
    solver.Add(solver.Sum([y5[i, j] for i in range(num_students)]) <= int(schools[j][1]))

for j in range(num_pathways):
    solver.Add(solver.Sum([path[i, j] for i in range(num_students)]) <= int(pathways[j][1]))

objective_terms = []
for i in range(num_students):
    for j in range(num_schools):
        objective_terms.append(y4_ranks[i][j] * y4[i, j])
        objective_terms.append(y5_ranks[i][j] * y5[i, j])
    
    for j in range(num_pathways):
        objective_terms.append(path_ranks[i][j] * path[i, j])
solver.Minimize(solver.Sum(objective_terms))

status = solver.Solve()

for i in range(num_students):
    for j in range(num_schools):
        if y4[i, j].solution_value() > 0.5:
            print(f"{students[i][0]} assigned to {schools[j][0]} in Year 4")

    for j in range(num_schools):
        if y5[i, j].solution_value() > 0.5:
            print(f"{students[i][0]} assigned to {schools[j][0]} in Year 5")

    for j in range(num_pathways):
        if path[i, j].solution_value() > 0.5:
            print(f"{students[i][0]} assigned to the pathway {pathways[j][0]}\n")