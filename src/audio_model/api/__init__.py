def __init__(self):
    self.events      = deque(maxlen=100)
    self.listening   = False
    self.latest_soil = None