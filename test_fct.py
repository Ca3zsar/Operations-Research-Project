import gurobipy as gp
from gurobipy import GRB
from time import perf_counter

from read_file import read_info


def get_predecessors(index, succesors):
    predecessors = []
    for i in range(len(succesors)):
        if index in succesors[i]:
            predecessors.append(i)
            predecessors += get_predecessors(i, succesors)

    return set(predecessors)

def solve_instance(path, max_time=330):
    # Create a new model
    start = perf_counter()
    model = gp.Model("mip1")

    # use a branch and bound algorithm
    model.setParam('Method', 2)
    model.setParam('TimeLimit', 300)
    model.update()

    n_tasks, resources, durations, res_needed, res_consumption, res_produced, n_successors, successors = read_info(path)
    predecessors = [get_predecessors(i, successors) for i in range(n_tasks+1)]
    t_max = sum(durations.values())
    latest = t_max

    s_i = model.addMVar(n_tasks, vtype=GRB.CONTINUOUS, name="s_i") # start time of task i
    x_i = model.addMVar((n_tasks, n_tasks), vtype=GRB.BINARY, name="x_i") # x[i,t] = 1 if task i is executed at time t
    f_i = model.addMVar((n_tasks, n_tasks, len(resources[0])), vtype=GRB.CONTINUOUS, name="f_i")
    d_i = model.addMVar((n_tasks+1, n_tasks+1, len(resources[1])), vtype=GRB.CONTINUOUS, name="d_i")

    ES = []
    LS = []

    for p in range(len(resources[1])):
        res_produced[0][p] = resources[1][p]

    for i in range(n_tasks):
        ES_i = sum(durations[j] for j in predecessors[i]) + 1 if len(predecessors[i]) > 0 else 0
        LS_i = latest - sum(durations[j] for j in successors[i]) - durations[i] - 1
        ES.append(ES_i)
        LS.append(LS_i)

    # set objective as min of S_n+1
    model.setObjective(s_i[-1], GRB.MINIMIZE)

    # (13)
    for i in range(n_tasks):
        for j in range(i+1, n_tasks):
            model.addConstr(x_i[i,j] + x_i[j,i] <= 1)

    # (14) 
    for i in range(n_tasks):
        for j in range(n_tasks):
            for k in range(n_tasks):
                model.addConstr(x_i[i,k] >= x_i[i,j] + x_i[j,k] - 1)

    # (15)
    M = 100000
    for i in range(n_tasks):
        for j in range(n_tasks):
            model.addConstr(s_i[j] - s_i[i] >= durations[i]*x_i[i,j] - M*(1 - x_i[i,j]))

    # (16)
    for k in range(len(resources[0])):
        res_needed[0][k] = res_needed[-1][k] = resources[0][k]

    for i in range(n_tasks-1):
        for j in range(1,n_tasks):
            for k in range(len(resources[0])):
                model.addConstr(f_i[i,j,k] <= min(res_needed[i][k], res_needed[j][k])*x_i[i,j])

    # (17)
    for i in range(n_tasks):
        for k in range(len(resources[0])):
            model.addConstr(gp.quicksum(f_i[i,j,k] for j in range(n_tasks)) == res_needed[i][k])

    # (18)
    for i in range(n_tasks):
        for k in range(len(resources[0])):
            model.addConstr(gp.quicksum(f_i[j,i,k] for j in range(n_tasks)) == res_needed[i][k])

    # (19)
    for k in range(len(resources[0])):
        model.addConstr(f_i[-1,0,k] == resources[0][k]) 

    # (20)
    for i in range(n_tasks):
        for j in range(n_tasks):
            for k in range(len(resources[0])):
                model.addConstr(f_i[i,j,k] >= 0)

    # (21)
    model.addConstr(s_i[0] == 0)

    # (22)
    for i in range(1, n_tasks):
        ES_i = ES[i]
        LS_i = LS[i]
        model.addConstr(s_i[i] >= ES_i)
        model.addConstr(s_i[i] <= LS_i)

    # (24)
    for i in range(1, n_tasks - 1):
        for j in range(1, n_tasks - 1):
            for p in range(len(resources[1])):
                model.addConstr(d_i[i,j,p] <= min(res_produced[i][p], res_consumption[j][p])*x_i[i,j])

    # # (25)
    for j in range(1, n_tasks - 1):
        for p in range(len(resources[1])):
            model.addConstr(gp.quicksum(d_i[i,j,p] for i in range(n_tasks - 1)) == res_consumption[j][p])

    # # (26)
    for i in range(n_tasks - 1):
        for p in range(len(resources[1])):
            model.addConstr(gp.quicksum(d_i[i,j,p] for j in range(1, n_tasks)) == res_produced[i][p])

    stop = perf_counter()
    if stop - start > max_time:
        return model.Runtime, None, None, False, None, None, None, None
    
    model.setParam('TimeLimit', max_time - int((stop - start)))

    model.optimize()

    is_feasible = (model.Status != GRB.INFEASIBLE)

    if not is_feasible:
        return model.Runtime, None, None, is_feasible, None, None, None, None

    # set the solution number parameter to select the solution
    nSolutions = model.SolCount
    all_solutions = []
    dev_best = []
    
    if nSolutions == 0:
        return model.Runtime, None, model.NodeCount, is_feasible, model.objVal, None, model.SolCount, None

    for sol in range(nSolutions):
        model.setParam(GRB.Param.SolutionNumber, sol)
        dev_best.append((model.PoolObjVal - model.objVal))
        all_solutions.append(int(model.PoolObjVal))

    average_dev = sum(dev_best)/len(dev_best)
    dev_best = average_dev * 100 / model.ObjVal

    return model.Runtime, model.MIPGap, model.NodeCount, is_feasible, model.objVal, dev_best, model.SolCount, all_solutions

# only for test purposes
if __name__ == "__main__":
    path = "RCPSP_CPR/BL_ConsProd/ConsProd_bl2002.rcp"
    solve_instance(path)