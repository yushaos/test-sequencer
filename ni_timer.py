import time

class NITimer:
    def __init__(self):
        self.start_time = None
        
    def start(self):
        self.start_time = time.time()
        
    def wait_until(self, target_time):
        while time.time() - self.start_time < target_time:
            time.sleep(0.001)
