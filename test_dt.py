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


# Create a new model
model = gp.Model("mip1")

# use a branch and bound algorithm
model.setParam('Method', 2)

n_tasks, resources, durations, res_needed, res_consumption, res_produced, n_successors, successors = read_info('ConsProd_j07.rcp')
predecessors = [get_predecessors(i, successors) for i in range(1, n_tasks+1)]
t_max = sum(durations)

x = model.addMVar((n_tasks, t_max+1), vtype=GRB.BINARY, name="x") # x[i,t] = 1 if task i is executed at time t
# Set other data
earliest = 0
latest = t_max


# Set objective
model.setObjective(gp.quicksum(t*x[i,t] for i in range(n_tasks) for t in range(earliest, latest+1)), GRB.MINIMIZE)

# indici din fisier -> i - 1
# indici doar din cod -> i

# get all precedences
for i in range(n_tasks):
    pred_i = predecessors[i]
    ES_i = sum(durations[j] for j in predecessors[i]) + 1 if len(predecessors[i]) > 0 else 0
    LS_i = latest - sum(durations[j-1] for j in successors[i]) + 1
    
    for j in successors[i]:
        ES_j = sum(durations[k] for k in predecessors[j-1]) + 1 if len(predecessors[j-1]) > 0 else 0
        LS_j = latest - sum(durations[k-1] for k in successors[j-1]) + 1
    
        sum_left = gp.quicksum(t*x[j-1, t] for t in range(ES_j, LS_j))
        sum_right = gp.quicksum(t*x[i, t] for t in range(ES_i, LS_i)) + durations[i]
        model.addConstr(sum_left >= sum_right)

for t in range(earliest, latest+1):
    for r in range(len(resources[0])):
        for i in range(n_tasks):
            ES_i = sum(durations[j] for j in predecessors[i]) + 1 if len(predecessors[i]) > 0 else 0
            LS_i = latest - sum(durations[j-1] for j in successors[i]) + 1

            inner_sum = 0
            for tau in range(max(ES_i, t-durations[i]+1), min(LS_i, t)):
                inner_sum += x[i, tau]

        sum_left = gp.quicksum(res_needed[i][r]*inner_sum for i in range(n_tasks))
        model.addConstr(sum_left <= resources[0][r])

for i in range(n_tasks):
    ES_i = sum(durations[j] for j in predecessors[i]) + 1 if len(predecessors[i]) > 0 else 0
    LS_i = latest - sum(durations[j-1] for j in successors[i]) + 1

    model.addConstr(gp.quicksum(x[i, t] for t in range(ES_i, LS_i)) == 1)

P = 3
s = [[0 for _ in range(P)] for _ in range(t+1)]

for p in range(P):
    inner_sum = [x[i, 0] * res_consumption[i][p] for i in range(n_tasks)]
    s[0][p] = resources[1][p] - sum(inner_sum)

for t in range(1, latest+1):
    for p in range(P):
        first_sum = [x[i, t-durations[i]] * res_produced[i][p] for i in range(n_tasks)]
        second_lum = [x[i, t] * res_consumption[i][p] for i in range(n_tasks)]
        s[t][p] = s[t-1][p] + sum(first_sum) - sum(second_lum)

for t in range(earliest, latest+1):
    for p in range(P):
        model.addConstr(s[t][p] >= 0)
        
model.optimize()

temp = model.x
print(len(temp))
print(model.objVal)
