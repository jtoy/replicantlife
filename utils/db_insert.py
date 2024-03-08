"""
This module handles the processing and inserting
of data to the database.
"""

import os
import sys
import json
import jsonlines
import psycopg2

from dotenv import load_dotenv
from sshtunnel import SSHTunnelForwarder

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
    "ssh_private_key": os.environ.get("SSH_PRIVATE_KEY"),
}


def process_and_insert_data(conn_cursor, file_path, rows_process):
    """
    This module processes the data then inserts the data to database.
    """

    with jsonlines.open(file_path, "r") as jsonl_file:
        for i, row in enumerate(jsonl_file):
            if rows_to_process is None or i < rows_process:
                obj = json.loads(row)
                step = obj.get("step")
                substep = obj.get("substep")
                step_type = obj.get("step_type")
                sim_id = obj.get("sim_id")
                data = {
                    k: v
                    for k, v in obj.items()
                    if k not in ["step", "substep", "step_type", "sim_id", "embedding"]
                }

                try:
                    conn_cursor.execute(
                        "INSERT INTO timelines (sim_id,step, substep, step_type, data) "
                        "VALUES (%s,%s, %s, %s, %s)",
                        (sim_id, step, substep, step_type, json.dumps(data)),
                    )

                    conn.commit()
                    if i % 500 == 0:
                        print(i)
                except Exception as e: # pylint: disable=broad-except
                    conn.rollback()
                    print(f"Error: {e}")


jsonl_file_path = sys.argv[
    1
]  # Assumes the first command-line argument is the JSONL file path
rows_to_process = (
    int(sys.argv[2]) if len(sys.argv) > 2 else None
)  # Assumes the second argument is the number of rows to process

if ssh_host:
    with SSHTunnelForwarder(
        (ssh_settings["ssh_host"], ssh_settings["ssh_port"]),
        ssh_username=ssh_settings["ssh_user"],
        ssh_pkey=ssh_settings["ssh_private_key"],
        remote_bind_address=(
            db_settings["database_host"],
            db_settings["database_port"],
        ),
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
        process_and_insert_data(cursor, jsonl_file_path, rows_to_process)
else:
    conn = psycopg2.connect(
        user=db_settings["database_username"],
        password=db_settings["database_password"],
        host=db_settings["database_host"],
        port=db_settings["database_port"],
        database=db_settings["database_name"],
    )

    cursor = conn.cursor()
    process_and_insert_data(cursor, jsonl_file_path, rows_to_process)


cursor.close()
conn.close()
