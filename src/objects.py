class Object:
    def __init__(self, name, position, is_boundary=False, description='Object', symbol='x'):
        self.name = name
        self.position = position
        self.is_boundary = is_boundary
        self.description = description
        self.symbol = symbol

    def setPosition(self, position):
        self.position = position

    def getPosition(self):
        return self.position

    def __str__(self, verbose=False):
        if verbose:
            return f"Object(name: {self.name}, position: {self.position}, description: {self.description}, is_boundary: {self.is_boundary}, symbol: {self.symbol})"
        else:
            return f"{self.name}"


