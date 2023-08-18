"""
This script takes student preferences with school and pathway 
capacities to assign each student their schools and pathways

Usage: python3 placements.py [school file] [pathway file] [student file]
"""

import csv
import sys
from ortools.linear_solver import pywraplp

# Scaling for preference between Year 4, Year 5 and Pathways
scaling = [1, 1.2, 1.5]

def load_data(file_name, delimiter=','):
    return list(csv.reader(open(file_name, 'r'), delimiter=','))

def check_errors(schools, pathways, students):
    if len(students) > sum([int(capacity[1]) for capacity in schools]):
        print('There are more students than school spots available')
        sys.exit(1)
    elif len(students) > sum([int(capacity[1]) for capacity in pathways]):
        print('There are more students than pathway spots available')
        sys.exit(1)
    elif any(len(student) <= 2 * len(schools) + len(pathways) + 3 for student in students):
        print('Students needs to have a ranking for all schools and pathways')
        sys.exit(1)

def calc_ranks(students, start, end, scale):
    return [[int(rank) * scaling[int(student[scale]) - 1] for rank in student[start:end]] for student in students]

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print('Usage: python3 placements.py [school file] [pathway file] [student file]')
        sys.exit(1)

    schools = load_data(sys.argv[1])
    pathways = load_data(sys.argv[2])
    students = load_data(sys.argv[3])

    num_students = len(students)
    num_pathways = len(pathways)
    num_schools = len(schools)

    check_errors(schools, pathways, students)

    cols = [1, num_schools + 1, 2 * num_schools + 1, 2 * num_schools + num_pathways + 1]
    y4_ranks = calc_ranks(students, cols[0], cols[1], cols[3])
    y5_ranks = calc_ranks(students, cols[1], cols[2], cols[3] + 1)
    path_ranks = calc_ranks(students, cols[2], cols[3], cols[3] + 2)

    solver = pywraplp.Solver.CreateSolver("SCIP")

    # having the solver assign either 0 or 1 where 1 means  the option is chosen
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
        solver.Add(
            solver.Sum([y4[i, j] * int(schools[j][2] == 'M') for j in range(num_schools)]) + 
            solver.Sum([y5[i, j] * int(schools[j][2] == 'M') for j in range(num_schools)]) 
            >= 1
        )

    # Each school and pathway is assigned to at most the given capacity
    for j in range(num_schools):
        solver.Add(solver.Sum([y4[i, j] for i in range(num_students)]) <= int(schools[j][1]))
        solver.Add(solver.Sum([y5[i, j] for i in range(num_students)]) <= int(schools[j][1]))

    for j in range(num_pathways):
        solver.Add(solver.Sum([path[i, j] for i in range(num_students)]) <= int(pathways[j][1]))


    # adding how the cost is calculated to the solver
    objective_terms = []
    for i in range(num_students):
        for j in range(num_schools):
            objective_terms.append(y4_ranks[i][j] * y4[i, j])
            objective_terms.append(y5_ranks[i][j] * y5[i, j])
        
        for j in range(num_pathways):
            objective_terms.append(path_ranks[i][j] * path[i, j])
    solver.Minimize(solver.Sum(objective_terms))

    status = solver.Solve()

    if status not in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
        print("No possible assignment found")
        sys.exit()

    # printing out the solution
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