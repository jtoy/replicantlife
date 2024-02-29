import json
import redis
import sys
import os

def inject_jsonl_to_redis_queue(file_path, queue_name, max_steps=None):
    # Connect to Redis
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    redis_client = redis.StrictRedis.from_url(redis_url, decode_responses=True)

    # Read JSONL file
    with open(file_path, 'r') as jsonl_file:
        for step, line in enumerate(jsonl_file, start=1):
            if max_steps is not None and step > max_steps:
                break

            try:
                # Parse JSON from each line
                data = json.loads(line.strip())

                # Push data into the Redis queue
                redis_client.rpush(queue_name, json.dumps(data))
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                continue

    print(f"Data from {file_path} injected into Redis queue {queue_name} ({step} lines)")

if __name__ == "__main__":
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python script.py <jsonl_file_path> <redis_queue_name> [max_steps]")
        sys.exit(1)

    jsonl_file_path = sys.argv[1]
    redis_queue_name = sys.argv[2]
    max_steps = int(sys.argv[3]) if len(sys.argv) == 4 else None if len(sys.argv) == 3 else None

    inject_jsonl_to_redis_queue(jsonl_file_path, redis_queue_name, max_steps)

