import redis
import os
from dotenv import load_dotenv

load_dotenv()

redis_client = redis.StrictRedis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    db=int(os.getenv("REDIS_DB")),
    decode_responses=True
)

# Redis 키 만료 이벤트를 수신하기 위해 Pub/Sub 설정
redis_client.config_set("notify-keyspace-events", "Ex")
