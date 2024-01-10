class Location:
    def __init__(self, name, description, areas):
        self.name = name
        self.description = description
        self.areas = areas

    def getAreas(self):
        return self.areas

    def getLocationTree(self):
        area_tree = []
        for area in self.areas:
            area_tree.append(area.getAreaTree())

        tree = {"name": self.name, "description": self.description, "areas": area_tree }
        return tree

    def __str__(self, verbose=False):
        if verbose:
            return f"Location(name: {self.name}, description: {self.description})"
        else:
            return f"{self.name}"

class Area:
    def __init__(self, name, x, y, description, objects):
        self.name = name
        self.x = x
        self.y = y
        self.description = description
        self.objects = objects

    def getObjects(self):
        return self.objects

    def getAreaTree(self):
        object_tree = []
        for object in self.objects:
            object_tree.append(object.getObjectTree())

        tree = {"name": self.name, "x": self.x, "y": self.y, "description": self.description, "objects": object_tree }
        return tree

    def __str__(self, verbose=False):
        if verbose:
            return f"Area(name: {self.name}, x: {self.x}, y: {self.y}, description: {self.description})"
        else:
            return f"{self.name}"

class Object:
    def __init__(self, name, x, y, is_boundary=False, description='Object', symbol='x'):
        self.name = name
        self.x = x
        self.y = y
        self.is_boundary = is_boundary
        self.description = description
        self.symbol = symbol

    def getObjectTree(self):
        tree = {"name": self.name, "x": self.x, "y": self.y, "is_boundary": False, "description": self.description, "symbol": self.symbol }
        return tree

    def __str__(self, verbose=False):
        if verbose:
            return f"Object(name: {self.name}, position: {self.position}, description: {self.description}, is_boundary: {self.is_boundary}, symbol: {self.symbol})"
        else:
            return f"{self.name}"

