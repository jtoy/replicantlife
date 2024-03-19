import os
import json
import jsonlines
import sys
import psycopg2
from dotenv import load_dotenv
from sshtunnel import SSHTunnelForwarder
import redis
import argparse

# Load environment variables from .env file
load_dotenv()

parser = argparse.ArgumentParser(description='Process and insert data.')
parser.add_argument('jsonl_file_path', type=str, help='Path to the JSONL file')
parser.add_argument('--rows', type=int, help='Number of rows to process', default=None)
parser.add_argument('--id', type=str, help='Override sim_id', default=None)
parser.add_argument('--full', action='store_true', help='Process minimal data only')
args = parser.parse_args()


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
override_sim_id = None
printed = False
inserted = 0

def process_and_insert_data(cursor,redis_client, args):
    global printed,inserted
    with jsonlines.open(args.jsonl_file_path, "r") as jsonl_file:
        for i, row in enumerate(jsonl_file):
            if args.rows is None or i < args.rows:
                obj = json.loads(row)
                step = obj.get("step")
                substep = obj.get("substep")
                step_type = obj.get("step_type")
                sim_id = obj.get("sim_id")
                if args.id:
                    sim_id = args.id
                if printed == False:
                    print(f"SIM ID: {sim_id}")
                    if not args.full:
                        print("inserting minimum data for simulation display")
                    printed = True
                if not args.full and step_type not in ['talk', 'agent_set', 'move', 'matrix_set', 'agent_init']:
                    continue
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
                    inserted += 1

                    if i % 500 == 0:
                        print(i)
                except Exception as e:
                    if cursor:
                        conn.rollback()
                        print(f"Error: {e}")
    print(f"cursor: {i}")
    print(f"actual inserted: {inserted}")

cursor = None
if redis_url:
    print("INSERTING INTO REDIS")
    redis_client = redis.StrictRedis.from_url(redis_url, decode_responses=True)
    process_and_insert_data(None,redis_client,args)

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
        process_and_insert_data(cursor,None, args)
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
    process_and_insert_data(cursor, None,args)


if cursor:
    cursor.close()
    conn.close()

