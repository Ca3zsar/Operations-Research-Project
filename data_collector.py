import test_dt, test_ddt, test_fct, test_ooe, test_ooe_prec

import os
import pandas as pd
import random

# list the directories to be searched for test files
root_dir = 'RCPSP_CPR'

file_number = 0

results = pd.DataFrame(columns=['dataset', 'file', 'model', 'time', 'gap%', 'nodes', 'is_feasible', 'obtimal%', 'dev_best%', 'solution_count', 'all_solutions'])
formulations = {
    'dt': test_dt.solve_instance,
    'ddt': test_ddt.solve_instance,
    'fct': test_fct.solve_instance,
    'ooe': test_ooe.solve_instance,
    'ooe_prec': test_ooe_prec.solve_instance
}

files_number = {}
percentage_of_files_to_be_processed = 0.5

for dir in os.listdir(root_dir):
    if os.path.isdir(os.path.join(root_dir, dir)):
        files_number[dir] = len(os.listdir(os.path.join(root_dir, dir)))
        files_considered = int(percentage_of_files_to_be_processed * files_number[dir])
        selected_files = random.sample(os.listdir(os.path.join(root_dir, dir)), files_considered)
        for file in selected_files:
            if file.endswith('.rcp'):
                file_number += 1
                print(f"File {file_number}: {file}")
                for model in formulations.keys():
                    print(f"Model: {model}")
                    if (dir == 'Pack_d_ConsProd' and (model in ['dt', 'ddt'])):
                        print(f"Model {model} not applicable to dataset {dir}")
                        continue
                    try:
                        time, gap, nodes, is_feasible, optimal, dev_best, solution_count, all_solutions = formulations[model](os.path.join(root_dir, dir, file))
                        results = results.append({'dataset': dir, 'file': file, 'model': model, 'time': time, 'gap%': gap, 'nodes': nodes, 'is_feasible': is_feasible, 'obtimal%': optimal, 'dev_best%': dev_best, 'solution_count': solution_count, 'all_solutions': all_solutions}, ignore_index=True)
                    except:
                        print(f"Error in file {file} with model {model}")
                        results = results.append({'dataset': dir, 'file': file, 'model': model, 'time': None, 'gap%': None, 'nodes': None, 'is_feasible': None, 'obtimal%': None, 'dev_best%': None, 'solution_count': None, 'all_solutions': None}, ignore_index=True)
                        continue
        print("---------")



results.to_csv('results.csv', index=False)