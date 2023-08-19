'''
This script takes student preferences with school and pathway 
capacities to assign each student their schools and pathways

Usage: python3 placements.py [school file] [pathway file] [student file]
'''

import csv
import sys

from ortools.linear_solver import pywraplp

import config as cfg

def check_cmd_line_args():
    if len(sys.argv) != 4:
        print('Usage: python3 placements.py [school file] [pathway file] [student file]')
        sys.exit(1)

def load_data(file_name, delim=','):
    return list(csv.reader(open(file_name, 'r'), delimiter=delim))

def load_all(*files):
    return [load_data(file) for file in files]

def check_errors(schools, pathways, students):
    if len(students) > sum([int(capacity[1]) for capacity in schools]):
        print('There are more students than school spots available')
        sys.exit(1)
    elif len(students) > sum([int(capacity[1]) for capacity in pathways]):
        print('There are more students than pathway spots available')
        sys.exit(1)
    elif any(len(student) != 2 * len(schools) + len(pathways) + 4 for student in students):
        print('Students needs to have a ranking for all schools and pathways')
        sys.exit(1)

def calc_ranks(students, start, end, scale):
    return [[int(rank) * cfg.scaling[int(student[scale]) - 1] for rank in student[start:end]] for student in students]

def solver_variables(solver, num_students, num_choices):
    variables = {}
    for i in range(num_students):
        for j in range(num_choices):
            variables[i, j] = solver.IntVar(0, 1, '')
    
    return variables

def set_constraints(solver, num_students, schools, pathways, y4, y5, path):
    # Each student is assigned to exactly 1 school in y4, y5 and 1 pathway
    for i in range(num_students):
        solver.Add(solver.Sum([y4[i, j] for j in range(len(schools))]) == 1)
        solver.Add(solver.Sum([y5[i, j] for j in range(len(schools))]) == 1)
        solver.Add(solver.Sum([path[i, j] for j in range(len(pathways))]) == 1)

        # There must be at least 1 metro school between y4 and y5
        solver.Add(
            solver.Sum([y4[i, j] * int(schools[j][3] == 'M') for j in range(len(schools))]) + 
            solver.Sum([y5[i, j] * int(schools[j][3] == 'M') for j in range(len(schools))]) 
            >= 1
        )

    # Each school and pathway is assigned to at most the given capacity
    for j in range(len(schools)):
        solver.Add(solver.Sum([y4[i, j] for i in range(num_students)]) <= int(schools[j][1]))
        solver.Add(solver.Sum([y5[i, j] for i in range(num_students)]) <= int(schools[j][2]))

    for j in range(len(pathways)):
        solver.Add(solver.Sum([path[i, j] for i in range(num_students)]) <= int(pathways[j][1]))

def add_obj_terms(choices, students, ranks, variables, scale=1):
    objective_terms = []
    for i in range(len(students)):
        for j in range(len(choices)):
            objective_terms.append(ranks[i][j] * variables[i, j] / scale)
    
    return objective_terms

def find_choice(solution, student, choices):
    for i in range(len(choices)):
        if solution[student, i].solution_value() > 0.5:
            return choices[i][0]

def report_status(solver):
    status = solver.Solve()
    if status == pywraplp.Solver.OPTIMAL:
        print('This is an optimal solution')
    elif status == pywraplp.Solver.FEASIBLE:
        print('This is an approximate solution')
    else:
        print('No possible assignment found')
        sys.exit()


def print_solution(students, y4, y5, path, schools, pathways):
    solution = []
    for i in range(len(students)):
        y4_school = find_choice(y4, i, schools)
        print(f'{students[i][0]} assigned to {y4_school} in Year 4')

        y5_school = find_choice(y5, i, schools)
        print(f'{students[i][0]} assigned to {y5_school} in Year 5')

        pathway = find_choice(path, i, pathways)
        print(f'{students[i][0]} assigned to the pathway {pathway}\n')
        
        solution.append(f'{students[i][0]},{y4_school},{y5_school},{pathway}')
    
    with open('assignment.csv', 'w') as file:
        file.write('\n'.join(solution))

def main():
    check_cmd_line_args()

    schools, pathways, students = load_all(sys.argv[1], sys.argv[2], sys.argv[3])

    check_errors(schools, pathways, students)

    cols = [1, len(schools) + 1, 2 * len(schools) + 1, 2 * len(schools) + len(pathways) + 1]
    y4_ranks = calc_ranks(students, cols[0], cols[1], cols[3])
    y5_ranks = calc_ranks(students, cols[1], cols[2], cols[3] + 1)
    path_ranks = calc_ranks(students, cols[2], cols[3], cols[3] + 2)

    solver = pywraplp.Solver.CreateSolver('SCIP')

    y4 = solver_variables(solver, len(students), len(schools))
    y5 = solver_variables(solver, len(students), len(schools))
    path = solver_variables(solver, len(students), len(pathways))

    set_constraints(solver, len(students), schools, pathways, y4, y5, path)

    # adding how the cost is calculated to the solver
    objective_terms = add_obj_terms(schools, students, y4_ranks, y4) + \
                      add_obj_terms(schools, students, y5_ranks, y5, cfg.rural_scaling) + \
                      add_obj_terms(pathways, students, path_ranks, path)

    solver.Minimize(solver.Sum(objective_terms))
    report_status(solver)

    print_solution(students, y4, y5, path, schools, pathways)

if __name__ == '__main__':
    main()