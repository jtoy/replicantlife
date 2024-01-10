import random
from datetime import datetime
import concurrent.futures
import sys
import time
import json
import redis
import requests
import signal
import argparse
from concurrent.futures import ThreadPoolExecutor

from utils.utils import *
from utils.names import FIRST_NAMES
from src.agents import Agent
from src.npc import Npc
#from src.objects import Object
from src.location import Location, Area, Object


class Matrix:
#class Matrix(Base):
    if False:
        __tablename__ = 'simulations'

        id = Column(String, primary_key=True)
        n = Column(Integer)
        num_agents = Column(Integer)
        percecption_range = Column(Integer)
        #objects = Column(PickleType)
        world = Column(PickleType)
        agents = relationship('Agent', back_populates='simulation')
        allow_movement = Column(Integer)
        model = Column(String)
        env_file = Column(String)
        simulation_runtime = Column(Float)
        unix_time = Column(Integer)

    def __init__(self, matrix_data):
        self.id = str(uuid.uuid4())
        self.n = MATRIX_SIZE
        self.num_agents = NUM_AGENTS
        self.num_zombies = NUM_ZOMBIES
        self.perception_range = PERCEPTION_RANGE
        #self.objects = []
        self.locations = []
        self.collisions = []
        self.agents = []
        self.allow_movement = ALLOW_MOVEMENT
        self.agents_file = matrix_data.get("agents_file")
        self.world_file = matrix_data.get("world_file")
        self.simulation_steps = SIMULATION_STEPS
        self.model = llm.model
        self.interview_questions = []
        self.possible_goals = []
        self.possible_descriptions = []
        self.sumulation_runtime = 0
        self.unix_time = None
        self.death = False
        self.llm = "mistral"
        self.total_llm_calls = 0
        self.llm_calls = 0
        self.status = "run"

        if self.agents_file and self.world_file:
            self.load_environment_from_json(self.agents_file, self.world_file)
        else:
            self.agents = [
                Agent({
                    'name': f"Agent {i}",
                    'position': (random.randint(0, self.n - 1), random.randint(0, self.n - 1))
                }) for i in range(self.num_agents)
            ]

        #session.add(self)
        #session.commit()

    def send_matrix_to_redis(self):
        if TEST_RUN == 0:
            # Commit to redis for frontend view
            simulation_details = {
                "id": self.id,
                "map": self.world_file,
                "agents": self.agents_file,
                "date": datetime.now().isoformat(),
                "n": self.n,
                "status": self.status
            }

            redis_connection.set(f"{self.id}:simulations", json.dumps(simulation_details))

    def run_step_for_agent(self,agent,step):

        #pd(f"Step {step}:")
        redis_connection.lpush(f"{self.id}:agent_conversations", json.dumps(f"Step: {step + 1} | {self.unix_to_strftime(self.unix_time)}"))
        # Check if 12:00am, if so we make plans
        hours = datetime.fromtimestamp(self.unix_time).strftime("%H")
        minutes = datetime.fromtimestamp(self.unix_time).strftime("%M")
        seconds = datetime.fromtimestamp(self.unix_time).strftime("%S")
        # New day so update is_busy flag
        #for agent in self.agents:
        if agent.specie != "zombie":
            if hours == "00" and minutes == "00" and seconds == "00":
                agent.make_plans(self.unix_to_strftime(self.unix_time))
            if agent.recent_memories_importance() > 100:
                agent.reflect(self.unix_to_strftime(self.unix_time))
            # Submit agent actions concurrently
            if LLM_ACTION == 1 and agent.specie != "zombie":
                self.llm_action(agent,self.unix_time)
            else:
                self.agent_action(agent,self.unix_time)
        # Retrieve results from futures
        #updated_agents = [future.result() for future in futures]
        # Update the agents' states. Reflect
        #for i, updated_agent in enumerate(updated_agents):
        #    self.agents[i].__dict__.update(updated_agent.__dict__)


    def run(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            for step in range(self.simulation_steps):
                if self.status == "stop":
                    pd("stopping simulation")
                    break
                start_time = time.time()
                futures = [executor.submit(self.run_step_for_agent, agent, step) for agent in self.agents]
                concurrent.futures.wait(futures)
                end_time = time.time()
                self.unix_time = self.unix_time + 10
                self.llm_calls = llm.call_counter - self.total_llm_calls
                self.total_llm_calls += self.llm_calls
                print(f"LLm calls for Step {step}: {self.llm_calls} calls")
                print(f"Step {step} ran in {end_time - start_time}")
                if PRINT_MAP == 1:
                    self.print_matrix()
                redis_connection.set(f"{self.id}:matrix_state", json.dumps(self.get_arr_2D()))
                if SLEEP_STEP and SLEEP_STEP > 0:
                    time.sleep(SLEEP_STEP)

        average_llm_calls = self.total_llm_calls / (step + 1)
        self.print_agent_memories()
        pd(f"made it to step {step}")
        pd(f"Total LLM calls: {self.total_llm_calls} calls | Average LLM calls: {average_llm_calls} calls")

    def unix_to_strftime(self, unix_time):
        return datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")

    def step(self):
        for agent in self.agents:
            if agent.status == "active":
                agent_action_result = self.agent_action(agent)
                agent.__dict__.update(agent_action_result.__dict__)  # Update agent's state

    def llm_action(self, agent, unix_time):
        agent.conversation_cooldown = agent.conversation_cooldown - 1
        while agent.is_busy:
            print(f"{agent} is busy, wait 1 second")
            time.sleep(1)
        
        perceived_agents = [a for a in self.agents if agent.perceive(a, self.perception_range, self.collisions, self.unix_to_strftime(self.unix_time))]
        perceived_objects = [obj for location in self.locations for area in location.areas for obj in area.objects if agent.perceive(obj, self.perception_range, self.collisions, self.unix_to_strftime(self.unix_time))]

        # Get agent's current location
        # TODO Implement a better checking for current location
        current_location = "unknown location" 

        # Perceive new locations in here
        for loc in self.locations:
            # Only inspect locations not in agent's spatial memory
            if not loc.getLocationTree() in agent.spatial_memory:
                for area in loc.areas:
                    if agent.perceive(area, self.perception_range, self.collisions, self.unix_to_strftime(self.unix_time)):
                        # Agent discovered new Area
                        agent.spatial_memory.append(loc.getLocationTree())
                        current_location = loc.name
                        interaction = f"{self.unix_to_strftime(self.unix_time)} - {agent} discovered new location: {loc.name}"
                        redis_connection.lpush(f"{self.id}:agent_conversations", json.dumps(f"{interaction}"))

                        agent.addMemory("observation", interaction, self.unix_to_strftime(self.unix_time))

        variables = {
            "current_location": current_location,
            "perceived_agents": [a.name for a in perceived_agents],
            "perceived_objects": [obj.name for obj in perceived_objects]
        }

        decision = agent.decide(variables, self.unix_to_strftime(self.unix_time))
        decision_answer = decision.split("Answer: ", 1)[-1].strip() if "Answer: " in decision else "" 
        split_answer = decision_answer.split("Answer: ", 1)[-1].strip().split(maxsplit=1)

        try:
            choice = split_answer[0]
            params = split_answer[1] if len(split_answer) > 1 else ""
        except Exception as e:
            choice = "stay"
            params = ""
        print(f"Choice: {choice}, Params: {params}")

        if choice == "move":
            if params == "":
                print("invalid destination")
                return agent
            old_position = (agent.x, agent.y)
            new_position = agent.move_to(self.n, self.collisions, params, self.unix_to_strftime(self.unix_time))

            # Check if the new position is valid
            if self.is_position_valid(new_position):
                # Determine the direction the agent is moving
                if old_position[0] < new_position[0]:
                    agent.direction = "down"
                elif old_position[0] > new_position[0]:
                    agent.direction = "up"
                elif old_position[1] < new_position[1]:
                    agent.direction = "right"
                elif old_position[1] > new_position[1]:
                    agent.direction = "left"
                agent.x = new_position[0]
                agent.y = new_position[1]
                return agent

            else:
                pd("invalid position")
                return agent

        elif choice == "continue":
            old_position = (agent.x, agent.y)
            new_position = agent.move_to(self.n, self.collisions, agent.destination, self.unix_to_strftime(self.unix_time))

            # Check if the new position is valid
            if self.is_position_valid(new_position):
                # Determine the direction the agent is moving
                if old_position[0] < new_position[0]:
                    agent.direction = "down"
                elif old_position[0] > new_position[0]:
                    agent.direction = "up"
                elif old_position[1] < new_position[1]:
                    agent.direction = "right"
                elif old_position[1] > new_position[1]:
                    agent.direction = "left"
                agent.x = new_position[0]
                agent.y = new_position[1]
                return agent

        elif choice == "kill":
            other_agent = next((a for a in self.agents if a.name in params), None)
            agent.kill(other_agent, self.unix_to_strftime(unix_time))

            if other_agent.status == "dead":
                witnesses = (set(perceived_agents) - {other_agent})
                for witness in witnesses:
                    witness.addMemory("perceive", f"{other_agent} was just murdered", self.unix_to_strftime(unix_time))

        elif choice == "talk":
            other_agent = next((a for a in self.agents if a.name in params), None)
            if other_agent is None:
                interaction = f"{self.unix_to_strftime(self.unix_time)} - You can't with {params} at the moment."
                print(interaction)
                return agent
            if other_agent.conversation_cooldown > 0: 
                interaction = f"{self.unix_to_strftime(self.unix_time)} - {other_agent} is busy and can't talk with you right now."
                print(interaction)
            else:
                agent.talk(other_agent, self.unix_to_strftime(unix_time))
        else:
            print("stay")

        return agent

    def agent_action(self, agent, unix_time):
        while agent.is_busy:
            print(f"{agent} is busy, wait 1 second")
            time.sleep(1)

        perceived_agents = [a for a in self.agents if agent.perceive(a, self.perception_range, self.collisions, self.unix_to_strftime(self.unix_time))]
        #TODO this code doesnt take into action objects, need that
        #TODO add ability to dynamically choose from different situations
        if agent.status == "dead":
            return agent
        if perceived_agents:
            other_agent = random.choice(perceived_agents)
            if "kill" in agent.actions and other_agent.status != "dead":
                if random.randint (0,100) < 90 and "kill" in agent.actions:
                    agent.kill(other_agent,self.unix_to_strftime(unix_time))
                    if other_agent.status == "dead":
                        witnesses = (set(perceived_agents) - {other_agent})
                        for witness in witnesses:
                            witness.addMemory("perceive", f"{other_agent} was just murdered", self.unix_to_strftime(unix_time))
            elif other_agent.specie != "zombie" and other_agent.status != "dead" and (random.randint(0, 100) < agent.invitation or (agent.last_conversation is not None and other_agent.last_conversation is not None)):
                if agent.conversation_cooldown > 0:
                    agent.conversation_cooldown = agent.conversation_cooldown - 1
                    interaction = f"{self.unix_to_strftime(self.unix_time)} - {agent} ignored {other_agent}"
                    redis_connection.lpush(f"{self.id}:agent_conversations", json.dumps(f"{interaction}"))
                else:
                    agent.talk(other_agent, self.unix_to_strftime(unix_time))
                    return agent

        # Perceive new locations in here
        for loc in self.locations:
            # Only inspect locations not in agent's spatial memory
            if not loc.getLocationTree() in agent.spatial_memory:
                for area in loc.areas:
                    if agent.perceive(area, self.perception_range, self.collisions, self.unix_to_strftime(self.unix_time)):
                        # Agent discovered new Area
                        agent.spatial_memory.append(loc.getLocationTree())
                        interaction = f"{self.unix_to_strftime(self.unix_time)} - {agent} discovered new location: {loc.name}"
                        redis_connection.lpush(f"{self.id}:agent_conversations", json.dumps(f"{interaction}"))

                        agent.addMemory("observation", interaction, self.unix_to_strftime(self.unix_time))

        # Perceive Static Objects Here
        perceived_objects = [obj for location in self.locations for area in location.areas for obj in area.objects if agent.perceive(obj, self.perception_range, self.collisions, self.unix_to_strftime(self.unix_time))]

        for obj in perceived_objects:
            interaction = f"{self.unix_to_strftime(self.unix_time)} - {agent} saw a {obj.name}"
            redis_connection.lpush(f"{self.id}:agent_conversations", json.dumps(f"{interaction}"))

        if self.allow_movement == 1:
            old_position = (agent.x, agent.y)
            #new_position = agent.move(self.n, self.get_all_objects(), self.unix_to_strftime(self.unix_time))
            new_position = agent.move(self.n, self.collisions, self.unix_to_strftime(self.unix_time))

            # Check if the new position is valid
            if self.is_position_valid(new_position):
                # Determine the direction the agent is moving
                if old_position[0] < new_position[0]:
                    agent.direction = "down"
                elif old_position[0] > new_position[0]:
                    agent.direction = "up"
                elif old_position[1] < new_position[1]:
                    agent.direction = "right"
                elif old_position[1] > new_position[1]:
                    agent.direction = "left"
                agent.x = new_position[0]
                agent.y = new_position[1]
                return agent
            else:
                pd("invalid position")

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
            retention = agent_data.get("retention")
            acceptance = agent_data.get("acceptance")
            invitation = agent_data.get("invitation")
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

        # Generate additional agents based on NUM_AGENTS
        num_additional_agents = max(self.num_agents, 0)
        for _ in range(num_additional_agents):
            name = self.generate_unique_name()
            specie = "human"
            position = self.generate_random_position()

            if len(self.possible_goals) == 1:
                description = f"{random.choice(self.possible_descriptions)}"
                goal = self.possible_goals[0] 
            else:
                description, goal = random.choice(list(zip(self.possible_descriptions, self.possible_goals)))
            actions_whitelist = None
            known_locations = [loc.name for loc in self.locations]

            spatial_memory = []

            for loc in self.locations:
                if loc.name in known_locations:
                    spatial_memory.append(loc.getLocationTree())
            
            agent_dict_data = {
                "name": name,
                "specie": specie,
                "description": description,
                "goal": goal,
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
            dead_agents = [agent for agent in self.agents if (agent.status == "dead" and agent.specie != "zombie")]
            living_agents = [agent for agent in self.agents if (agent.status != "dead" and agent.specie != "zombie")]

            for agent in dead_agents + living_agents:
                for question in self.interview_questions:
                    if agent.status == "dead":
                        pd(f"{agent} dead, can't ask questions")
                    else:
                        agent.answer(question)

    def print_matrix(self):
        cell_width = 15  # Adjust this value based on your needs
        matrix = [[" " * cell_width for _ in range(self.n)] for _ in range(self.n)]

        # Print objects
        for obj in self.get_all_objects():
            try:
                matrix[obj.x][obj.y] = "{:<{width}}".format(obj.name, width=cell_width)
            except IndexError:
                print(f"Warning: Object {obj.name} is out of bounds and will be skipped.")

        # Print agents
        for agent in self.agents:
            matrix[agent.x][agent.y] = "{:<{width}}".format(f"{agent.direction} * {agent.name}", width=cell_width)

        for x in range(10):
            for y in range(10):
                if self.collisions[x][y] == 1:
                    matrix[x][y] = "{:<{width}}".format(f"Wall", width=cell_width)
        #sys.stdout.write("\033[H")
        print("\n\n")
        for row in matrix:
            print("|".join(row))
            print("-" * (cell_width * self.n - 1))

    def get_all_objects(self):
        all_objects = [obj for loc in self.locations for area in loc.areas for obj in area.objects]
        return all_objects

    def save_report(self, filename="change_to_sim_id.txt"):
        # total steps
        # total conversations
        # total agents
        # total dead
        # total time
        # total calls
        # time per calls
        # interview question results
        # all

        with open(filename, "w") as file:
            for agent in self.agents:
                file.write("\n".join(f"{agent.name}: {memory.content}" for memory in agent.memory))

    def get_arr_2D(self):
        arr_2D = [["" for _ in range(self.n)] for _ in range(self.n)]

        for obj in self.get_all_objects():
            try:
                arr_2D[obj.x][obj.y] = f"*{obj}"
            except IndexError:
                pd(f"Warning: Object {obj.name} is out of bounds and will be skipped.")

        for agent in self.agents:
            #arr_2D[agent.x][agent.y] = f"{agent.direction} * {agent}"
            arr_2D[agent.x][agent.y] = f"{agent}"

        return arr_2D

matrix = None

def main():
    global matrix
    Base.metadata.create_all(engine)
    # Parse Args
    parser = argparse.ArgumentParser(description='Matrix Simulation')
    parser.add_argument('--agents', type=str, default='configs/def_environment.json', help='Path to the env file')
    parser.add_argument('--world', type=str, default='configs/def_environment.json', help='Path to the env file')
    args = parser.parse_args()

    matrix_data = {"agents_file":args.agents, "world_file":args.world}
    matrix = Matrix(matrix_data)
    matrix.send_matrix_to_redis()

    pd(f"model:#{MODEL}")
    pd("Initial Agents Positions:")
    redis_connection.set(f"{matrix.id}:matrix_state", json.dumps(matrix.get_arr_2D()))
    if os.environ.get('PRINT_MAP', False):
        matrix.print_matrix()

    # Clear convos
    redis_connection.delete(f"{matrix.id}:agent_conversations")

    # Run
    start_time = time.time()
    matrix.run()
    end_time = time.time()
    matrix.run_interviews()

    # Log Runtime
    matrix.simulation_runtime = end_time - start_time
    #session.commit()

    # Save the environment state to a file for inspection
    matrix.save_report()


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

