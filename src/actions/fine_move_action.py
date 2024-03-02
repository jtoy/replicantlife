import re

class FineMoveAction:
    #for fine move, i need to know who is near me, perception needs to be updated to provide that info or passed into here
    @classmethod
    def description(cls):
        print("to control the direction to move in")

    @classmethod
    def example_usage(cls):
        return "fine_move <up|up-left|up-right|down|down-left|down-right|left|right>"

    @classmethod
    def explanation(cls):
        return "george will \"fine_move right\" to walk towards the car"

    @classmethod
    def act(cls,agent, pre_processed_direction):
        current_x = agent.x
        current_y = agent.y
        pattern = r'\b(up-left|up-right|down-left|down-right|up|down|left|right)\b'
        match = re.search(pattern, pre_processed_direction)
        if match:
            direction =  match.group(1)
        else:
            direction = "current"
        if direction == "up":
            new_x, new_y = current_x, current_y - 1
        elif direction == "down":
            new_x, new_y = current_x, current_y + 1
        elif direction == "left":
            new_x, new_y = current_x - 1, current_y
        elif direction == "right":
            new_x, new_y = current_x + 1, current_y
        elif direction == "up-left":
            new_x, new_y = current_x - 1, current_y - 1
        elif direction == "up-right":
            new_x, new_y = current_x + 1, current_y - 1
        elif direction == "down-left":
            new_x, new_y = current_x - 1, current_y + 1
        elif direction == "down-right":
            new_x, new_y = current_x + 1, current_y + 1
        elif direction == "current":
            new_x, new_y = current_x, current_y
        else:
            new_x, new_y = current_x, current_y
        agent.x = new_x
        agent.y = new_y


