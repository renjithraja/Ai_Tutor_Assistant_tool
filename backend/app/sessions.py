from collections import defaultdict
from typing import List, Dict

class SessionStore:
    def __init__(self):
        self.store = defaultdict(list)

    def get_history(self, session_id: str):
        return self.store.get(session_id, [])

    def append(self, session_id: str, message: Dict):
        self.store[session_id].append(message)

    def clear(self, session_id: str):
        self.store[session_id] = []
