class State:
    def __init__(self):
        self.transitions = None
        # Vars go here

    # Handle Startup
    def start(self, last_state, data):
        pass

    # Evaluate Conditions Here
    def process(self, data):
        pass

    # Transition to next state
    def stop(self, next_state):
        pass


class GState(State):
    def __init__(self):
        super().__init__(self)
        self.entities = None
        # Vars go here


class EState(State):
    def __init__(self):
        super().__init__(self)
