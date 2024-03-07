class Action:
    def __init__(self, name):
        self.name = name

    def execute(self):
        raise NotImplementedError("Subclasses must implement the execute method")

    def example():
        raise NotImplementedError("Subclasses must implement the example method")
