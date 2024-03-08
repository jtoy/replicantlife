import random
from utils.utils import *
from src.memory import Memory
from src.agents import Agent
from datetime import datetime
import numpy as np
import json
import heapq
import re


class Npc(Agent):
    simulation_id = 42

    def __init__(self, agent_data):
        self.id = str(uuid.uuid4())
        self.name = agent_data.get("name", "")
        self.description = agent_data.get(
            "description", "A zombie that chase and kills humans"
        )
        self.goal = agent_data.get("goal", "Goal is to kill all humans")
        self.x = agent_data["position"][0] if "position" in agent_data else 0
        self.y = agent_data["position"][1] if "position" in agent_data else 0
        self.direction = agent_data.get("direction", "up")
        self.path = []
        self.acceptance = 0
        self.invitation = 0
        self.retention = 100
        self.last_conversation = None
        self.spatial_memory = agent_data.get("spatial_memory", None)
        self.destination = None
        self.is_busy = False
        self.status = "active"  # initiate, active, dead, sleeping,
        self.memory = []
        self.actions = ["move"]
        self.specie = "zombie"
        self.interactions = set()

    def kill(self, other, timestamp):
        if self == other or (self.specie == "zombie" and other.specie == "zombie"):
            return
        if random.random() < 0.5:
            print(f"{self.name} killed {other}")
            other.status = "dead"
        else:
            # tried to kill, but failed, memories should note this
            other.addMemory("interaction", f"{self.name} tried to kill you", timestamp)

    def make_plans(self, unix_time):
        pass

    def move(self, n, collisions, timestamp):
        if self.destination is None:
            # Move randomly
            possible_moves = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            random_move = random.choice(possible_moves)
            new_position = (self.x + random_move[0], self.y + random_move[1])

            # Ensure the new position is valid
            while not self.is_position_valid(n, collisions, new_position):
                random_move = random.choice(possible_moves)
                new_position = (self.x + random_move[0], self.y + random_move[1])

            self.destination = {"x": new_position[0], "y": new_position[1]}

        # If zombie has arrived at the destination, reset the destination
        if self.x == self.destination["x"] and self.y == self.destination["y"]:
            print(f"{self} has arrived at {self.destination}")
            self.destination = None
            return (self.x, self.y, "up")
        else:
            print(f"{self} is travelling to {self.destination}")

        # Move towards the last seen human
        if len(self.path) == 0:
            # If there is no current path, find a path to a random human if available
            humans = [
                agent
                for agent in self.spatial_memory
                if agent.get("specie", "") == "human"
            ]
            if humans:
                random_human = random.choice(humans)
                self.path = self.find_path(
                    (self.x, self.y),
                    (random_human["x"], random_human["y"]),
                    n,
                    collisions,
                )
            else:
                # If no humans are in memory, move randomly
                possible_moves = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                random_move = random.choice(possible_moves)
                new_position = (self.x + random_move[0], self.y + random_move[1])

                # Ensure the new position is valid
                while not self.is_position_valid(n, collisions, new_position):
                    random_move = random.choice(possible_moves)
                    new_position = (self.x + random_move[0], self.y + random_move[1])

                self.destination = {"x": new_position[0], "y": new_position[1]}
                self.path = []

        # If there is an existing path, pop and continue
        if len(self.path) == 0:
            self.destination = None
            return (self.x, self.y, "up")
        else:
            print(f"Current Path: {self.path}")
            return self.path.pop(0)

    def perceive(self, other, perception_range, collisions, timestamp):
        def has_blocker_between(agent, other, collisions):
            x1, y1 = agent.x, agent.y
            x2, y2 = other.x, other.y

            x1, y1, x2, y2 = (
                int(round(x1)),
                int(round(y1)),
                int(round(x2)),
                int(round(y2)),
            )

            dx = abs(x2 - x1)
            dy = abs(y2 - y1)
            sx = 1 if x1 < x2 else -1
            sy = 1 if y1 < y2 else -1
            err = dx - dy

            while x1 != x2 or y1 != y2:
                if (
                    x1 >= 0
                    and y1 >= 0
                    and x1 < len(collisions)
                    and y1 < len(collisions[0])
                    and collisions[x1][y1] == 1
                ):
                    return True

                e2 = 2 * err
                if e2 > -dy:
                    err = err - dy
                    x1 = x1 + sx
                if e2 < dx:
                    err = err + dx
                    y1 = y1 + sy

            return False

        can_perceive = (
            abs(self.x - other.x) <= perception_range
            and abs(self.y - other.y) <= perception_range
            and not has_blocker_between(self, other, collisions)
            and self != other
        )

        if can_perceive:
            if other.__class__.__name__ == "Agent" and other.status == "dead":
                interaction = f"{timestamp} - {self.name} saw {other.name} dead"
            else:
                interaction = f"{timestamp} - {self.name} saw {other.name}"

            redis_connection.lpush("agent_conversations", json.dumps(interaction))
            self.addMemory("observation", interaction, timestamp)

            # Store information about the perceived agent
            perceived_agent_info = {
                "name": other.name,
                "x": other.x,
                "y": other.y,
            }
            if isinstance(other, Agent) and other.specie == "human":
                perceived_agent_info["specie"] = "human"
            else:
                perceived_agent_info["specie"] = "zombie"
            self.spatial_memory.append(perceived_agent_info)

        return can_perceive

    def __str__(self, verbose=False):
        if verbose:
            return f"Npc(name: {self.name}, specie:{self.specie} position: {self.position}, description: {self.description}, goal: {self.goal})"
        else:
            return f"{self.name}"
