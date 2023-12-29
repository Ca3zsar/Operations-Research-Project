import test_dt, test_ddt, test_fct, test_ooe, test_ooe_prec

import os
import pandas as pd

# list the directories to be searched for test files
root_dir = 'RCPSP_CPR'

file_number = 0

results = pd.DataFrame(columns=['dataset', 'file', 'model', 'time', 'gap%', 'nodes', 'is_feasible', 'obtimal%', 'dev_best%', 'solution_count'])
formulations = {
    'dt': test_dt.solve_instance,
    'ddt': test_ddt.py.solve_instance,
    'fct': test_fct.py.solve_instance,
    'ooe': test_ooe.py.solve_instance,
    'ooe_prec': test_ooe_prec.py.solve_instance
}

files_number = {}

for dir in os.listdir(root_dir):
    if os.path.isdir(os.path.join(root_dir, dir)):
        files_number[dir] = len(os.listdir(os.path.join(root_dir, dir)))
        for file in os.listdir(os.path.join(root_dir, dir)):
            if file.endswith('.rcp'):
                file_number += 1
                print(f"File {file_number}: {file}")
                for model in formulations.keys():
                    print(f"Model: {model}")
                    try:
                        time, gap, nodes, is_feasible, optimal, dev_best, solution_count = formulations[model](os.path.join(root_dir, dir, file))
                        results = results.append({'dataset': dir, 'file': file, 'model': model, 'time': time, 'gap%': gap, 'nodes': nodes, 'is_feasible': is_feasible, 'obtimal%': optimal, 'dev_best%': dev_best, 'solution_count': solution_count}, ignore_index=True)
                    except:
                        print(f"Error in file {file} with model {model}")
                        results = results.append({'dataset': dir, 'file': file, 'model': model, 'time': None, 'gap%': None, 'nodes': None, 'is_feasible': None, 'obtimal%': None, 'dev_best%': None, 'solution_count': None}, ignore_index=True)
                        continue
        print("---------")



results.to_csv('results.csv', index=False)