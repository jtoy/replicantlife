import subprocess
import sys
import os
import datetime
import requests
import time
WEBHOOK_URL = "https://discord.com/api/webhooks/1179589082540675113/o8NLAfbISn82hZ9SmGyJ3GAJavIc7OIDS8Qbjl8OoO-jWOBSVLuQ6kgv-_UDju1yWf8M"

def run_and_notify(scenario_config, env, id, file_path, report_path):
    with open(file_path, 'w') as file:
        python_executable = sys.executable
        subprocess.run([python_executable, "engine.py", "--scenario", scenario_config, "--environment", env, "--id", id], stdout=file, env={ 'LLM_ACTION': '1', 'SIMULATION_STEPS': '10' })
    # Check if the simulation output file is not empty
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        # Send the simulation output to Discord
        with open(file_path, 'rb') as file:
            requests.post(WEBHOOK_URL, files={'file': file}, json={'content': f"full debug logs for {id}"})
        print(f"Webhook sent for {file_path}")

    # Check if the report file is not empty
    if os.path.exists(report_path) and os.path.getsize(report_path) > 0:
        # Send the simulation output to Discord
        with open(report_path, 'rb') as file:
            requests.post(WEBHOOK_URL, files={'file': file}, json={'content': f"Report  {id}"})
        print(f"Report Contents sent to Discord for {report_path}")
    else:
        print(f"No webhook sent for {file_path} and {report_path}")

current_date = datetime.datetime.now().strftime("%Y-%m-%d")
logs_path = "logs/"
os.makedirs(logs_path, exist_ok=True)

sims = [
    {"scenario_config": "configs/christmas_party_situation.json", "env": "configs/largev2.tmj", "id": "christmasparty_graph"},
    {"scenario_config": "configs/murder_situation.json", "env": "configs/largev2.tmj", "id": "murder_graph"},
    {"scenario_config": "configs/zombie_situation.json", "env": "configs/largev2.tmj", "id": "zombies_graph"},
    {"scenario_config": "configs/secret_santa_situation.json", "env": "configs/largev2.tmj", "id": "secretsanta_graph"},
]

# Run simulations and notify
for sim in sims:
    file_path = f"{logs_path}{sim['id']}_{current_date}.txt"
    report_path = f"{logs_path}report-{sim['id']}_{current_date}.txt"
    run_and_notify(sim['scenario_config'], sim['env'], f"{sim['id']}_{current_date}",  file_path, report_path)

