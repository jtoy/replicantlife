import threading
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import time
from engine import Matrix

steps = 5
variation = { "steps": steps, "allow_plan": 1, "allow_reflect": 1, "allow_observance": 1, "allow_meta": 1, "llm_action": 1, "llm_importance": 0 }
scenario = "configs/christmas_party_situation.json"
id = "test_concurrency"
time_scores = []

# Run Single Thread 3 times and grab scores
for i in range(3):
    params = { **variation, "scenario": scenario, "id": id }
    matrix = Matrix(params)

    start_time = time.time()
    for step in range(steps):
        for a in matrix.agents:
            matrix.llm_action(a, matrix.unix_time)

        matrix.unix_time += 10

    end_time = time.time()

    time_scores.append(end_time - start_time)

# Run 3 Threads 3 times and grab scores
for i in range(3):
    params = { **variation, "scenario": scenario, "id": id, "max_workers": 3 }
    matrix = Matrix(params)

    start_time = time.time()
    for step in range(steps):
        with concurrent.futures.ThreadPoolExecutor(max_workers=matrix.max_workers) as executor:
            futures = [executor.submit(matrix.llm_action, agent, matrix.unix_time) for agent in matrix.agents]
            updated_agents = [future.result() for future in futures]

        matrix.unix_time += 10

    end_time = time.time()

    time_scores.append(end_time - start_time)

# Run 5 Threads 3 times and grab scores
for i in range(3):
    params = { **variation, "scenario": scenario, "id": id, "max_workers": 5 }
    matrix = Matrix(params)

    start_time = time.time()
    for step in range(steps):
        with concurrent.futures.ThreadPoolExecutor(max_workers=matrix.max_workers) as executor:
            futures = [executor.submit(matrix.llm_action, agent, matrix.unix_time) for agent in matrix.agents]
            updated_agents = [future.result() for future in futures]

        matrix.unix_time += 10

    end_time = time.time()

    time_scores.append(end_time - start_time)

print(time_scores)
