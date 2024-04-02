import os
import json
import jsonlines
import sys
import time
import psycopg2
from dotenv import load_dotenv
from sshtunnel import SSHTunnelForwarder
import redis
import threading
import queue
load_dotenv()

class Data:
    def setup_redis(self):
        if os.environ.get("REDIS_URL"):
            return redis.Redis.from_url(os.environ.get("REDIS_URL"))
        else:
            return None

    def setup_database(self):
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
        self.dbconn = None
        if ssh_host:
            self.tunnel = SSHTunnelForwarder(
                (ssh_settings["ssh_host"], ssh_settings["ssh_port"]),
                ssh_username=ssh_settings["ssh_user"],
                ssh_pkey=ssh_settings["ssh_private_key"],
                remote_bind_address=(db_settings["database_host"], db_settings["database_port"]),
            ) 
            self.tunnel.start()
            # Establish database connection
            self.dbconn = psycopg2.connect(
                user=db_settings["database_username"],
                password=db_settings["database_password"],
                host=db_settings["database_host"],
                port=self.tunnel.local_bind_port,
                database=db_settings["database_name"],
            )
            self.dbcursor = self.dbconn.cursor()
        elif db_settings["database_host"]:
            self.dbconn = psycopg2.connect(
                user=db_settings["database_username"],
                password=db_settings["database_password"],
                host=db_settings["database_host"],
                port=db_settings["database_port"],
            database=db_settings["database_name"],
        )
        if self.dbconn:
            self.log_queue = queue.Queue()
            self.log_thread = threading.Thread(target=self.process_log_queue)
            self.log_thread.daemon = True 
            self.log_thread.start()

    def process_log_queue(self):
        while True:
            obj = self.log_queue.get()
            if obj is None:
                break

            file = f"logs/{obj['sim_id']}.jsonl"
            with jsonlines.open(file, mode='a') as writer:
                writer.write(json.dumps(obj))
            stream = f"{obj['sim_id']}_stream"
            queue = f"{obj['sim_id']}"
            wtf = json.loads(json.dumps(obj, default=str))
            #redis_connection.xadd(stream, wtf)
            max_retries = 3
            retry_delay = 1
            if self.redis_connection:
                for attempt in range(max_retries):
                    try:
                        self.redis_connection.lpush(queue, json.dumps(obj))
                        break  # Break the loop if successful
                    except redis.RedisError as e:
                        print(f"Error pushing to Redis queue. Retrying... ({attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)

            # Write the log entry to the database
            if self.dbconn and obj["step_type"] in ['talk', 'agent_set', 'move', 'matrix_set', 'agent_init']:
                fields_to_skip = ["step", "substep", "step_type", "sim_id", "embedding"]
                data = {k: v for k, v in obj.items() if k not in fields_to_skip}
                try:
                    self.dbcursor.execute(
                        "INSERT INTO timelines (sim_id, step, substep, step_type, data) VALUES (%s, %s, %s, %s, %s)",
                        (obj["sim_id"], obj["step"], obj["substep"], obj["step_type"], json.dumps(data))
                    )
                    self.dbconn.commit()
                except Exception as e:
                    print(f"Error writing to database: {e}")

            self.log_queue.task_done()


    def cleanup_db():
        self.log_queue.put(None)
        self.log_thread.join()
        self.dbconn.close()

    def add_to_logs(self,obj):
        obj["step"] = self.cur_step
        obj["substep"] = self.current_substep
        obj["sim_id"] = self.id # i think we will change this to sim id everywhere


        self.log_queue.put(obj)
        self.current_substep += 1
