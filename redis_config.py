import redis

REDIS_PORT = 6384

# Run redis on main server
# We can also use proper distributed database for better fault tolerance
rds = redis.Redis(port=REDIS_PORT, charset="utf-8", decode_responses=True)
