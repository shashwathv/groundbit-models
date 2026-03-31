from collections import deque
from ..models.schemas import DetectionEvent

class ResultStore:
    def __init__(self):
        self.events = deque(maxlen=100)
        self.listening = False
    
    def add_event(self, event: DetectionEvent):
        self.events.appendleft(event)
    
    def get_latest(self):
        try:
            return self.events[0]
        except IndexError:
            return None
        
    def get_history(self):
        return list(self.events), len(self.events)
        
    def set_listening(self, value:bool):
        self.listening = value