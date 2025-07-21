import time
import threading

class TokenLimiter:
    def __init__(self, tokens, cooldown_seconds=60):
        self.tokens = list(tokens)
        self.cooldown = cooldown_seconds
        self.blocked = {}  # token: timestamp_until
        self.lock = threading.Lock()

    def get_token(self):
        now = time.time()
        with self.lock:
            for _ in range(len(self.tokens)):
                token = self.tokens.pop(0)
                if token not in self.blocked or self.blocked[token] < now:
                    self.tokens.append(token)
                    return token
                self.tokens.append(token)
        return None  # Все токены на cooldown

    def block_token(self, token):
        with self.lock:
            self.blocked[token] = time.time() + self.cooldown

    def unblock_expired(self):
        now = time.time()
        with self.lock:
            expired = [t for t, until in self.blocked.items() if until < now]
            for t in expired:
                del self.blocked[t] 