from utils.utils import *

class Environment:
    def __init__(self, environment_data={}):
        map_file_path = environment_data.get("filename", "configs/largev2.tmj")
        self.name = os.path.splitext(os.path.basename(map_file_path))[0]
        # Set Defaults temporarily
        self.width = 150
        self.height = 150
        self.collisions =[]
        self.locations = []

        self.parse_from_file(map_file_path)

    def parse_from_file(self, filename):
        with open(filename, 'r') as file:
            data = json.load(file)

        self.width = data.get("width", 150)
        self.height = data.get("height", 150)

        layers = data.get("layers", [])

        locations = []
        for loc_layer in layers:
            if loc_layer["name"].startswith("*"):
                # Trash Layer
                continue

            if loc_layer["name"] == "Collisions":
                self.collisions = self.process_bounds(loc_layer["data"])

            if loc_layer["type"] == "group":
                location_name = loc_layer["name"]
                location_areas = []

                for area_layer in loc_layer["layers"]:
                    if area_layer["type"] == "group":
                        area_name = area_layer["name"]
                        area_objects = []

                        for obj_layer in area_layer["layers"]:
                            if obj_layer["name"] == "Bounds":
                                area_bounds = obj_layer["data"]

                            elif obj_layer["name"].startswith("*"):
                                # Trash Layer
                                continue

                            else:
                                new_obj = Object({ "name": obj_layer["name"], "bounds": self.process_bounds(obj_layer["data"]) })
                                area_objects.append(new_obj)


                        new_area = Area({ "name": area_name, "bounds": self.process_bounds(area_bounds) })
                        new_area.objects = area_objects
                        for obj in area_objects:
                            obj.area = new_area

                        location_areas.append(new_area)

                    elif area_layer["name"] == "Bounds":
                        location_bounds = area_layer["data"]

                new_loc = Location({ "name": location_name, "bounds": self.process_bounds(location_bounds) })
                new_loc.areas = location_areas

                for area in location_areas:
                    area.location = new_loc

                locations.append(new_loc)

        self.locations = locations

        for loc in locations:
            self.set_valid_coordinates(loc)
            for area in loc.areas:
                self.set_valid_coordinates(area)
                for obj in area.objects:
                    self.set_valid_coordinates(obj)

    def set_valid_coordinates(self, item):
        for x in range(self.height):
            for y in range(self.width):
                if self.collisions[x][y] == 0 and item.bounds[x][y] == 1:
                    item.valid_coordinates.append((x, y))

    def process_bounds(self, array_bounds):
        processed_bounds = []
        for x in range(self.height):
            current_row = []
            for y in range(self.width):
                index = (x * self.width) + y
                value = array_bounds[index]
                if value == 0:
                    current_row.append(0)
                else:
                    current_row.append(1)

            processed_bounds.append(current_row)

        return processed_bounds

    def get_location_from_coordinates(self, x, y):
        for location in self.locations:
            if location.bounds[x][y] != 0:
                return location

    def get_location_from_coordinates(self, x, y):
        for location in self.locations:
            if location.bounds[x][y] != 0:
                return location

        return None

    def get_area_from_coordinates(self, x, y):
        location = self.get_location_from_coordinates(x, y)
        if location is None:
            return None

        for area in location.areas:
            if area.bounds[x][y] != 0:
                return area

        return None

    def get_objects_from_coordinates(self, x, y, include_walls=False):
        area = self.get_area_from_coordinates(x, y)
        objs = []
        if area is None:
            return objs

        for obj in area.objects:
            if obj.bounds[x][y] != 0:
                if not include_walls and obj.name == "Wall":
                    continue
                objs.append(obj)

        return objs

    def get_valid_coordinates(self):
        valid_coordinates = []
        for x in range(self.height):
            for y in range(self.width):
                if self.collisions[x][y] == 0:
                    valid_coordinates.append((x, y))

        return valid_coordinates

    def get_tree(self):
        return (
            {
                "name": self.name,
                "collisions": self.collisions,
                "width": self.width,
                "height": self.height,
                "locations": [location.get_tree() for location in self.locations]
            }
        )

class Location:
    def __init__(self, location_data={}):
        self.name = location_data.get("name", "Location")
        self.bounds = location_data.get("bounds", [])
        self.valid_coordinates = []
        self.areas = []

    def get_tree(self):
        return ({
            "name": self.name,
            "bounds": self.bounds,
            "areas": [area.get_tree() for area in self.areas]
        })

    def __str__(self):
        return f"{self.name}"

class Area:
    def __init__(self, area_data={}):
        self.name = area_data.get("name", "Area")
        self.bounds = area_data.get("bounds", [])
        self.valid_coordinates = []

        self.location = area_data.get("location", None)
        self.objects = []

    def get_tree(self):
        return ({
            "name": self.name,
            "bounds": self.bounds,
            "objects": [obj.get_tree() for obj in self.objects]
        })

    def __str__(self):
        return f"{self.name}"

class Object:
    def __init__(self, object_data={}):
        self.name = object_data.get("name", "Area")
        self.bounds = object_data.get("bounds", [])
        self.valid_coordinates = []

        self.area = object_data.get("area", None)

    def get_tree(self):
        return ({
            "name": self.name,
            "bounds": self.bounds
        })

    def __str__(self):
        return f"{self.name}"

