import jsonlines
import json
import sys
path = sys.argv[1]
total_steps = 0
max_step = 0
step_types = {}
agent_actions = {}
agents = {}
completed = False
deaths = 0
sim_id = ""
scenario = ""
world = ""
last_death_at_step = 0
last_death_at_row = 0
with jsonlines.open(path, "r") as jsonl_file:
    for i, row in enumerate(jsonl_file):
        obj = json.loads(row)
        max_step = obj.get("step")
        step_type = obj.get("step_type")
        step_types[step_type] = step_types.get(step_type, 0) + 1
        sim_id = obj.get("sim_id")
        if step_type == "agent_init":
            agents[obj["agent_id"]] = {}
            agents[obj["agent_id"]]["name"] = obj["name"]
            agents[obj["agent_id"]]["kind"] = obj["kind"]
        elif step_type == "matrix_set" and obj["status"] == "complete":
            completed = True
        elif "status" in obj and obj["status"] == "dead":
            deaths += 1
            last_death_at_step = max_step
            last_death_at_row = i+1
        elif step_type == "matrix_init":
            sim_id = obj["sim_id"]
            scenario = obj["data"]["scenario"]
            world = obj["data"]["environment"]

        total_steps +=1
human_agents = dict(filter(lambda item: item[1]["kind"] == "human", agents.items()))
print(f"matrix info sim_id: {sim_id}")
print(f"matrix info scenario: {scenario}")
print(f"matrix info world: {world}")
print(f"total individual steps {total_steps}")
print(f"simulation steps {max_step}")
print(f"step types {step_types}")
print(f"average substeps per step {total_steps/max_step}")
print(f"human agent count: {len(human_agents)}")
print(f"deaths: {deaths}")
print(f"last_death_at_step {last_death_at_step}")
print(f"last_death_at_row {last_death_at_row}")
#print(f"human agents {human_agents}")
print(f"total agent count: {len(agents)}")
#print(f"agent actions {agent_actions}")
print(f"completed: {completed}")
