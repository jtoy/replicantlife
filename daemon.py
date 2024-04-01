import os
import redis
import json
import requests
from dotenv import load_dotenv
from engine import Matrix

load_dotenv()

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
QUEUE_NAME = os.getenv('QUEUE_NAME', 'simulation_jobs')
DISCORD_URL = os.getenv('DISCORD_URL')

# Connect to Redis
redis_conn = redis.from_url(REDIS_URL)

def notify_discord(msg):
    if DISCORD_URL:
        requests.post(DISCORD_URL,json={'content':msg})

# get this out of here or refactor with engine
def update_from_env(config):
    for key, value in config.items():
        env_var = os.getenv(key)
        if env_var is not None:
            # Update the value from the environment variable
            config[key] = type(value)(env_var) if value is not None else env_var
    return config

def load_config():
    filename = "configs/defaults.json"
    with open(filename, 'r') as file:
        config = json.load(file)
    config = update_from_env(config)
    return config

def process_simulation(data):
    config = load_config()
    config['scenario'] = data
    config['environment'] = "configs/largev2.tmj"
    notify_discord(f"starting simulation: #{config}")
    matrix = Matrix(config)
    matrix.boot()
    matrix.run_singlethread()
    notify_discord(f"finished simulation: #{config}")


    print(f'Simulation {simulation_id} completed.')

def main():
    print('Starting simulation job daemon...')
    while True:
        # Fetch a job from the Redis queue
        _, job = redis_conn.blpop(QUEUE_NAME)
        job_data = json.loads(job)

        # Process the simulation
        try:
            process_simulation(job_data)
        except Exception as e:
            print(f'Error processing simulation: {e}')

if __name__ == '__main__':
    main()

