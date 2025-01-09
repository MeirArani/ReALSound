class FSM:
    def __init__(self):
        self.states = []
        self.current_state = None

    def start(self):
        pass

    def process(self, state, data):
        state.process(data)

    def transition(self, state):
        self.current_state = state

    def stop(self):
        pass
