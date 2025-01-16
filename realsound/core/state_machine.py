class FSM:
    def __init__(self, start):
        self.current_state = start

    def process(self, data):
        self.current_state = self.current_state.process(data)

    def stop(self):
        pass
