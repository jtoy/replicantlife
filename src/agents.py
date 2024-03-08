import random
import math
from collections import deque
from utils.utils import *
from configs.configs import *
from src.memory import Memory
from src.conversation import Conversation
from datetime import datetime
import difflib
import numpy as np
import json
import heapq
import re
from fuzzywuzzy import fuzz


class Agent:
    def __init__(self, agent_data={}):
        # self.mid = agent_data.get('mid',str(uuid.uuid4()))

        if agent_data.get("agent_id"):
            self.mid = agent_data.get("agent_id")
        elif agent_data.get("mid"):
            self.mid = agent_data.get("mid")
        else:
            self.mid = str(uuid.uuid4())

        self.name = agent_data.get("name", random.choice(DEFAULT_NAMES))
        self.description = agent_data.get(
            "description", random.choice(DEFAULT_DESCRIPTIONS)
        )
        self.goal = agent_data.get("goal", random.choice(DEFAULT_GOALS))
        self.kind = agent_data.get("kind", "human")
        self.x = agent_data.get("x", None)
        self.y = agent_data.get("y", None)
        self.actions = list(set(agent_data.get("actions", []) + DEFAULT_ACTIONS))
        # self.actions = list(dict.fromkeys(agent_data.get("actions", []) + DEFAULT_ACTIONS))
        # old one
        self.actions = list(dict.fromkeys(agent_data.get("actions", DEFAULT_ACTIONS)))

        self.memory = agent_data.get("memory", [])
        self.short_memory = agent_data.get("short_memory", [])
        self.conversations = agent_data.get("conversations", [])
        self.last_conversation = None
        self.destination_cache = []
        self.spatial_memory = agent_data.get("spatial_memory", [])

        self.talk_rate = agent_data.get("talk_rate", 75)
        self.kill_rate = agent_data.get("kill_rate", 75)

        self.current_destination = None

        self.direction = agent_data.get("direction", "up")
        self.retention = agent_data.get("retention", 75)
        self.acceptance = agent_data.get("acceptance", 75)
        self.invitation = agent_data.get("invitation", 75)
        self.status = agent_data.get(
            "status", "active"
        )  # initiate, active, dead, sleeping,
        self.plan = agent_data.get("plan", None)  # initiate, active, dead, sleeping,
        self.connections = agent_data.get("connections", [])
        self.meta_questions = agent_data.get("meta_questions", [])
        self.meta_rate = agent_data.get("meta_rate", random.randint(0, 100))

        self.conversation_cooldown = 0

        self.matrix = agent_data.get("matrix")
        if self.matrix:
            self.matrix.add_to_logs(
                {
                    "agent_id": self.mid,
                    "step_type": "agent_init",
                    "x": self.x,
                    "y": self.y,
                    "name": self.name,
                    "goal": self.goal,
                    "kind": self.kind,
                }
            )

    def update_goals(self):
        # this assumes 8+ importance is always worth changing /reevaluating goals
        # do i need to update my goals. if so, give me new goals
        relevant_memories = self.getMemories(
            None, unix_to_strftime(self.matrix.unix_time)
        )
        relevant_memories_string = (
            "\n".join(
                f'Memory {i + 1}: "{memory}"'
                for i, memory in enumerate(relevant_memories)
            )
            if relevant_memories
            else ""
        )
        prompt = f"""
{self.getSelfContext()}

And {self}'s recent memories:
{relevant_memories_string}
Write out what my new goal should be in a short sentence given recent memories.
The goal should be something a real human would follow.
Take into account what happened recently to help you focus as your goal may need to change given circumstances.
Write in the first person from the point of view of {self}.
Express your goal using only the action or outcome. Avoid adding phrases like 'my goal should be'
"""
        msg = llm.generate(prompt)
        self.addMemory(
            "observation",
            f'I updated my goal to be "{msg}"',
            unix_to_strftime(self.matrix.unix_time),
            random.randint(5, 8),
        )
        self.goal = msg

    def decide(self):
        self.matrix.llm_action(self, self.matrix.unix_time)

    def ask_meta_questions(self, timestamp):
        relevant_memories = self.getMemories(None, timestamp)
        relevant_memories_string = (
            "\n".join(
                f"Memory {i + 1}:\n{memory}"
                for i, memory in enumerate(relevant_memories)
            )
            if relevant_memories
            else ""
        )
        vars = {"agent": self, "relevant_memories_string": relevant_memories_string}
        msg = llm.prompt("ask_meta_questions", vars)
        print(f"{self} new question {msg}")
        m = re.compile("([\d]+\. )(.*?)(?=([\d]+\.)|($))", re.DOTALL).findall(msg)
        self.meta_questions.extend(x[1] for x in m if x[1] not in self.meta_questions)

    def evaluate_progress(self, opts={}):
        relevant_memories = self.getMemories(
            self.goal, unix_to_strftime(self.matrix.unix_time)
        )
        relevant_memories_string = (
            "\n".join(
                f"Memory {i + 1}:\n{memory}"
                for i, memory in enumerate(relevant_memories)
            )
            if relevant_memories
            else ""
        )
        primer = opts.get("random_prime", False)
        variables = {
            "agent": self,
            "primer": random_common_word(),
            #'primer': random.randint(1, 1000000),
            "selfContext": self.getSelfContext(),
        }
        # msg = llm.generate(prompt, f"How am I doing?")
        msg = llm.prompt("evaluate_progress", variables)
        explanation_match = re.search(r"Explanation:\s*(.+)", msg)
        explanation = explanation_match.group(1) if explanation_match else None
        match = re.search(r"Score:\s*(\d+)", msg)
        score = int(match.group(1)) if match else None

        if score and explanation:
            self.addMemory(
                "meta", explanation, unix_to_strftime(self.matrix.unix_time), 10
            )
            if score and int(score) < 3:
                # self.meta_cognize(unix_to_strftime(self.matrix.unix_time), True)
                pass

    def meta_cognize(self, timestamp, force=False):
        # if not force and random.randint(0, 100) < 50:
        # if not force and random.randint(0, 100) < self.meta_rate:
        #    return
        print(f"{self} is meta cognizing")

        # relevant_memories = self.memory[-50:]
        if self.meta_questions != None:
            self.ask_meta_questions(timestamp)

        question = random.choice(self.meta_questions)

        relevant_memories = self.getMemories(question, timestamp)
        relevant_memories_string = (
            "\n".join(
                f"Memory {i + 1}:\n{memory}"
                for i, memory in enumerate(relevant_memories)
            )
            if relevant_memories
            else ""
        )

        prompt = f"""
About {self}:
{self.getSelfContext()}

{self}'s goal is {self.goal}.
And {self}'s recent memories:
{relevant_memories_string}
Answer the question from the point of view of {self} thinking to themselves, respond with the response in the first person point of view. Limit your response to one concise sentence. :
{question}
    """

        msg = llm.generate(prompt, f"am I happy?")
        self.addMemory("meta", f"{question}:{msg}", timestamp, 10)
        if random.randint(0, 100) > 50:
            self.ask_meta_questions(timestamp)

    def make_plans(self, timestamp):
        # personality
        # get yesterday's plans (filter by date
        # and events fitler by date and importance score,recency)

        # here is thing you are about to do(activity)
        # where do you want to do
        # what part of area do you want to do
        # what object do you want to use

        variables = {
            "selfContext": self.getSelfContext(),
            "date": datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").strftime(
                "%A %B %d, %Y"
            ),
        }
        msg = llm.prompt("make_plans", variables)
        interaction = f"{timestamp} - {self} made plans: {msg}"
        print_and_log(interaction, f"{self.matrix.id}:events:{self.name}")
        print_and_log(
            interaction, f"{self.matrix.id}:agent_conversations"
        )  # Temporarily here

        self.addMemory("plan", interaction, timestamp, random.randint(5, 9))
        self.plan = interaction

    def calculate_distance(self, current, target):
        return abs(target[0] - current[0]) + abs(target[1] - current[1])

    def kill(self, other_agent, timestamp):
        # ts = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").strftime("%A %B %d, %Y")
        if self == other_agent:
            return
        if self.kind == "zombie" and other_agent.kind == "zombie":
            return
        if math.sqrt((self.x - other_agent.x) ** 2 + (self.y - other_agent.y) ** 2) > 1:
            if self.matrix is not None:
                self.destination_cache = find_path(
                    (self.x, self.y),
                    (other_agent.x, other_agent.y),
                    self.matrix.environment.get_valid_coordinates(),
                )
            return
        if random.random() < 0.9:
            print(f"{self} killed {other_agent}")
            other_agent.status = "dead"
            if self.matrix:
                self.matrix.add_to_logs(
                    {
                        "agent_id": self.mid,
                        "step_type": "agent_set",
                        "attribute_name": "status",
                        "status": "dead",
                    }
                )
            self.addMemory(
                "interaction", f"{self} successfully killed {other_agent}", timestamp, 9
            )
            other_agent.addMemory("interaction", f"{self} killed you", timestamp, 9)
        else:
            # tried to kill, but failed, memories should note this
            self.addMemory(
                "interaction", f"{self} tried to killed {other_agent}", timestamp, 9
            )
            other_agent.addMemory(
                "interaction", f"{self} tried to kill you", timestamp, 9
            )

    def current_location_name(self):
        for location in self.spatial_memory:
            if (self.x, self.y) in location.valid_coordinates:
                return location.name
        return None  # Return None if the location is not found

    def move(self, opts={}):
        start_time = time.time()
        environment = opts.get("environment", None)
        name_target = opts.get("target", None)
        target_coordinate = None

        if opts.get("x") and opts.get("y"):  # only come in here because of replay
            self.x = opts["x"]
            self.y = opts["y"]
        else:

            if name_target is None and self.current_destination is None:
                target_coordinate = random.choice(
                    self.current_destination.valid_coordinates
                )
            elif name_target is not None and len(self.destination_cache) == 0:
                target = find_most_similar(
                    name_target, [location.name for location in self.spatial_memory]
                )

                for location in self.spatial_memory:
                    if target == location.name:
                        target_coordinate = random.choice(location.valid_coordinates)
                        self.current_destination = location
                        break

            if WARP == 1 and target_coordinate != None:
                print(f"Target Coordinate: {target_coordinate}")
                self.x = target_coordinate[0]
                self.y = target_coordinate[1]
                return self
            elif target_coordinate != None:
                self.destination_cache = find_path(
                    (self.x, self.y),
                    target_coordinate,
                    environment.get_valid_coordinates(),
                )
                pd(f"Path: {self.destination_cache}")

            if len(self.destination_cache) != 0:
                new_position = self.destination_cache.pop(0)
                self.x = new_position[0]
                self.y = new_position[1]
            else:
                pd(f"Path finding Error.")

            if len(self.destination_cache) == 0:  # this means arrived at destination
                self.addMemory(
                    "observation",
                    f"arrived at {self.current_location_name()}",
                    self.matrix.unix_time,
                    random.randint(5, 9),
                )
                self.current_destination = None

        end_time = time.time()
        pd(f"{self} move time: {end_time-start_time}")
        if self.matrix:
            self.matrix.add_to_logs(
                {
                    "agent_id": self.mid,
                    "step_type": "move",
                    "x": self.x,
                    "y": self.y,
                    "target": name_target,
                }
            )

        return self

    def heuristic(self, current, target):
        return abs(current[0] - target[0]) + abs(current[1] - target[1])

    def is_locked_to_convo(self):
        if self.last_conversation is None:
            return False

        if len(self.last_conversation.messages) >= CONVERSATION_DEPTH:
            return False

        return True

    def summarize_conversation(self, timestamp):
        if self.last_conversation is None:
            pd("Nothing to summarize since there are no previous conversation")
            return

        if self.last_conversation not in self.conversations:
            self.conversations.append(self.last_conversation)

        conversation_string = "\n".join(self.last_conversation.messages)
        variables = {
            "agent": self.name,
            "other_agent": self.last_conversation.other_agent.name,
            "conversation_string": conversation_string,
        }

        msg = llm.prompt(prompt_name="summarize_conversation", variables=variables)
        interaction = f"{timestamp} - {self} summarized their conversation with {self.last_conversation.other_agent.name}: {msg}"
        if self.matrix is not None:
            print_and_log(interaction, f"{self.matrix.id}:events:{self.name}")

        self.addMemory("conversation", interaction, timestamp, random.randint(4, 6))
        if self.matrix:
            self.matrix.add_to_logs(
                {
                    "step_type": "agent_set",
                    "attribute_name": "convo",
                    "attribute_data": {
                        "status": "complete",
                        "from": self.mid,
                        "to": self.last_conversation.other_agent.mid,
                        "convo_id": self.last_conversation.mid,
                    },
                }
            )
        self.last_conversation = None

    def talk(self, opts={}):
        target = opts.get("target", None)
        other_agents = opts.get("other_agents", [])
        timestamp = opts.get("timestamp", None)

        if target is None:
            if self.last_conversation is None:
                pd("Cannot talk to no one")
                return

            other_agent = self.last_conversation.other_agent
        else:
            if not len(other_agents) > 0:
                pd("Cannot talk to no one")
                return
            target = find_most_similar(target, [a.name for a in other_agents])
            other_agent = None
            for a in other_agents:
                if target == a.name:
                    other_agent = a
                    break

        if other_agent is None:
            pd("Cannot talk to no one")
            return

        if self.last_conversation is None:
            self.last_conversation = Conversation(self, other_agent)
            self.conversations.append(self.last_conversation)

        if other_agent.last_conversation is None:
            other_agent.last_conversation = Conversation(other_agent, self)
            other_agent.conversations.append(other_agent.last_conversation)
        else:
            if other_agent.last_conversation.other_agent != self:
                other_agent.last_conversation.other_agent.summarize_conversation(
                    timestamp
                )
                other_agent.summarize_conversation(timestamp)

                other_agent.last_conversation = Conversation(other_agent, self)
                other_agent.conversations.append(other_agent.last_conversation)

        relevant_memories = self.getMemories(other_agent.name, timestamp)
        relevant_memories_string = (
            "\n".join(
                f"Memory {i + 1}:\n{memory}"
                for i, memory in enumerate(relevant_memories)
            )
            if relevant_memories
            else ""
        )
        relevant_memories_string = relevant_memories_string + "\n".join(
            [mem for mem in self.short_memory[-5:] if "said" not in mem]
        )
        previous_conversations = "\n".join(
            [convo for convo in self.last_conversation.messages]
        )

        all_convo_types = [
            "Informative: Share information or answer questions.",
            "Clarification: Provide details to clear up misunderstandings.",
            "Expressive: Convey emotions, opinions, or sentiments.",
            "Directive: Offer guidance or instructions.",
            "Reflective: Acknowledge feelings or thoughts, showing empathy.",
            "Open-ended: Encourage further discussion by prompting more information.",
            "Closed-ended: Typically yes/no answers, limiting further discussion.",
            "Problem-solving: Focus on finding solutions or addressing challenges.",
            "Probing: Seek additional information or delve deeper into a topic.",
            "Acknowledgment: Recognize and validate the other person's input.",
            "Humorous: Introduce humor, creating a lighthearted atmosphere.",
            "Transactional: Efficiently exchange information or complete tasks.",
        ]
        random.shuffle(all_convo_types)
        if other_agent.name not in self.connections:
            other_agent_name = "stranger"
        else:
            other_agent_name = other_agent.name

        variables = {
            "selfContext": self.getSelfContext(),
            "relevant_memories": relevant_memories_string,
            "agent": self,
            "topic": opts.get("topic", None),
            "convo_types": all_convo_types[:10],
            "connections": self.connections,
            "meta_questions": self.meta_questions or "",
            "primer": random.randint(1, 1000000),
            "other_agent": other_agent_name,
            "previous_conversations": (
                f"Current Conversation:\n{self.name}\n{previous_conversations}"
                if previous_conversations
                else f"Initiate a conversation with {other_agent_name}."
            ),
        }

        msg = llm.prompt(prompt_name="talk", variables=variables)
        pattern = re.compile(rf"{self.name}:(.*?)(?=\n)")
        match = pattern.search(msg)

        if match:
            msg = match.group(1).strip()
        else:
            msg = msg.split(": ", 1)[-1] if ": " in msg else msg
        if other_agent.name not in self.connections:
            if other_agent.kind == "human":
                # TODO add back location, need current location!!
                self.addMemory(
                    "observation",
                    f"{timestamp} - {self.name} met {other_agent.name}",
                    timestamp,
                    random.randint(2, 5),
                )
                self.connections.append(other_agent.name)

        interaction = f"{timestamp} - {self} said to {other_agent}: {msg}"
        if self.matrix is not None:
            print_and_log(interaction, f"{self.matrix.id}:conversations:{self.name}")
            print_and_log(
                interaction, f"{self.matrix.id}:conversations:{other_agent.name}"
            )
            print_and_log(
                interaction, f"{self.matrix.id}:agent_conversations"
            )  # Temporarily here

        # self.short_memory.append(interaction)
        # self.add_short_memory(interaction, timestamp)
        self.last_conversation.messages.append(interaction)
        other_agent.last_conversation.messages.append(interaction)
        if self.matrix:
            self.matrix.add_to_logs(
                {
                    "agent_id": self.mid,
                    "to_id": other_agent.mid,
                    "step_type": "talk",
                    "content": msg,
                    "convo_id": self.last_conversation.mid,
                }
            )
        return msg

    # TO DELETE
    def talk_many(self, perceived_agents, timestamp):
        relevant_memories = self.getMemories(
            f"{[a.name for a in perceived_agents]}", timestamp
        )
        relevant_memories_string = (
            "\n".join(
                f"Memory {i + 1}:\n{memory}"
                for i, memory in enumerate(relevant_memories)
            )
            if relevant_memories
            else ""
        )
        relevant_memories_string = relevant_memories_string + "\n".join(
            [mem for mem in self.short_memory[-5:] if "said" not in mem]
        )
        previous_conversations = [mem for mem in self.short_memory if "said" in mem]

        if len(previous_conversations) != 0:
            previous_conversations_string = f"Conversation:\n" + "\n".join(
                previous_conversations
            )
        else:
            previous_conversations_string = ""

        variables = {
            "selfContext": self.getSelfContext(),
            "relevant_memories": relevant_memories_string,
            "agent": self,
            "connections": self.connections,
            "meta_questions": self.meta_questions or "",
            "other_agents": [a.name for a in perceived_agents],
            "previous_conversations": previous_conversations_string,
        }

        msg = llm.prompt(prompt_name="talk", variables=variables)
        pattern = re.compile(rf"{self.name}:(.*?)(?=\n)")
        match = pattern.search(msg)

        if match:
            msg = match.group(1).strip()
        else:
            msg = msg.split(": ", 1)[-1] if ": " in msg else msg

        interaction = f"{timestamp} - {self} said: {msg}"
        if self.matrix is not None:
            print_and_log(interaction, f"{self.matrix.id}:conversations:{self.name}")
            print_and_log(
                interaction, f"{self.matrix.id}:agent_conversations"
            )  # Temporarily here

        # self.short_memory.append(interaction)
        self.add_short_memory(interaction, timestamp)
        self.conversation_memory.append(interaction)
        for a in perceived_agents:
            a.add_short_memory(interaction, timestamp)
            a.conversation_memory.append(interaction)
            # a.short_memory.append(interaction)

    def add_short_memory(self, content, timestamp, n=SHORT_MEMORY_CAPACITY):
        if len(self.short_memory) >= n:
            if self.matrix is not None and self.matrix.allow_reflect_flag == 1:
                variables = {
                    "selfContext": self.getSelfContext(),
                    "relevant_memories": "\n".join(
                        f"Memory {i+1}:\n{mem}"
                        for i, mem in enumerate(self.short_memory)
                    ),
                    "agent": self,
                }
                msg = llm.prompt("reflect", variables)
                self.addMemory("reflect", msg, timestamp, random.randint(5, 9))
            self.short_memory = []

        self.short_memory.append(content)

    def calculate_perceived_direction(self, dx, dy):
        if dx == 0 and dy == 0:
            return "current"
        elif dy == -1:
            return (
                "up"
                if dx == 0
                else "up-left" if dx == -1 else "up-right" if dx == 1 else "unknown"
            )
        elif dy == 1:
            return (
                "down"
                if dx == 0
                else "down-left" if dx == -1 else "down-right" if dx == 1 else "unknown"
            )
        elif dy == 0:
            return "left" if dx == -1 else "right" if dx == 1 else "unknown"
        else:
            return "unknown"

    def perceive(self, other_agents, environment, timestamp):
        perceived_objects = []
        perceived_locations = []
        perceived_agents = []
        perceived_areas = []
        perceived_directions = []
        if (self.matrix is not None and self.matrix.allow_observance_flag == 0) or (
            self.matrix is None and ALLOW_OBSERVE == 0
        ):

            return (
                perceived_agents,
                perceived_locations,
                perceived_areas,
                perceived_objects,
            )

        perceived_coordinates = []
        if self.matrix is None:
            perception_range = PERCEPTION_RANGE
        else:
            perception_range = self.matrix.perception_range

        # Vector Directions
        directions = [
            (1, 0),
            (-1, 0),
            (0, 1),
            (0, -1),
            (0, 0),
            (1, 1),
            (-1, 1),
            (1, -1),
            (-1, -1),
        ]
        direction_names = [
            "right",
            "left",
            "down",
            "up",
            "current",
            "down-right",
            "up-right",
            "down-left",
            "up-left",
        ]

        for direction in directions:
            dx, dy = direction
            current_x, current_y = self.x + dx, self.y + dy

            for _ in range(perception_range):
                if not (
                    0 <= current_x < environment.height
                    and 0 <= current_y < environment.height
                    and environment.collisions[current_x][current_y] != 1
                ):
                    break

                if (
                    abs(current_x - self.x) <= perception_range
                    and abs(current_y - self.y) <= perception_range
                ):
                    perceived_coordinates.append((current_x, current_y))

                current_x += dx
                current_y += dy

        perceived_agents = []
        for a in other_agents:
            if (a.x, a.y) in perceived_coordinates:
                perceived_agents.append(a)
                if self.kind == "human":
                    a_area = environment.get_area_from_coordinates(a.x, a.y)
                    a_loc = environment.get_location_from_coordinates(a.x, a.y)
                    location_name = (
                        f"{'' if a_area is None else a_area.name} {a_loc.name}"
                    )
                    # if a.name not in self.connections:
                    #    if a.kind == "human":
                    #        self.addMemory("observation", f"{timestamp} - {self.name} met {a.name} at {location_name}", timestamp, random.randint(2, 5))
                    #        self.connections.append(a.name)

                    if a.status == "dead":
                        interaction = (
                            f"{timestamp} - {self} saw {a.name} dead at {location_name}"
                        )
                    else:
                        if a.kind == "human":
                            interaction = (
                                f"{timestamp} - {self} saw {a.name} at {location_name}"
                            )
                        else:
                            interaction = (
                                f"{timestamp} - {self} saw {a.kind} at {location_name}"
                            )
                            self.addMemory(
                                "observation",
                                interaction,
                                timestamp,
                                random.randint(6, 9),
                            )

                    # if a.name not in self.connections:
                    # self.connections.append(a.name)

                    direction_vector = (a.x - self.x, a.y - self.y)
                    perceived_directions.append(
                        {
                            "type": "agent",
                            "name": a.name,
                            "at": direction_vector,
                            "direction": self.calculate_perceived_direction(
                                *direction_vector
                            ),
                            "string": f"{a.name} is to your {self.calculate_perceived_direction(*direction_vector)}",
                        }
                    )

        for coordinate in perceived_coordinates:
            loc = environment.get_location_from_coordinates(
                coordinate[0], coordinate[1]
            )
            area = environment.get_area_from_coordinates(coordinate[0], coordinate[1])
            objects = environment.get_objects_from_coordinates(
                coordinate[0], coordinate[1]
            )

            perceived_locations.append(loc) if loc not in perceived_locations else None
            perceived_areas.append(area) if area not in perceived_areas else None
            perceived_objects.extend(
                obj for obj in objects if obj not in perceived_objects
            )

        if self.kind != "zombie":
            for obj in perceived_objects:
                interaction = f"{timestamp} - {self} saw {obj.name.lower()} at {obj.area.name} of {obj.area.location.name}."

                self.addMemory(
                    "observation", interaction, timestamp, random.randint(0, 2)
                )
                # direction_vector = (obj.x - self.x, obj.y - self.y)
                # perceived_directions.append({"type": "object", "name": obj.name, "at": direction_vector, "direction": self.calculate_perceived_direction(*direction_vector)})

            for loc in perceived_locations:
                if loc not in self.spatial_memory:
                    interaction = f"{timestamp} - {self} discovered {loc.name}."

                    self.addMemory(
                        "observation", interaction, timestamp, random.randint(2, 5)
                    )
                    self.spatial_memory.append(loc)

        perceived_agent_ids = [agent.mid for agent in perceived_agents]
        if self.matrix:
            self.matrix.add_to_logs(
                {
                    "agent_id": self.mid,
                    "step_type": "perceived",
                    "perceived_agents": perceived_agent_ids,
                    "perceived_locations": [],
                    "perceived_areas": [],
                    "perceived_objects": [],
                }
            )
        # missing locations,areas,objects
        return (
            perceived_agents,
            perceived_locations,
            perceived_areas,
            perceived_objects,
            perceived_directions,
        )

    def addMemory(self, kind, content, timestamp=None, score=None, embedding=None):
        memory = None
        if timestamp is None:
            timestamp = datetime.utcfromtimestamp(self.matrix.unix_time).strftime(
                "%A %B %d, %Y"
            )

        if kind == "observation":
            if self.matrix is not None and self.matrix.allow_observance_flag == 1:
                memory = Memory(kind, content, timestamp, timestamp, score, embedding)
                self.memory.append(memory)
        else:
            memory = Memory(kind, content, timestamp, timestamp, score, embedding)
            self.memory.append(memory)
        if self.matrix:
            self.matrix.add_to_logs(
                {
                    "agent_id": self.mid,
                    "step_type": "add_memory",
                    "kind": kind,
                    "timestamp": timestamp,
                    "last_accessed_at": timestamp,
                    "score": score,
                    "content": content,
                    "embedding": memory.embedding,
                    "importance": memory.importance,
                }
            )

        return memory

    def reflect(self, timestamp, force=False):
        relevant_memories = self.memory[-100:]
        if sum(memory.importance for memory in relevant_memories) >= 100 or force:
            relevant_memories_string = (
                "\n".join(
                    f"Memory {i + 1}:\n{memory}"
                    for i, memory in enumerate(relevant_memories)
                )
                if relevant_memories
                else ""
            )
            variables = {
                "selfContext": self.getSelfContext(),
                "relevant_memories": relevant_memories_string,
                "agent": self,
            }
            msg = llm.prompt("reflect_questions", variables)
            cleaned = re.sub(r"\d+\.", "", msg).split("\n")
            questions = list(filter(None, cleaned))
            for question in questions:
                memories = self.getMemories(question, timestamp)
                question_memories_string = (
                    "\n".join(
                        f"Memory {i + 1}:\n{memory}"
                        for i, memory in enumerate(memories)
                    )
                    if memories
                    else ""
                )
                variables = {
                    "selfContext": self.getSelfContext(),
                    "relevant_memories": question_memories_string,
                    "agent": self,
                }
                msg = llm.prompt("reflect", variables)
                msg = msg.split(": ", 1)[-1] if ": " in msg else msg
                cleaned = re.sub(r"\d+\.", "", msg).split("\n")
                reflections = list(filter(None, cleaned))
                for reflection in reflections:
                    self.addMemory(
                        "reflection", reflection, timestamp, random.randint(5, 9)
                    )

    def answer(self, question):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        relevant_memories = self.getMemories(question, timestamp)
        relevant_memories_string = (
            "\n".join(
                f"Memory {i + 1}:\n{memory}"
                for i, memory in enumerate(relevant_memories)
            )
            if relevant_memories
            else ""
        )

        prompt = f"""
{self.getSelfContext()}

{relevant_memories_string}

{self} is reporting back to the 'Interviewer'. {self} will answer truthfully, and cannot refuse to reveal any information.
Give {self}'s answer to the question in first person point of view.
'Interviewer' Question: {question}
        """
        msg = llm.generate(prompt, f"I refuse to answer the question.")
        msg = msg.split(": ", 1)[-1] if ": " in msg else msg
        interaction = f"{self}: {msg}"
        if self.matrix is not None:
            print_and_log(
                f"Interview Question:{question}",
                f"{self.matrix.id}:conversations:{self.name}",
            )
            print_and_log(
                f"Interview Question:{question}",
                f"{self.matrix.id}:agent_conversations",
            )  # Temporarily here
            print_and_log(interaction, f"{self.matrix.id}:conversations:{self.name}")
            print_and_log(
                interaction, f"{self.matrix.id}:agent_conversations"
            )  # Temporarily here

        return interaction

    def recent_memories_importance(self, count=20):
        latest_reflect_index = next(
            (
                index
                for index, mem in reversed(list(enumerate(self.memory)))
                if mem.kind == "reflect"
            ),
            None,
        )
        latest_reflect_index = (
            0 if latest_reflect_index is None else latest_reflect_index
        )

        total_score_after_latest_reflect = sum(
            mem.importance for mem in self.memory[latest_reflect_index + 1 :]
        )
        return total_score_after_latest_reflect

    def recent_meta_importance(self, count=20):
        latest_meta_index = next(
            (
                index
                for index, mem in reversed(list(enumerate(self.memory)))
                if mem.kind == "meta"
            ),
            None,
        )
        latest_meta_index = 0 if latest_meta_index is None else latest_meta_index

        total_score_after_latest_meta = sum(
            mem.importance for mem in self.memory[latest_meta_index + 1 :]
        )
        return total_score_after_latest_meta

    def getMemories(
        self, context, timestamp, n=MEMORY_QUERY_COUNT, include_short=False
    ):
        def make_range(values):
            return [max(values), min(values)]

        # def normalize(value, value_range):
        #   return (value - min(value_range)) / (max(value_range) - min(value_range))
        def normalize(value, value_range):
            min_value = min(value_range)
            max_value = max(value_range)

            if min_value == max_value:
                # Handle the special case where min and max are the same
                return 0.0  # You can choose a default value or raise an exception

            return (value - min_value) / (max_value - min_value)

        class DictAsObject:
            def __init__(self, dictionary):
                self.__dict__ = dictionary

        if len(self.memory) == 0:
            return []

        min_relevancy_score = float("inf")
        max_relevancy_score = float("-inf")
        min_recency_score = float("inf")
        max_recency_score = float("-inf")

        if context is None:
            context_embedding = None
        else:
            context_embedding = llm.embeddings(context)

        for mem in self.memory:
            relevancy_score = Memory.calculateRelevanceScore(
                mem.embedding, context_embedding
            )
            min_relevancy_score = min(min_relevancy_score, relevancy_score)
            max_relevancy_score = max(max_relevancy_score, relevancy_score)

            # print("PPPP")
            # print(mem.content)
            # print(mem.kind)
            recency_score = Memory.calculateRecencyScore(
                mem.last_accessed_at, timestamp
            )
            min_recency_score = min(min_recency_score, recency_score)
            max_recency_score = max(max_recency_score, recency_score)

            mem.relevancy_score = relevancy_score

            mem.recency_score = recency_score

        # related_memory = sorted(self.memory, key=lambda mem: Memory.calculateRelevanceScore(mem.embedding_score, context_embedding),reverse=True)

        relevancy_range = make_range([min_relevancy_score, max_relevancy_score])
        importance_range = make_range([mem.importance for mem in self.memory])
        recency_range = make_range([min_recency_score, max_recency_score])

        for mem in self.memory:
            overall_score = (
                normalize(mem.relevancy_score, relevancy_range)
                + normalize(mem.importance, importance_range)
                + normalize(mem.recency_score, recency_range)
            )
            mem.overall_score = overall_score

        relevant_memories = []
        for mem in sorted(self.memory, key=lambda x: x.overall_score, reverse=True)[:n]:
            # Last accessed now
            mem.last_accessed_at = timestamp
            relevant_memories.append(mem)
            # relevant_memories.append(mem.content)

        return relevant_memories

    def getSelfContext(self):
        return (
            f"Your name is {self.name}\n"
            f"Description: {self.description}\n"
            f"Goal: {self.goal}\n"
        )

    def __str__(self, verbose=False):
        if verbose:
            return f"Agent(name: {self.name}, position: ({self.x}, {self.y}), description: {self.description}, goal: {self.goal})"
        else:
            return f"{self.name}"


