import time
import redis
from django.conf import settings
from rest_framework.throttling import BaseThrottle

# Use a module-level client so it's reused across requests.
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

class TokenBucketThrottle(BaseThrottle):
    """
    Token Bucket Rate Limiting using Redis.
    Allows bursts up to `capacity` requests, refilled at `refill_rate` tokens per second.
    """
    def __init__(self):
        self.capacity = 5  # Maximum burst size
        self.refill_rate = 1.0  # Tokens added per second
        self.retry_after = None

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return f"throttle:token_bucket:{ident}"

    def allow_request(self, request, view):
        key = self.get_cache_key(request, view)
        now = time.time()

        # Lua script for atomic Token Bucket operation
        lua_script = """
        local key = KEYS[1]
        local capacity = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        
        local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
        local tokens = tonumber(bucket[1])
        local last_refill = tonumber(bucket[2])
        
        if tokens == nil then
            tokens = capacity
            last_refill = now
        end
        
        local elapsed = math.max(0, now - last_refill)
        local refill_amount = elapsed * refill_rate
        tokens = math.min(capacity, tokens + refill_amount)
        
        if tokens >= 1 then
            tokens = tokens - 1
            redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
            redis.call('EXPIRE', key, math.ceil(capacity / refill_rate))
            return 1
        else
            redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
            redis.call('EXPIRE', key, math.ceil(capacity / refill_rate))
            return 0
        end
        """
        
        script = redis_client.register_script(lua_script)
        allowed = script(keys=[key], args=[self.capacity, self.refill_rate, now])
        
        if not allowed:
            self.retry_after = 1 / self.refill_rate
            return False
            
        return True

    def wait(self):
        return self.retry_after
