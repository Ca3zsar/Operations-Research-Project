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
model.setParam('TimeLimit', 500)
model.update()

n_tasks, resources, durations, res_needed, res_consumption, res_produced, n_successors, successors = read_info('RCPSP_CPR\Pack_ConsProd\ConsProd_Pack008.rcp')
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

P = 3

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
        
for i in range(n_tasks):
    ES_i = ES[i]
    LS_i = LS[i]

    for t in range(ES_i, LS_i+1):
        first_sum = gp.quicksum(x[i, tau] for tau in range(t, LS_i))
        
        for j in successors[i]:
            LS_j = LS[j-1]

            second_sum = gp.quicksum(x[j-1, tau] for tau in range(ES_j, min(LS_j, t+durations[i]-1)))

            model.addConstr(first_sum + second_sum <= 1)
        
model.optimize()

temp = model.x
print(len(temp))
print(model.objVal)

# check the gap
print(model.MIPGap)

# check the number of nodes explored
print(model.NodeCount)

# check the time elapsed
print(model.Runtime)