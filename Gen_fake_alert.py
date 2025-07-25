import redis
import json

r = redis.Redis.from_url("rediss://default:AWTjAAIjcDE0ODhlMDIxZTEwNDg0Y2NmOTM5YTliZWI4ZTE0OGI5ZHAxMA@internal-sawfly-25827.upstash.io:6379",decode_responses=True)
# Open and read the JSON file
with open(r'/mnt/c/Users/Calvi/Downloads/MS181101ab-initial.json', 'r') as file:
    data = json.load(file)
data=json.dumps(data)
print(json.loads(data))
r.rpush("queue:waiting", data)