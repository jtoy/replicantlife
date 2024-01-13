import subprocess
import random
from datetime import datetime
import concurrent.futures
import sys
import re
import time
import json
import redis
import requests
import signal
import argparse
import threading
from concurrent.futures import ThreadPoolExecutor

from save_report import save_report
from utils.utils import *
from utils.names import FIRST_NAMES
from src.agents import Agent
from src.environment import Environment
from src.npc import Npc
from src.location import Location, Area, Object


class Matrix:
    def __init__(self, matrix_data={}):
        self.steps = matrix_data.get("steps", SIMULATION_STEPS)
        self.llm_action_flag = matrix_data.get("llm_action", LLM_ACTION)
        self.allow_plan_flag = matrix_data.get("allow_plan", ALLOW_PLAN)
        self.allow_reflect_flag = matrix_data.get("allow_reflect", ALLOW_REFLECT)
        self.allow_meta_flag = matrix_data.get("allow_meta", ALLOW_META)
        self.allow_observance_flag = matrix_data.get("allow_observance", ALLOW_OBSERVANCE)

        self.id = matrix_data.get("id", str(uuid.uuid4()))
        self.scenario_file = matrix_data.get("scenario", "configs/def.json")
        self.environment_file = matrix_data.get("environment", "configs/largev2.tmj")
        self.agents = []
        self.default_goals = []
        self.default_descriptions = []
        self.interview_questions = []
        self.interview_results = {}
        self.reflect_threshold = REFLECT_THRESHOLD
        self.cur_step = 0
        self.unix_time = DEFAULT_TIME
        self.status = "init"
        self.conversation_counter = 0
        self.sim_start_time = None
        self.simulation_runtime = None
        self.llm_calls = 0
        self.performance_metrics = {}
        self.performance_evals = {}

        self.num_npc = NUM_AGENTS
        self.num_zombies = NUM_ZOMBIES
        self.perception_range = PERCEPTION_RANGE
        self.allow_movement = matrix_data.get("allow_movement", ALLOW_MOVEMENT)
        self.model = MODEL
        # Build Environment
        self.environment = Environment({ "filename": self.environment_file })
        self.background = None
        self.performance_metrics[self.performance_evals["numerator"]] = 0
        self.performance_metrics["denominator"] = self.performance_evals["denominator"]

        # Setup Scenario
        if self.scenario_file is not None:
            self.parse_scenario_file(self.scenario_file)


        self.agent_locks = { agent: threading.Lock() for agent in self.agents }

    def parse_scenario_file(self, filename):
        with open(filename, 'r') as file:
            data = json.load(file)

        # Build Scenario
        self.perception_range = data.get("perception_range", PERCEPTION_RANGE)
        self.allow_movement = data.get("allow_movement", ALLOW_MOVEMENT)
        self.background = data.get("background", "")
        if self.steps <= 0:
            self.steps = data.get("steps", 100)
        if self.num_npc <= 0:
            self.num_npc = data.get("num_npc", 0)
        if self.num_zombies <= 0:
            self.num_zombies = data.get("num_zombies", 0)

        if REFLECT_THRESHOLD <= 0:
            self.reflect_threshold = data.get("reflect_threshold", 50)
        else:
            self.reflect_threshold = REFLECT_THRESHOLD
        self.model = data.get("model", MODEL)
        self.interview_questions = data.get("questions", DEFAULT_QUESTIONS)
        self.unix_time = data.get("unix_time", DEFAULT_TIME)

        # Add Agents
        for agent_data in data.get("agents", []):
            agent = Agent(agent_data)
            agent.matrix = self
            self.add_agent_to_simulation(agent)

        for goal in data.get("default_goals", DEFAULT_GOALS):
            self.default_goals.append(goal)

        for description in data.get("default_descriptions", DEFAULT_DESCRIPTIONS):
            self.default_descriptions.append(description)

        # Add NPCs
        for i in range(self.num_npc):
            if len(self.default_goals) == 1:
              description = f"{random.choice(self.default_descriptions)}"
              goal = self.default_goals[0]
            else:
                description, goal = random.choice(list(zip(self.default_descriptions, self.default_goals)))
            name = self.generate_unique_name()
            agent = Agent({ "name": name, "description": description, "goal": goal, "kind": "npc" })
            agent.matrix = self
            self.add_agent_to_simulation(agent)

        # Add Zombies
        for i in range(self.num_zombies):
            zombie = Agent({ "name": f"Zombie_{i}", "kind": "zombie", "actions": ["kill"] })
            zombie.matrix = self
            self.add_agent_to_simulation(zombie)

    def add_agent_to_simulation(self, agent):
        valid_coordinates = self.environment.get_valid_coordinates()

        if (agent.x, agent.y) not in valid_coordinates:
            new_position = random.choice(valid_coordinates)
            agent.x = new_position[0]
            agent.y = new_position[1]

        if agent.kind != "zombie":
            parsed_spatial_mem = []
            if len(agent.spatial_memory) > 0:
                for loc in self.environment.locations:
                    if loc.name in agent.spatial_memory:
                        parsed_spatial_mem.append(loc)


            interaction = f"{self.unix_to_strftime(self.unix_time)} - {agent} knows the locations: {agent.spatial_memory}."
            agent.addMemory("observation", interaction, self.unix_to_strftime(self.unix_time), random.randint(0,2))
            agent.spatial_memory = parsed_spatial_mem
        else:
            agent.spatial_memory = self.environment.locations

        self.agents.append(agent)

    def get_server_info(self):
        try:
            # Run 'uname -a' command
            uname_output = subprocess.check_output(['uname', '-a']).decode('utf-8').strip()
            return uname_output
        except Exception as e:
            # Handle any exceptions that may occur
            return f"Error getting server info: {str(e)}"

    def all_env_vars(self):
        if self.sim_start_time is None:
            self.sim_start_time = datetime.now()

        if self.simulation_runtime is None:
            self.simulation_runtime = datetime.now() - self.sim_start_time

        total_reflections = 0
        total_metas = 0
        for a in self.agents:
            for m in a.memory:
                if m.kind == "reflect":
                    total_reflections += 1
                if m.kind == "meta":
                    total_metas += 1

        total_seconds = self.simulation_runtime.total_seconds()

        # Calculate minutes and seconds
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)

        # Create a human-readable string
        runtime_string = f"{minutes} minute(s) and {seconds} second(s)"

        return {
            "id": self.id,
            "map": self.environment_file,
            "agents": self.scenario_file,
            "date": self.sim_start_time.isoformat(),
            "width": self.environment.width,
            "height": self.environment.width,
            "status": self.status,
            "runtime": runtime_string, # Include the string representation
            "server_info": self.get_server_info(),
            "created_at": self.sim_start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "model": self.model,
            "total_steps": self.steps,
            "meta_flag": self.allow_meta_flag,
            "reflect_flag": self.allow_reflect_flag,
            "conversation_counter": self.conversation_counter,
            "total_meta_memories": total_metas,
            "total_reflect_memories": total_reflections,
            "total_agents": sum(1 for agent in self.agents if agent.kind != 'zombie'),
            "total_zombies": sum(1 for agent in self.agents if agent.kind == 'zombie'),
            "total_dead": sum(1 for agent in self.agents if agent.status == 'dead'),
            "llm_call_counter": llm.call_counter,
            "avg_runtime_per_step": total_seconds / self.steps,
            "avg_llm_calls_per_step": llm.call_counter / self.steps
        }


    def send_matrix_to_redis(self):
        if TEST_RUN == 0:
            redis_connection.set(f"{self.id}:simulations", json.dumps(self.all_env_vars()))

    def log_agents_to_redis(self):
        for agent in self.agents:
            agent_data = {
                "name": agent.name,
                "x": agent.x,
                "y": agent.y,
                "status": agent.status
            }
            redis_connection.rpush(f"{self.id}:agents:{agent.name}", json.dumps(agent_data))

    def run_singlethread(self):
        self.status = "running"
        self.sim_start_time = datetime.now()
        self.send_matrix_to_redis()
        for step in range(self.steps):
            self.cur_step = step
            if self.status == "stop":
                pd("stopping simulation")
                break

            start_time = datetime.now()
            pd(f"Step {step + 1}:")

            redis_log(self.get_arr_2D(), f"{self.id}:matrix_states")
            redis_connection.set(f"{self.id}:matrix_state", json.dumps(self.get_arr_2D()))
            print_and_log(f"Step: {step + 1} | {self.unix_to_strftime(self.unix_time)}", f"{self.id}:agent_conversations")

            self.log_agents_to_redis()

            for a in self.agents:
                print_and_log(f"Step: {step + 1} | {self.unix_to_strftime(self.unix_time)}", f"{self.id}:events:{a.name}")
                print_and_log(f"Step: {step + 1} | {self.unix_to_strftime(self.unix_time)}", f"{self.id}:conversations:{a.name}")

            control_cmd = redis_connection.lpop(f"{self.id}:communications")
            if control_cmd:
                control_cmd_str = control_cmd.decode('utf-8')
                try:
                    control_cmd_dict = json.loads(control_cmd_str)

                    name = control_cmd_dict.get('name', None)
                    msg = control_cmd_dict.get('msg', None)
                    control_type = control_cmd_dict.get('type', None)

                    if name:
                        for agent in self.agents:
                            if name == agent.name:
                                agent.addMemory(kind=control_type, content=msg, timestamp=self.unix_to_strftime(self.unix_time), score=10)
                except json.JSONDecodeError as e:
                    print(f"Error decoding control_cmd: {e}")

            # Submit agent actions concurrently
            for i in range(len(self.agents)):
                if self.llm_action_flag == 1 and self.agents[i].kind != 'zombie':
                    self.llm_action(self.agents[i], self.unix_time)
                else:
                    self.agent_action(self.agents[i], self.unix_time)

            if PRINT_MAP == 1:
                self.print_matrix()

            self.unix_time = self.unix_time + 10
            end_time = datetime.now()
            pd(f"LLm calls for Step {step}: {llm.call_counter - self.llm_calls} calls")
            self.llm_calls = llm.call_counter
            pd(f"Step {step + 1} ran in {end_time - start_time}")
            if SLEEP_STEP and SLEEP_STEP > 0:
                time.sleep(SLEEP_STEP)

        self.status = "complete"
        average_llm_calls = llm.call_counter / (step + 1)
        sim_end_time = datetime.now()
        self.simulation_runtime = sim_end_time - self.sim_start_time
        self.print_agent_memories()
        pd(f"made it to step {step + 1}")
        pd(f"Total LLM calls: {llm.call_counter} calls | Average LLM calls: {average_llm_calls} calls")

    def run(self):
        self.status = "running"
        self.sim_start_time = datetime.now()
        self.send_matrix_to_redis()
        for step in range(self.steps):
            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                if self.status == "stop":
                    pd("stopping simulation")
                    break
                start_time = datetime.now()

                pd(f"Step {step}:")

                redis_connection.lpush(f"{self.id}:agent_conversations", json.dumps(f"Step: {step + 1} | {self.unix_to_strftime(self.unix_time)}"))

                # Submit agent actions concurrently
                if LLM_ACTION == 1:
                  futures = [executor.submit(self.llm_action, agent, self.unix_time,step) for agent in self.agents]
                else:
                  futures = [executor.submit(self.agent_action, agent, self.unix_time) for agent in self.agents]
                # Retrieve results from futures
                updated_agents = [future.result() for future in futures]
                # Update the agents' states. Reflect

                #for i, updated_agent in enumerate(updated_agents):
                #    self.agents[i].__dict__.update(updated_agent.__dict__)

                if PRINT_MAP == 1:
                    self.print_matrix()

                redis_connection.set(f"{self.id}:matrix_state", json.dumps(self.get_arr_2D()))
                self.unix_time = self.unix_time + 10
                end_time = datetime.now()
                pd(f"LLm calls for Step {step}: {llm.call_counter - self.llm_calls} calls")
                self.llm_calls = llm.call_counter
                pd(f"Step {step} ran in {end_time - start_time}")
                if SLEEP_STEP and SLEEP_STEP > 0:
                    time.sleep(SLEEP_STEP)

        self.status = "complete"
        average_llm_calls = llm.call_counter / (step + 1)
        sim_end_time = datetime.now()
        self.simulation_runtime = sim_end_time - self.sim_start_time
        self.print_agent_memories()
        pd(f"made it to step {step + 1}")
        pd(f"Total LLM calls: {llm.call_counter} calls | Average LLM calls: {average_llm_calls} calls")

    def unix_to_strftime(self, unix_time):
        return datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")

    def llm_action(self, agent, unix_time):
        if agent.status == "dead":
            return agent

        # It is 12:00, time to make plans
        if unix_time % 86400 == 0 and self.allow_plan_flag == 1:
            agent.make_plans(self.unix_to_strftime(unix_time))

        # Recent memories importance > 100, time to reflect
        if self.allow_reflect_flag == 1 and agent.recent_memories_importance() > self.reflect_threshold:
            agent.reflect(self.unix_to_strftime(unix_time))

        if self.allow_meta_flag == 1 and random.randint(0,100) < 25:
        #if self.allow_meta_flag == 1 and agent.recent_meta_importance() > 30
            agent.evaluate_progress(self.unix_to_strftime(unix_time))
            #agent.meta_cognize(self.unix_to_strftime(unix_time))

        agent.conversation_cooldown -= 1

        # In here, we double check first if agent's conversation messages depth > CONVERSATION_DEPTH
        # we will summarize it and then clear
        if agent.last_conversation is not None:
            if len(agent.last_conversation.messages) >= CONVERSATION_DEPTH:
                other_agent = agent.last_conversation.other_agent

                agent.summarize_conversation(self.unix_to_strftime(unix_time))
                other_agent.summarize_conversation(self.unix_to_strftime(unix_time))

                agent.conversation_cooldown = CONVERSATION_COOLDOWN
                other_agent.conversation_cooldown = CONVERSATION_COOLDOWN

        # In here, if agent is locked to a conversation, no need then to let them decide
        # we let them talk
        if agent.is_locked_to_convo():
            agent.talk({ "other_agents": [agent.last_conversation.other_agent], "timestamp": self.unix_to_strftime(unix_time) })
            return agent

        perceived_agents, perceived_locations, perceived_areas, perceived_objects = agent.perceive([a for a in self.agents if a != agent], self.environment, self.unix_to_strftime(self.unix_time))

        relevant_memories = agent.getMemories(agent.goal, self.unix_to_strftime(unix_time))
        relevant_memories_string = "\n".join(f"Memory {i + 1}:\n{memory}" for i, memory in enumerate(relevant_memories)) if relevant_memories else ""
        current_location = self.environment.get_location_from_coordinates(agent.x, agent.y)
        current_area = self.environment.get_area_from_coordinates(agent.x, agent.y)
        if agent.last_conversation is not None:
            relevant_memories_string += f"\n{agent} is currently in a conversation with {agent.last_conversation.other_agent}.\n"

        other_agents = [a for a in perceived_agents if a.status != "dead" and a.kind != "zombie"]

        #valid_actions = ["stay"]
        #example_strings = "\n\nExplanation: George will stay because it is still too early to go outside.\nAnswer: stay"
        valid_actions = []
        example_strings = "\n\n"
        agents_available_to_talk = []

        if "move" in agent.actions and not agent.is_locked_to_convo() and self.allow_movement == 1:
            # You can move, and have not decided where to move yet
            valid_actions.append("move <location>")
            example_strings = example_strings + "\n\nExplanation: George will move because he needs to be at the Park at 18:00.\nAnswer: move Park"

        if "continue_to_destination" in agent.actions and agent.current_destination is not None and not agent.is_locked_to_convo() and self.allow_movement == 1:
            # You can move, and have already decided where to move
            valid_actions.append("continue_to_destination")
            example_strings = example_strings + "\n\nExplanation: George will continue travelling to the Park because he wants to be there by 18:00.\nAnswer: continue_to_destination"
        if random.randint(0, 100) < 10 and self.allow_meta_flag == 1 and "meta_cognize" in agent.actions:
            valid_actions.append("meta_cognize")
            example_strings = example_strings + "\n\nExplanation: George will meta_cognize because he wants to improve its strategy towards his goal.\nAnswer: meta_cognize"

        if "talk" in agent.actions and not agent.is_locked_to_convo() and agent.conversation_cooldown <= 0:
            agents_available_to_talk = [a for a in other_agents if not a.is_locked_to_convo() and a.conversation_cooldown <= 0]
            if len(agents_available_to_talk) > 0:
                valid_actions.append("talk <person to talk to>")
                example_strings = example_strings + "\n\nExplanation: George will talk to Anne because he is trying to make new friends.\nAnswer: talk Anne"

        if "kill" in agent.actions and len(perceived_agents) > 0 and not agent.is_locked_to_convo():
            valid_actions.append("kill <person to kill>")
            example_strings = example_strings + "\n\nExplanation: George will kill Anne because no one else is around.\nAnswer: kill Anne"

        if len(valid_actions) == 0 and len(agent.destination_cache) > 0:
            interaction = f"{agent} is travelling to {self.environment.get_location_from_coordinates(agent.destination_cache[-1][0], agent.destination_cache[-1][1]).name}"
            print_and_log(interaction, f"{self.id}:events:{agent.name}")
            agent.move()
            return agent

        variables = {
            "selfContext": agent.getSelfContext(),
            "relevant_memories": relevant_memories_string,
            "agent": agent,
            "other_agents": [a.name for a in other_agents],
            "agents_available_to_talk": [a.name for a in agents_available_to_talk],
            'objects': [obj.name.lower() for obj in perceived_objects] + [a.name.lower() for a in perceived_agents if a.kind != "human"],
            'examples': example_strings,
            'actions': valid_actions,
            'location': current_location.name if current_location is not None else "",
            'area': current_area if current_area is not None else "",
            'spatial_memory': [loc.name for loc in agent.spatial_memory],
            'time': self.unix_to_strftime(unix_time)
        }

        msg = llm.prompt("decide", variables)
        match = re.search(r"Answer:\s*(.+)", msg)
        explanation_match = re.search(r"Explanation:\s*(.+)", msg)
        explanation = explanation_match.group(1) if explanation_match else None

        msg = match.group(1) if match else None

        if msg is None:
            return "stay", ""

        decision, parameters = msg.split(" ", 1) + [""] * (1 - msg.count(" "))

        if decision == "talk":
            if len(agents_available_to_talk) > 0:
                agent.talk({ "target": parameters, "other_agents": agents_available_to_talk, "timestamp": self.unix_to_strftime(unix_time) })
                self.conversation_counter += 1
        elif decision == "move":
            agent.move({ "target": parameters, "environment": self.environment })
        elif decision == "continue_to_destination":
            if agent.current_destination is not None:
                agent.move({ "environment": self.environment })
        elif decision == "meta_cognize":
            agent.meta_cognize(self.unix_to_strftime(unix_time),True)
        elif decision == "kill":
            if len(other_agents) > 0:
                target = find_most_similar(parameters, [a.name for a in other_agents])
                for a in other_agents:
                    if target == a.name:
                        agent.kill(a, self.unix_to_strftime(unix_time))
                        if a.status == "dead":
                            witnesses = (set(perceived_agents) - {a})
                            for witness in witnesses:
                                witness.addMemory("perceive", f"{a} was just murdered by {agent} at {self.environment.get_area_from_coordinates(a.x, a.y)} {self.environment.get_location_from_coordinates(a.x, a.y)}", self.unix_to_strftime(unix_time), 9)

        agent.addMemory("decision",f"I decided to {decision} because {explanation}",self.unix_to_strftime(unix_time),random.randint(1,4))
        return agent

    def agent_action(self, agent, unix_time):
        if agent.status == "dead":
            return agent

        if agent.kind != 'zombie':
            # Recent memories importance > reflect_threshold, time to reflect
            if agent.recent_memories_importance() > self.reflect_threshold and self.allow_reflect_flag == 1:
                agent.reflect(self.unix_to_strftime(unix_time))

            agent.conversation_cooldown -= 1
            if agent.last_conversation is not None:
                if len(agent.last_conversation.messages) >= CONVERSATION_DEPTH:
                    other_agent = agent.last_conversation.other_agent

                    agent.summarize_conversation(self.unix_to_strftime(unix_time))
                    other_agent.summarize_conversation(self.unix_to_strftime(unix_time))

                    agent.conversation_cooldown = CONVERSATION_COOLDOWN
                    other_agent.conversation_cooldown = CONVERSATION_COOLDOWN

            if agent.is_locked_to_convo():
                agent.talk({ "other_agents": [agent.last_conversation.other_agent], "timestamp": self.unix_to_strftime(unix_time) })
                return agent

        perceived_agents, perceived_locations, perceived_areas, perceived_objects = agent.perceive([a for a in self.agents if a != agent], self.environment, self.unix_to_strftime(self.unix_time))

        if len(perceived_agents) > 0:
            other_agent = random.choice(perceived_agents)
            # Killing condition
            if "kill" in agent.actions and other_agent.status != "dead":
                if random.randint(0, 100) < agent.kill_rate - (5 * len(perceived_agents)):
                    agent.kill(other_agent, self.unix_to_strftime(unix_time))
                    if other_agent.status == "dead":
                        witnesses = (set(perceived_agents) - {other_agent})
                        for witness in witnesses:
                            witness.addMemory("perceive", f"{other_agent} was just murdered by {agent} at {self.environment.get_area_from_coordinates(other_agent.x, other_agent.y)} {self.environment.get_location_from_coordinates(other_agent.x, other_agent.y)}", self.unix_to_strftime(unix_time), 9)

                    return agent

            if agent.kind != 'zombie':
                # Talk Condition
                agents_can_hear = [a for a in perceived_agents if a.status != "dead" and a.kind != "zombie"]
                if len(agents_can_hear) > 0:
                    other_agent = random.choice(agents_can_hear)
                    if random.randint(0, 100) < agent.talk_rate and len(agents_can_hear) > 0:
                        agent.talk({ "target": other_agent.name, "other_agents": [other_agent], "timestamp": self.unix_to_strftime(unix_time) })
                        self.conversation_counter += 1
                        return agent

        if self.allow_movement == 1:
            if len(agent.destination_cache) == 0 or agent.current_destination is None:
                # Decide where to go
                agent.move({ "target": random.choice(agent.spatial_memory).name, "environment": self.environment })
            else:
                # Has current path to go
                agent.move({ "environment": self.environment })

        return agent  # Agent stays in the same position

    def print_agent_memories(self):
        for agent in self.agents:
            pd(f"\nMemories for {agent}:")
            for memory in agent.memory:
                pd(memory)

    def is_position_valid(self, position):
        # Check if the position is within the boundaries of the matrix
        if not (0 <= position[0] <= self.n and 0 <= position[1] <= self.n):
            return False

        try:
            if self.collisions[position[0]][position[1]] == 1:
                return False
        except Exception as e:
            return False

        return True

    def load_environment_from_json(self, agents_file, world_file):
        try:
            data = json.loads(world_file)
            data.update(json.loads(agents_file))
        except json.JSONDecodeError:
            with open(world_file, "r") as file:
                data = json.load(file)

            with open(agents_file, "r") as file:
                data.update(json.load(file))

        agents_data = data.get("agents", [])
        zombies_data = data.get("zombies", [])
        questions_data = data.get("questions", [])
        goals_data = data.get("goal", [])
        descriptions_data = data.get("possible_descriptions", [])
        self.n = max(data.get("width", 15), data.get("height", 15))
        self.simulation_steps = data.get("simulation_steps",SIMULATION_STEPS)
        self.collisions = data.get("collision", [])
        self.unix_time = data.get("unix_time", 1672502400) # January 1, 2024 default
        #self.id = data.get("simulation_id", "")

        location_data = data.get("location", [])
        for location in location_data:
            l_name = location.get("name", "Loc")
            l_description = location.get("description", "Desc")
            areas_data = location.get("areas", [])
            areas = []
            for area in areas_data:
                a_name = area.get("name", "Area")
                a_x = area.get("x", 0)
                a_y = area.get("y", 0)
                a_description = area.get("description", "Desc")

                objects_data = area.get("objects", [])
                objects = []
                for obj in objects_data:
                    o_name = obj.get("name", "Obj")
                    o_x = obj.get("x", 0)
                    o_y = obj.get("y", 0)
                    o_is_boundary = obj.get("is_boundary", True)
                    o_symbol = obj.get("symbol", "x")
                    objects.append(Object(o_name, o_x, o_y, o_is_boundary, "Object", o_symbol))

                areas.append(Area(a_name, a_x, a_y, a_description, objects))

            self.locations.append(Location(l_name, l_description, areas))

        for question in questions_data:
            self.interview_questions.append(question)

        for goal in goals_data:
            self.possible_goals.append(goal)

        for description in descriptions_data:
            self.possible_descriptions.append(description)
        # Load existing agents from the JSON file

        for agent_data in agents_data:
            name = agent_data.get("name", f"Agent{len(self.agents) + 1}")
            position = agent_data.get("position", (random.randint(0, self.n - 1), random.randint(0, self.n - 1)))

            while not self.is_position_valid(position):
                position = (random.randint(0, self.n - 1), random.randint(0, self.n - 1))

            description = agent_data.get("description")
            goal = agent_data.get("goal")
            retention = agent_data.get("retention",99)
            acceptance = agent_data.get("acceptance",99)
            invitation = agent_data.get("invitation",99)
            known_locations = agent_data.get("spatial_memory", [loc.name for loc in self.locations])
            actions_whitelist = agent_data.get("actions_whitelist", None)

            spatial_memory = []
            for loc in self.locations:
                if loc.name in known_locations:
                    spatial_memory.append(loc.getLocationTree())

            agent_dict_data = {
                "name": name,
                "description": description,
                "goal": goal,
                "position": position,
                "spatial_memory": spatial_memory,
                "retention": int(retention),
                "acceptance": int(acceptance),
                "invitation": int(invitation),
                "sim_id": self.id
            }

            agent = Agent(agent_dict_data)

            if actions_whitelist:
                for action in actions_whitelist:
                    agent.actions.append(action)

            self.agents.append(agent)

        # Generate additional agents based on NUM_NPC
        num_additional_agents = max(self.num_npc, 0)
        for _ in range(num_additional_agents):
            name = self.generate_unique_name()
            specie = "human"
            position = self.generate_random_position()

            # if len(self.possible_goals) == 1:
            #     description = f"{random.choice(self.possible_descriptions)}"
            #     goal = self.possible_goals[0]
            # else:
            #     description, goal = random.choice(list(zip(self.possible_descriptions, self.possible_goals)))
            actions_whitelist = None
            known_locations = [loc.name for loc in self.locations]

            spatial_memory = []

            for loc in self.locations:
                if loc.name in known_locations:
                    spatial_memory.append(loc.getLocationTree())

            agent_dict_data = {
                "name": name,
                "specie": specie,
                "position": position,
                "spatial_memory": spatial_memory,
                "sim_id": self.id
            }

            agent = Agent(agent_dict_data)

            if actions_whitelist:
                for action in actions_whitelist:
                    agent.actions.append(action)

            self.agents.append(agent)

        for zombie_data in zombies_data:
            name = zombie_data.get("name", f"Zombie {sum(agent.specie == 'zombie' for agent in self.agents) + 1}")
            position = self.generate_random_position()
            known_locations = zombie_data.get("spatial_memory", [loc.name for loc in self.locations])
            actions_whitelist = ["kill"]
            spatial_memory = []

            for loc in self.locations:
                if loc.name in known_locations:
                    spatial_memory.append(loc.getLocationTree())

            zombie_dict_data = {
                "name": name,
                "position": position,
                "spatial_memory": spatial_memory,
            }

            zombie = Npc(zombie_dict_data)

            if actions_whitelist:
                for action in actions_whitelist:
                    zombie.actions.append(action)

            self.agents.append(zombie)

        num_of_zombies = max(self.num_zombies, 0)
        for _ in range(num_of_zombies):
            name = f"Zombie {sum(agent.specie == 'zombie' for agent in self.agents) + 1}"
            position = self.generate_random_position()
            known_locations = [loc.name for loc in self.locations]
            actions_whitelist = ["kill"]

            spatial_memory = []

            for loc in self.locations:
                if loc.name in known_locations:
                    spatial_memory.append(loc.getLocationTree())

            zombie_dict_data = {
                "name": name,
                "position": position,
                "spatial_memory": spatial_memory,
            }

            zombie = Npc(zombie_dict_data)

            if actions_whitelist:
                for action in actions_whitelist:
                    zombie.actions.append(action)


            self.agents.append(zombie)

    # Add a helper method to generate a random valid position
    def generate_random_position(self):
        position = (random.randint(1, self.n - 2), random.randint(1, self.n - 2))
        while not self.is_position_valid(position):
            position = (random.randint(1, self.n - 2), random.randint(1, self.n - 2))
        return position

    # Add a helper method to generate a unique name
    def generate_unique_name(self):
        existing_names = {agent.name for agent in self.agents}
        available_names = list(set(FIRST_NAMES) - existing_names)
        print(f"Available Names: {available_names}")
        if available_names:
            chosen_name = random.choice(available_names)
            print(f"Chosen Name: {chosen_name}")
            return chosen_name
        else:
            new_name = f"Agent{len(self.agents) + 1}"
            print(f"New Name: {new_name}")
            return new_name

    def run_interviews(self):
        if self.interview_questions:
            dead_agents = [agent for agent in self.agents if (agent.status == "dead" and agent.kind != "zombie")]
            living_agents = [agent for agent in self.agents if (agent.status != "dead" and agent.kind != "zombie")]

            for agent in dead_agents + living_agents:
                results = []
                for question in self.interview_questions:
                    metric = question.get("metric", None)
                    #if agent.status == "dead":
                    #    pd(f"{agent} dead, can't ask questions")
                    #    results.append("Agent is dead, cannot answer questions")
                    #elif question["who"] == "all" or question["who"] == agent.name:
                    answer = agent.answer(question["question"])
                    if metric:
                        match = re.search(r"Answer: (\d)", answer)
                        if match:
                            score = int(match.group(0))
                        else:
                            score = 0
                        self.performance_metrics[metric] += score
                    answer_data = {
                        "question": question["question"],
                        "answer": answer
                    }
                    results.append(answer_data)
                self.interview_results[agent.name] = results

    def print_matrix(self):
        cell_width = 15  # Adjust this value based on your needs
        matrix = [[" " * cell_width for _ in range(self.environment.width)] for _ in range(self.environment.height)]

        # Print agents
        for agent in self.agents:
            matrix[agent.x][agent.y] = "{:<{width}}".format(f"{agent.direction} * {agent.name}", width=cell_width)

        #sys.stdout.write("\033[H")
        print("\n\n")
        for row in matrix:
            print("|".join(row))
            print("-" * (cell_width * self.n - 1))

    def get_all_objects(self):
        all_objects = [obj for loc in self.locations for area in loc.areas for obj in area.objects]
        return all_objects

    def get_arr_2D(self):
        arr_2D = [["" for _ in range(self.environment.width)] for _ in range(self.environment.height)]
        objs = [obj for location in self.environment.locations for area in location.areas for obj in area.objects]

        for x in range(self.environment.height):
            for y in range(self.environment.width):
                for obj in objs:
                    if obj.bounds[x][y] != 0:
                        arr_2D[x][y] = obj.name[0].lower()

        for agent in self.agents:
            arr_2D[agent.x][agent.y] = f"{agent}"

        return arr_2D

    def clear_redis(self):
        redis_connection.delete(f"{self.id}:matrix_state")
        redis_connection.delete(f"{self.id}:matrix_states")
        redis_connection.delete(f"{self.id}:agent_conversations")
        for a in self.agents:
            redis_connection.delete(f"{self.id}:conversations:{a.name}")
            redis_connection.delete(f"{self.id}:events:{a.name}")
            redis_connection.delete(f"{self.id}:agents:{a.name}")

