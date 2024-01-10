import subprocess
import sys
import os
import datetime
import requests
import time
WEBHOOK_URL = "https://discord.com/api/webhooks/1179589082540675113/o8NLAfbISn82hZ9SmGyJ3GAJavIc7OIDS8Qbjl8OoO-jWOBSVLuQ6kgv-_UDju1yWf8M"
def last_commit_within_last_24_hours():
    current_dir = os.getcwd()
    git_dir = os.path.join(current_dir, '.git')

    # Check if .git directory exists in the current directory or the parent directory
    while not os.path.exists(git_dir):
        parent_dir = os.path.dirname(current_dir)

        # Check if we have reached the root directory
        if parent_dir == current_dir:
            return False

        current_dir = parent_dir
        git_dir = os.path.join(current_dir, '.git')

    # Get the last modification time of the .git directory
    last_modified_time = os.path.getmtime(git_dir)

    # Get the current time
    current_time = time.time()

    # Calculate the time difference in seconds
    time_difference = current_time - last_modified_time

    # Check if the last commit was within the last 24 hours (86400 seconds)
    return time_difference < 86400

if not last_commit_within_last_24_hours():
    msg = "No changes in the last 24 hours"
    print(msg)
    requests.post(WEBHOOK_URL, json={'content': msg})
    exit()


def run_and_notify(scenario_config, env, id, file_path, report_path):
    with open(file_path, 'w') as file:
        python_executable = sys.executable
        subprocess.run([python_executable, "engine.py", "--scenario", scenario_config, "--environment", env, "--id", id], stdout=file, env={ 'LLM_ACTION': '1' })
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

# Test.py
test_results_path = f"{logs_path}Test_Result.txt"
result = subprocess.run(["python", "test.py"])

# Access test results
errors = len(result.stderr.splitlines()) if result.stderr else 0
failures = len(result.stdout.splitlines()) if result.stdout else 0

# Check if the tests failed
if result.returncode != 0:
    with open(test_results_path, 'w') as test_results_file:
        test_results_file.write(result.stderr + '\n' + result.stdout)
    # Send the test results file to Discord
    with open(test_results_path, 'rb') as test_results_file:
        requests.post(WEBHOOK_URL, files={'file': test_results_file}, json={'content': f"Unit Test Result: Failed"})
    print(f"Webhook sent for test results")
else:
    print("Tests passed. No test results file created.")

sims = [
    {"scenario_config": "configs/spyfall_situation.json", "env": "configs/largev2.tmj", "id": "spyfall"},
    {"scenario_config": "configs/christmas_party_situation.json", "env": "configs/largev2.tmj", "id": "christmasparty"},
    {"scenario_config": "configs/murder_situation.json", "env": "configs/largev2.tmj", "id": "murder"},
    {"scenario_config": "configs/zombie_situation.json", "env": "configs/largev2.tmj", "id": "zombies"},
    {"scenario_config": "configs/secret_santa_situation.json", "env": "configs/largev2.tmj", "id": "secretsanta"},
    {"scenario_config": "configs/truman_show_situation.json", "env": "configs/largev2.tmj", "id": "trumanshow"}
]

# Run simulations and notify
for sim in sims:
    file_path = f"{logs_path}{sim['id']}_{current_date}.txt"
    report_path = f"{logs_path}report-{sim['id']}_{current_date}.txt"
    run_and_notify(sim['scenario_config'], sim['env'], f"{sim['id']}_{current_date}",  file_path, report_path)

# Remove files older than 14 days
for file in os.listdir(logs_path):
    if file.endswith('.txt') and os.path.getmtime(os.path.join(logs_path, file)) < (datetime.datetime.now() - datetime.timedelta(days=14)).timestamp():
        os.remove(os.path.join(logs_path, file))