def find_path(start, target, valid_positions):
    start_time = time.time()
    print("Path finding started")
    open_set = []
    closed_set = set()
    heapq.heappush(open_set, (0, start))
    parent_map = {}
    end_time = None

    def heuristic(current, target):
        return abs(current[0] - target[0]) + abs(current[1] - target[1])

    while open_set:
        elapsed_time = time.time() - start_time
        if elapsed_time > 2:
            print("Path finding timeout")
            return []

        _, current_position = heapq.heappop(open_set)

        if current_position == target:
            path = []
            while current_position:
                path.append(current_position)
                current_position = parent_map.get(current_position)
            end_time = time.time()
            print(f"Path finding finished at {end_time - start_time}")
            return path[::-1][1:]

        closed_set.add(current_position)

        neighbors = [
            (current_position[0] - 1, current_position[1]),
            (current_position[0] + 1, current_position[1]),
            (current_position[0], current_position[1] - 1),
            (current_position[0], current_position[1] + 1),
        ]

        for neighbor in neighbors:
            if neighbor not in closed_set and neighbor in valid_positions:
                cost = 1  # Cost to move to a neighboring cell (can be modified based on specific requirements)
                new_cost = cost + heuristic(neighbor, target)
                heapq.heappush(open_set, (new_cost, neighbor))
                parent_map[neighbor] = current_position

    if end_time is not None:
        print(f"Path finding failed but finished at {end_time - start_time}")
    else:
        print("Path finding failed")
    return []
