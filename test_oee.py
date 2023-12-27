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

# z_i,e = 1 if task i is executed at event e
z_i = model.addVars((n_tasks, n_tasks), vtype=GRB.BINARY, name="z_i")
# t_e = date of event e
t_e = model.addVars(n_tasks, vtype=GRB.INTEGER, name="t_e")
# C_max = makespan
C_max = model.addVar(vtype=GRB.INTEGER, name="C_max")
# set objective as min of C_max
model.setObjective(C_max, GRB.MINIMIZE)
# s_e,p : stock level of resource p after event e
s_e = model.addVars((n_tasks, len(resources)), vtype=GRB.INTEGER, name="s_e")
# u_i,e,p : amount of resource p consumed by activity i at event e
u_i = model.addVars((n_tasks, n_tasks, len(resources)), vtype=GRB.INTEGER, name="u_i")
# v_i,e,p : amount of resource p produced by activity i at event e
v_i = model.addVars((n_tasks, n_tasks, len(resources)), vtype=GRB.INTEGER, name="v_i")
c_prod_i = model.addVars((n_tasks, len(resources)), vtype=GRB.CONTINUOUS, name="c_prod_i")
c_cons_i = model.addVars((n_tasks, len(resources)), vtype=GRB.CONTINUOUS, name="c_cons_i")


# (28) 
for i in range(n_tasks):
    model.addConstr(gp.quicksum(z_i[i,e] for e in range(n_tasks)) >= 1)

# (29)
for i in range(n_tasks):
    for event in range(n_tasks):
        model.addConstr(C_max >= t_e[event] + (z_i[i,event] - z_i[i,event-1])*durations[i])

# (30)
model.addConstr(t_e[0] == 0)

# (31)
for event in range(1, n_tasks):
    model.addConstr(t_e[event] >= t_e[event-1])

# (32)
for i in range(n_tasks):
    for event in range(n_tasks):
        for f in range(event+1, n_tasks):
            model.addConstr(t_e[event] + (z_i[i,event] - z_i[i,event-1]) - (z_i[i,f] - z_i[i,f-1]) <= t_e[f])

# (33)
for i in range(n_tasks):
    for event in range(1, n_tasks):
        model.addConstr(gp.quicksum(z_i[i,e] for e in range(event)) <= event*(1 - z_i[i,event] - z_i[i,event-1]))

# (34)
for i in range(n_tasks):
    for event in range(1, n_tasks):
        model.addConstr(gp.quicksum(z_i[i,e] for e in range(event+1, n_tasks)) <= (n_tasks-event)*(1 + (z_i[i,event] - z_i[i,event-1])))

# (35)
for i in range(n_tasks):
    for event in range(n_tasks):
        for j in successors[i]:
            model.addConstr(gp.quicksum(z_i[j,e_prime] for e_prime in range(event+1)) <= (event+1)*(1 - z_i[i,event]))

# (37)
for i in range(n_tasks):
    for event in range(n_tasks):
        for p in range(len(resources)):
            model.addConstr(v_i[i,event,p] >= 0)

# (38)
for i in range(n_tasks):
    for event in range(n_tasks):
        for p in range(len(resources)):
            model.addConstr(v_i[i,event,p] >= c_prod_i[i,p]*(z_i[i,event-1] - z_i[i,event]))

# (41)
for i in range(n_tasks):
    for event in range(n_tasks):
        for p in range(len(resources)):
            model.addConstr(u_i[i,event,p] >= 0)

# (47)
for event in range(n_tasks):
    for p in range(len(resources)):
        model.addConstr(s_e[event,p] >= 0)














