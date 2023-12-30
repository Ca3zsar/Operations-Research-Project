import gurobipy as gp
from gurobipy import GRB

from read_file import read_info


def get_predecessors(index, succesors):
    predecessors = []
    for i in range(len(succesors)):
        if index in succesors[i]:
            predecessors.append(i)
            predecessors += get_predecessors(i, succesors)

    return set(predecessors)

def solve_instance(path):
    # Create a new model
    model = gp.Model("mip1")

    # use a branch and bound algorithm
    model.setParam('Method', 2)
    model.setParam('NodeMethod', 2)
    model.setParam('TimeLimit', 300)
    model.update()

    n_tasks, resources, durations, res_needed, res_consumption, res_produced, n_successors, successors = read_info(path)
    predecessors = [get_predecessors(i, successors) for i in range(n_tasks+1)]
    t_max = sum(durations.values())

    x = model.addMVar((n_tasks, t_max+2), vtype=GRB.BINARY, name="x") # x[i,t] = 1 if task i is executed at time t
    s = model.addMVar((t_max+1, len(resources[1])), vtype=GRB.INTEGER, name="s") # s[i,p] = stock level of resource p after task i
    # Set other data
    earliest = 0
    latest = t_max

    ES = []
    LS = []

    for i in range(n_tasks):
        ES_i = sum(durations[j] for j in predecessors[i]) + 1 if len(predecessors[i]) > 0 else 0
        LS_i = latest - sum(durations[j] for j in successors[i]) - durations[i] - 1
        ES.append(ES_i)
        LS.append(LS_i)

    # Set objective
    model.setObjective(gp.quicksum(t*x[-1, t] for t in range(ES[-1], LS[-1])), GRB.MINIMIZE)

    # indici din fisier -> i - 1
    # indici doar din cod -> i

    # get all precedences
    # (4)
    for i in range(n_tasks):
        ES_i = ES[i]
        LS_i = LS[i]
        
        for j in successors[i]:
            ES_j = ES[j-1]
            LS_j = LS[j-1]
        
            sum_left = gp.quicksum(t*x[j-1, t] for t in range(ES_j, LS_j))
            sum_right = gp.quicksum(t*x[i, t] for t in range(ES_i, LS_i))
            model.addConstr(sum_left >= sum_right  + durations[i])

    # (5)
    for t in range(latest+1):
        for r in range(len(resources[0])):
            left_sum = 0
            for i in range(1, n_tasks):
                ES_i = ES[i]
                LS_i = LS[i]

                inner_sum = 0
                for tau in range(max(ES_i, t-durations[i]+1), min(LS_i, t)):
                    inner_sum += x[i, tau]

                term = res_needed[i][r]*inner_sum
                left_sum += term

            model.addConstr(left_sum <= resources[0][r])
            
    for i in range(n_tasks):
        ES_i = ES[i]
        LS_i = LS[i]

        model.addConstr(gp.quicksum(x[i, t] for t in range(ES[i], LS[i] + 1)) == 1)
        # model.addConstr(gp.quicksum(x[i, t] for t in set(range(ES[i])) | set(range(LS[i] + 1, x.shape[1]-1))) == 0)

    P = len(resources[1])

    for p in range(P):
        inner_sum = [x[i, 0] * res_consumption[i][p] for i in range(1, n_tasks)]
        model.addConstr(s[0, p] == resources[1][p] - sum(inner_sum))

    for t in range(1, latest+1):
        for p in range(P):
            first_sum = [(x[i, t-durations[i]] if t-durations[i] > 0 else 0) * res_produced[i][p] for i in range(1, n_tasks)]
            second_lum = [x[i, t] * res_consumption[i][p] for i in range(1, n_tasks)]
            model.addConstr(s[t, p]== s[t-1, p] + sum(first_sum) - sum(second_lum), name=f"stock_{t}_{p}")

    for t in range(earliest, latest+1):
        for p in range(P):
            model.addConstr(s[t, p] >= 0)
            
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