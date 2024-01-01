import test_dt, test_ddt, test_fct, test_ooe, test_ooe_prec

import os
import pandas as pd
import random
import time as tm

import multiprocessing as mp

# list the directories to be searched for test files
root_dir = 'RCPSP_CPR'

file_number = 0

results = pd.DataFrame(columns=['dataset', 'file', 'model', 'time', 'gap%', 'nodes', 'is_feasible', 'obtimal%', 'dev_best%', 'solution_count', 'all_solutions'])
formulations = {
    # 'dt': test_dt.solve_instance,
    'ddt': test_ddt.solve_instance,
    # 'fct': test_fct.solve_instance,
    # 'ooe': test_ooe.solve_instance,
    # 'ooe_prec': test_ooe_prec.solve_instance
}

files_number = {}
percentage_of_files_to_be_processed = 0.6
current_date_time = tm.strftime("%Y%m%d-%H%M%S")

for dir in os.listdir(root_dir):
    if os.path.isdir(os.path.join(root_dir, dir)):
        if dir == 'Pack_d_ConsProd' or dir == 'KSD15_d_ConsProd' or dir == 'BL_ConsProd' or dir == 'Pack_ConsProd':
            continue

        files_number[dir] = len(os.listdir(os.path.join(root_dir, dir)))
        files_considered = int(percentage_of_files_to_be_processed * files_number[dir])
        random.seed(83)
        selected_files = random.sample(os.listdir(os.path.join(root_dir, dir)), files_considered)
        
        MAX_TIME = 330

        for file in selected_files:
            if file.endswith('.rcp'):
                file_number += 1
                print(f"File {file_number}: {file}")
                for model in formulations.keys():
                    print(f"Model: {model}")
                    if (dir == 'Pack_d_ConsProd' and (model in ['dt', 'ddt'])):
                        print(f"Model {model} not applicable to dataset {dir}")
                        continue

                    # check that the call lasts at most 300 seconds, otherwise skip the file
                    with mp.Pool(processes=1) as pool:
                        async_result = pool.apply_async(formulations[model], (os.path.join(root_dir, dir, file), ))
                        try:
                            time, gap, nodes, is_feasible, optimal, dev_best, solution_count, all_solutions = async_result.get(MAX_TIME)
                            results = pd.concat([results, pd.DataFrame({'dataset': dir, 'file': file, 'model': model, 'time': time, 'gap%': gap, 'nodes': nodes, 'is_feasible': is_feasible, 'obtimal%': optimal, 'dev_best%': dev_best, 'solution_count': solution_count, 'all_solutions': [str(all_solutions)]})], ignore_index=True)
                            
                        except mp.context.TimeoutError:
                            results = pd.concat([results, pd.DataFrame({'dataset': dir, 'file': file, 'model': model, 'time': MAX_TIME, 'gap%': None, 'nodes': None, 'is_feasible': True, 'obtimal%': None, 'dev_best%': None, 'solution_count': 0, 'all_solutions': [str(None)]})], ignore_index=True)
                            print(f"Timeout of {MAX_TIME} seconds reached for file {file} and model {model}")
                        


                    results.to_csv(f"results_{current_date_time}.csv")
        print("---------")
