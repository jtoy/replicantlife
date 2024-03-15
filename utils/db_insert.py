import os
import json
import jsonlines
import sys
import psycopg2
from dotenv import load_dotenv
from sshtunnel import SSHTunnelForwarder
import redis

# Load environment variables from .env file
load_dotenv()

# Database settings
db_settings = {
    "database_host": os.environ.get("DB_HOST"),
    "database_port": int(os.environ.get("DB_PORT")),
    "database_name": os.environ.get("DB_NAME"),
    "database_username": os.environ.get("DB_USER"),
    "database_password": os.environ.get("DB_PASSWORD"),
}

# SSH settings
ssh_host = os.environ.get("SSH_HOST")
ssh_settings = {
    "ssh_host": ssh_host,
    "ssh_port": int(os.environ.get("SSH_PORT", 22)),
    "ssh_user": os.environ.get("SSH_USER"),
    "ssh_private_key": os.environ.get("SSH_PRIVATE_KEY")
}
redis_url = os.environ.get("REDIS_URL")
minimal = True #TODO move this to a flag
override_sim_id = None
printed = False

def process_and_insert_data(cursor,redis_client, jsonl_file_path,rows_to_process):
    global printed,minimal
    with jsonlines.open(jsonl_file_path, "r") as jsonl_file:
        for i, row in enumerate(jsonl_file):
            if rows_to_process is None or i < rows_to_process:
                obj = json.loads(row)
                step = obj.get("step")
                substep = obj.get("substep")
                step_type = obj.get("step_type")
                sim_id = obj.get("sim_id")
                if printed == False:
                    print(f"SIM ID: {sim_id}")
                    printed = True
                #if minimal and step_type not in ['talk', 'agent_set', 'move', 'matrix_set', 'agent_init']:
                #    next
                data = {k: v for k, v in obj.items() if k not in ["step", "substep", "step_type","sim_id","embedding"]}

                try:
                    if cursor:
                        cursor.execute(
                            "INSERT INTO timelines (sim_id,step, substep, step_type, data) VALUES (%s,%s, %s, %s, %s)",
                            (sim_id,step, substep, step_type, json.dumps(data)),
                        )
                        conn.commit()
                    elif redis_client:
                        redis_client.rpush(os.getenv('REDIS_QUEUE', sim_id), json.dumps(data))

                    if i % 500 == 0:
                        print(i)
                except Exception as e:
                    if cursor:
                        conn.rollback()
                        print(f"Error: {e}")
    print(i)

jsonl_file_path = sys.argv[1]  # Assumes the first command-line argument is the JSONL file path
rows_to_process = int(sys.argv[2]) if len(sys.argv) > 2 else None  # Assumes the second argument is the number of rows to process
cursor = None
if redis_url:
    print("INSERTING INTO REDIS")
    redis_client = redis.StrictRedis.from_url(redis_url, decode_responses=True)
    process_and_insert_data(None,redis_client, jsonl_file_path,rows_to_process)

elif ssh_host:
    print("INSERTING INTO DB VIA TUNNEL")
    with SSHTunnelForwarder(
        (ssh_settings["ssh_host"], ssh_settings["ssh_port"]),
        ssh_username=ssh_settings["ssh_user"],
        ssh_pkey=ssh_settings["ssh_private_key"],
        remote_bind_address=(db_settings["database_host"], db_settings["database_port"]),
    ) as tunnel:
        # Establish database connection
        conn = psycopg2.connect(
            user=db_settings["database_username"],
            password=db_settings["database_password"],
            host=db_settings["database_host"],
            port=tunnel.local_bind_port,
            database=db_settings["database_name"],
        )
        cursor = conn.cursor()
        process_and_insert_data(cursor,None, jsonl_file_path,rows_to_process)
else:
    print("INSERTING INTO DB")
    conn = psycopg2.connect(
        user=db_settings["database_username"],
        password=db_settings["database_password"],
        host=db_settings["database_host"],
        port=db_settings["database_port"],
        database=db_settings["database_name"],
    )

    cursor = conn.cursor()
    process_and_insert_data(cursor, None,jsonl_file_path,rows_to_process)


if cursor:
    cursor.close()
    conn.close()

