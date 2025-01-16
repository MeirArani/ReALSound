class FSM:
    def __init__(self, start):
        self.current_state = start

    def process(self, data):
        self.current_state = self.current_state.process(data)

    def stop(self):
        pass


class State:
    def __init__(self):
        self.transitions = None
        # Vars go here

    # Handle Startup
    def start(self, data):
        pass

    # Evaluate Conditions Here
    def process(self, data):
        pass

    # Transition to next state
    def stop(self):
        pass
