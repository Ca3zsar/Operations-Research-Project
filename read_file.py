
def read_info(file):
    with open(file, 'r') as f:
        first_line = f.readline()
        second_line = f.readline().split()

        n_tasks = int(first_line.split()[0])
        res_not = int(first_line.split()[1])
        res_yes = int(first_line.split()[2])

        res_not_max = [int(i) for i in second_line[:res_not]]
        res_yes_max = [int(i) for i in second_line[res_not:]]

        resources = [res_not_max, res_yes_max]

        durations = {}
        res_needed = []
        res_consumption = []
        res_produced = []

        n_successors = []
        successors = []

        for index, line in enumerate(f):
            line = line.split()
            durations[index] = int(line[0])
            res_needed.append([int(i) for i in line[1:res_not+1]])
            res_consumption.append([int(i) for i in line[res_not+1:res_not+res_yes+1]])
            res_produced.append([int(i) for i in line[res_not+res_yes+1:res_not+2*res_yes+1]])

            n_successors.append(int(line[res_not+2*res_yes+1]))
            successors.append([int(i) for i in line[-n_successors[-1]:]] if n_successors[-1] > 0 else [])

        durations[0] = 0
        durations[n_tasks-1] = 0
        durations[n_tasks] = 0

        res_produced.append([0 for _ in range(res_yes)])
        res_consumption.append([0 for _ in range(res_yes)])

        return n_tasks, resources, durations, res_needed, res_consumption, res_produced, n_successors, successors
