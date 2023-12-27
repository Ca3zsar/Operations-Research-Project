import gurobipy as gp
from gurobipy import GRB

from read_file import read_info


def get_predecessors(index, succesors):
    predecessors = []
    for i in range(len(succesors)):
        if index+1 in succesors[i]:
            predecessors.append(i)
    return predecessors


# Create a new model
model = gp.Model("mip1")

# use a branch and bound algorithm
model.setParam('Method', 2)

n_tasks, resources, durations, res_needed, res_consumption, res_produced, n_successors, successors = read_info('ConsProd_j07.rcp')
predecessors = [get_predecessors(i, successors) for i in range(n_tasks)]
t_max = sum(durations)

s_i = model.addVars(n_tasks, vtype=GRB.CONTINUOUS, name="s_i") # start time of task i
x_i = model.addVars((n_tasks, t_max+1), vtype=GRB.BINARY, name="x_i") # x[i,t] = 1 if task i is executed at time t
f_i = model.addVars((n_tasks, n_tasks, len(resources)), vtype=GRB.CONTINUOUS, name="f_i")
d_i = model.addVars((n_tasks, n_tasks, len(resources)), vtype=GRB.CONTINUOUS, name="d_i")
c_prod_i = model.addVars((n_tasks, len(resources)), vtype=GRB.CONTINUOUS, name="c_prod_i")
c_cons_i = model.addVars((n_tasks, len(resources)), vtype=GRB.CONTINUOUS, name="c_cons_i")

# set objective as min of S_n+1
model.setObjective(s_i[n_tasks], GRB.MINIMIZE)

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
for i in range(n_tasks):
    for j in range(n_tasks):
        for k in range(len(resources)):
            model.addConstr(f_i[i,j,k] <= min(res_needed[i][k], res_needed[j][k])*x_i[i,j])

# (17)
for i in range(n_tasks):
    for k in range(len(resources)):
        model.addConstr(gp.quicksum(f_i[i,j,k] for j in range(n_tasks)) == res_needed[i][k])

# (18)
for i in range(n_tasks):
    for k in range(len(resources)):
        model.addConstr(gp.quicksum(f_i[j,i,k] for j in range(n_tasks)) == res_produced[i][k])

# (19)
for k in range(len(resources)):
    model.addConstr(f_i[n_tasks,0,k] == resources[1][k]) 

# (20)
for i in range(n_tasks):
    for j in range(n_tasks):
        for k in range(len(resources)):
            model.addConstr(f_i[i,j,k] >= 0)

# (21)
model.addConstr(s_i[0] == 0)

# (22)
for i in range(n_tasks):
    ES_i = sum(durations[j] for j in predecessors[i]) + 1 if len(predecessors[i]) > 0 else 0
    LS_i = t_max - sum(durations[j-1] for j in successors[i]) + 1
    model.addConstr(s_i[i] >= ES_i)
    model.addConstr(s_i[i] <= LS_i)

# (24)
for i in range(n_tasks):
    for j in range(n_tasks):
        for p in range(len(resources)):
            model.addConstr(d_i[i,j,p] <= min(res_produced[i][p], res_consumption[j][p])*x_i[i,j])

# (25)
for i in range(n_tasks):
    for p in range(len(resources)):
        model.addConstr(gp.quicksum(d_i[i,j,p] for j in range(n_tasks)) == res_produced[i][p])

# (26)
for i in range(n_tasks):
    for p in range(len(resources)):
        model.addConstr(gp.quicksum(d_i[j,i,p] for j in range(n_tasks)) == res_consumption[i][p])




