matrix = None

def main():
    global matrix
    #Base.metadata.create_all(engine)
    # Parse Args
    parser = argparse.ArgumentParser(description='Matrix Simulation')
    #parser.add_argument('--agents', kind=str, default='configs/def_environment.json', help='Path to the env file')
    #parser.add_argument('--world', kind=str, default='configs/def_environment.json', help='Path to the env file')
    parser.add_argument('--scenario', type=str, default='configs/def.json', help='Path to the scenario file')
    parser.add_argument('--environment', type=str, default='configs/largev2.tmj', help='Path to the env file')
    parser.add_argument('--id', type=str, default='', help='Custom Simulation ID')
    args = parser.parse_args()

    #matrix_data = {"agents_file":args.agents, "world_file":args.world}
    #matrix = Matrix(matrix_data)
    if args.id != '':
        matrix = Matrix({ "scenario": args.scenario, "environment": args.environment, "id": args.id })
    else:
        matrix = Matrix({ "scenario": args.scenario, "environment": args.environment })
    # matrix.send_matrix_to_redis()

    pd(f"model:#{MODEL}")
    pd("Initial Agents Positions:")
    redis_connection.set(f"{matrix.id}:matrix_state", json.dumps(matrix.get_arr_2D()))

    # Clear convos
    matrix.clear_redis()

    # Run
    start_time = datetime.now()

    #matrix.run()
    matrix.run_singlethread()
    end_time = datetime.now()
    matrix.run_interviews()

    # Log Runtime
    matrix.simulation_runtime = end_time - start_time
    matrix.send_matrix_to_redis()

    # Save the environment state to a file for inspection
    if matrix.id is not None and matrix.id != '' and RUN_REPORTS != 0:
        save_report(matrix)
    #session.commit()

def signal_handler(signum, frame):
    global matrix,last_interrupt_time, ctrl_c_count
    current_time = time.time()
    #TODO on first control-c, run interview questions then quit, we need to pause the simulation
    if current_time - last_interrupt_time < 2:
        ctrl_c_count += 1
        if ctrl_c_count > 1 :
            pd("Exiting...")
            exit(0)
        else:
            pass

    else:
        ctrl_c_count = 1
        pd("stopping matrix, please wait for current step to finish")
        pd("*"*50)
        matrix.status = "stop"
        matrix.send_matrix_to_redis()
    last_interrupt_time = current_time

ctrl_c_count = 0
last_interrupt_time = time.time()
signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    main()

