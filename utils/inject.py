import os
import json
import argparse
import redis

parser = argparse.ArgumentParser(description='inject thoughts into simulation')
parser.add_argument('--id', required=True, help='id of simulation')
parser.add_argument('--name', required=True, help='name of the agent')
parser.add_argument('--msg', required=True, help='thought for the agent')
args = parser.parse_args()

redis_url = os.getenv("REDIS_URL")
redis_client = redis.StrictRedis.from_url(redis_url, decode_responses=True)
package = {"name": args.name, "msg": args.msg}
redis_client.rpush(f"{args.id}:communications",json.dumps(package))

