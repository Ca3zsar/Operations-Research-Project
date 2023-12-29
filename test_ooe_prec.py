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
    model.setParam('TimeLimit', 300)
    model.update()

    n_tasks, resources, durations, res_needed, res_consumption, res_produced, n_successors, successors = read_info(path)
    predecessors = [get_predecessors(i, successors) for i in range(n_tasks+1)]

    A = set([i for i in range(1, n_tasks)])
    EV = set([i for i in range(1, n_tasks)])

    # z_i,e = 1 if task i is executed at event e
    z_i = model.addMVar((n_tasks , n_tasks), vtype=GRB.BINARY, name="z_i")
    # t_e = date of event e
    t_e = model.addMVar(n_tasks, vtype=GRB.INTEGER, name="t_e")
    # C_max = makespan
    C_max = model.addVar(vtype=GRB.INTEGER, name="C_max")

    # s_e,p : stock level of resource p after event e
    s_e = model.addMVar((n_tasks, len(resources[1])), vtype=GRB.INTEGER, name="s_e")
    # u_i,e,p : amount of resource p consumed by activity i at event e
    u_i = model.addMVar((n_tasks, n_tasks, len(resources[1])), vtype=GRB.INTEGER, name="u_i")
    # v_i,e,p : amount of resource p produced by activity i at event e
    v_i = model.addMVar((n_tasks, n_tasks, len(resources[1])), vtype=GRB.INTEGER, name="v_i")

    t_max = sum(durations.values())

    # set objective as min of C_max
    model.setObjective(C_max, GRB.MINIMIZE)

    # (28) 
    model.addConstrs(gp.quicksum(z_i[i,e] for e in EV) >= 1 for i in A)

    # (29)
    for i in A:
        model.addConstrs(C_max >= t_e[event] + (z_i[i,event] - z_i[i,event-1])*durations[i-1] for event in EV)

    # (30)
    model.addConstr(t_e[0] == 0)

    # (31)
    for event in EV - {n_tasks-1}:
        model.addConstr(t_e[event+1] >= t_e[event])

    # (32)
    for i in A:
        for event in EV | {0}:
            EV_prime = {e for e in EV if e > event}
            for f in  EV_prime:
                model.addConstr(t_e[f] >= t_e[event] + ((z_i[i,event] - z_i[i,event-1]) - (z_i[i,f] - z_i[i,f-1]) - 1) * durations[i])

    # (33)
    for i in A:
        for event in EV:
            EV_prime = {e for e in EV if e < event}
            model.addConstr(gp.quicksum(z_i[i,e] for e in EV_prime) <= event*(1 - z_i[i,event] + z_i[i,event-1]))

    # (34)
    for i in A:
        for event in EV:
            EV_prime = {e for e in EV if e >= event}
            model.addConstr(gp.quicksum(z_i[i,e] for e in EV_prime) <= (n_tasks-event)*(1 + (z_i[i,event] - z_i[i,event-1])))

    # (35)
    for i in A | {n_tasks-1}:
        pred = predecessors[i]
        for j in pred:
            for event in EV | {0}:
                EV_prime = {e for e in EV if e <= event} | {0}
                model.addConstr(gp.quicksum(z_i[i,e_prime] for e_prime in EV_prime) <= (event+1)*(1 - z_i[j,event]))

    # (36)
    for event in EV:
        for k in range(len(resources[0])):
            model.addConstrs(res_needed[i][k] * z_i[i,event] <= resources[0][k] for i in range(n_tasks-1))

    # (37)
    for i in A:
        for event in EV | {0}:
            for p in range(len(resources[1])):
                model.addConstr(v_i[i,event,p] >= 0)

    # (38)
    for i in A:
        for event in EV | {0}:
            for p in range(len(resources[1])):
                model.addConstr(v_i[i,event,p] >= res_produced[i][p]*(z_i[i,event-1] - z_i[i,event]))

    # (39)
    for i in A:
        for event in EV | {0}:
            for p in range(len(resources[1])):
                model.addConstr(v_i[i,event,p] <= res_produced[i][p]*z_i[i, event-1])

    # (40)
    for i in A:
        for event in EV | {0}:
            for p in range(len(resources[1])):
                model.addConstr(v_i[i,event,p] <= res_produced[i][p]*(1-z_i[i, event]))

    # (41)
    for i in A:
        for event in EV | {0}:
            for p in range(len(resources)):
                model.addConstr(u_i[i,event,p] >= 0)

    # (42)
    for i in A:
        for event in EV | {0}:
            for p in range(len(resources[1])):
                model.addConstr(u_i[i,event,p] >= res_consumption[i][p]*(z_i[i,event] - z_i[i,event-1]))

    # (43)
    for i in A:
        for event in EV | {0}:
            for p in range(len(resources[1])):
                model.addConstr(u_i[i,event,p] <= res_consumption[i][p]*z_i[i, event])

    # (44)
    for i in A:
        for event in EV | {0}:
            for p in range(len(resources[1])):
                model.addConstr(u_i[i,event,p] <= res_consumption[i][p]*(1-z_i[i, event-1]))

    # (45)
    for event in EV:
        for p in range(len(resources[1])):
            model.addConstr(s_e[event,p] == s_e[event-1,p] + gp.quicksum(v_i[i,event,p] for i in range(1, n_tasks - 1)) - gp.quicksum(u_i[i,event,p] for i in range(1, n_tasks)))

    # (46)
    for p in range(len(resources[1])):
        model.addConstr(s_e[0,p] == (resources[1][p] - gp.quicksum(u_i[i,0,p] for i in range(1, n_tasks - 1))), name=f'cons_{p}')

    # (47)
    for event in EV | {0}:
        for p in range(len(resources[1])):
            model.addConstr(s_e[event,p] >= 0)

    # (48)
    for i in range(n_tasks):
        no_predecessors = len(get_predecessors(i, successors))
        no_successors = len(successors[i])
        indices = set(range(no_predecessors)) | set(range(n_tasks - no_successors + 1, n_tasks))
        for event in indices:
            model.addConstr(z_i[i,event] == 0)

    model.optimize()

    is_feasible = (model.Status != GRB.INFEASIBLE)

    if not is_feasible:
        return model.Runtime, None, None, is_feasible, None, None, None, None
    
    # set the solution number parameter to select the solution
    nSolutions = model.SolCount
    all_solutions = []
    dev_best = []
    
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