import unittest
import argparse
from datetime import datetime
from src.agents import Agent
from src.memory import Memory
from src.environment import Environment
from src.conversation import Conversation
from utils.utils import *
from engine import Matrix
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import random
import re

class TestMemoryFunctions(unittest.TestCase):
    def test_memory(self):
        agent_data = {
            "name": "John",
            "description": "You are a simulated persona.",
            "goal": "Answer questions, think, be rational.",
        }
        agent = Agent(agent_data)

        unix_time = 1704067200
        try:
            with open('tests/input_memory.txt', 'r') as file:
                for mem in file:
                    timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
                    agent.addMemory("test", mem, timestamp, random.randint(0, 9))
                    unix_time = unix_time + 10
        except Exception as e:
            print(f"Error {e}")

        for mem in agent.memory:
            print(mem)
        self.assertTrue(len(agent.memory) > 0)

    def test_eval(self):
        agent1_data = {
            "name": "John",
            "description": "software engineer",
            "goal": "have a hello kitty themed party",
            #"meta_questions": ["how can I be more like Elon Musk?"],
        }
        agent2_data = {
            "name": "Paul",
            "description": "bar tender",
        }
        agent1 = Agent(agent1_data)
        agent2 = Agent(agent2_data)

        unix_time = 1704067200
        try:
            with open('tests/input_memory.txt', 'r') as file:
                for mem in file:
                    timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
                    #agent1.addMemory("test", mem, timestamp, (CLEAR_TEST_MEMORIES != 1))
                    unix_time = unix_time + 10
        except Exception as e:
            print(f"Error {e}")

        timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
        agent1.evaluate_progress(timestamp)

    def test_askmetaquestions(self):
        agent1_data = {
            "name": "John",
            "description": "software engineer",
            "goal": "have a hello kitty themed party",
        }
        agent2_data = {
            "name": "Paul",
            "description": "bar tender",
        }
        agent1 = Agent(agent1_data)
        agent2 = Agent(agent2_data)

        # if random <  1 always happen
        unix_time = 1704067200
        try:
            with open('tests/input_memory.txt', 'r') as file:
                for mem in file:
                    timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
                    #agent1.addMemory("test", mem, timestamp, (CLEAR_TEST_MEMORIES != 1))
                    unix_time = unix_time + 10
        except Exception as e:
            print(f"Error {e}")

        timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
        agent1.ask_meta_questions(timestamp)
        #agent2.ask_meta_questions(timestamp)


        print(f"====== DATA FOR {agent1} ======\nMEMORIES:")
        for (i, mem) in enumerate(agent1.memory):
            print(f"{i}: {mem}")
        print(f"QUESTIONS:")
        for (i, q) in enumerate(agent1.meta_questions):
            print(f"{i}: {q}")


    def test_metacognition(self):
        agent1_data = {
            "name": "John",
            "description": "software engineer",
            "goal": "have a hello kitty themed party",
            #"meta_questions": ["how can I be more like Elon Musk?"],
        }
        agent2_data = {
            "name": "Paul",
            "description": "bar tender",
        }
        agent1 = Agent(agent1_data)
        agent2 = Agent(agent2_data)

        #agent1.connections.append(str(agent2))
        #agent2.connections.append(str(agent1))
        # if random <  1 always happen
        unix_time = 1704067200
        try:
            with open('tests/input_memory.txt', 'r') as file:
                for mem in file:
                    timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
                    #agent1.addMemory("test", mem, timestamp, (CLEAR_TEST_MEMORIES != 1))
                    unix_time = unix_time + 10
        except Exception as e:
            print(f"Error {e}")

        timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
        agent1.meta_cognize(timestamp,True)
        for i in range(2):
            timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
            agent1.talk({ "target": agent2.name, "other_agents": [agent2], "timestamp": timestamp })
            agent2.talk({ "target": agent1.name, "other_agents": [agent1], "timestamp": timestamp })

            # matrix.print_matrix()
            unix_time = unix_time + 10

        #takes memories and returns questions
        #agent.meta_reflect(timestamp, True)

        # print(agent.memory)
        for mem in agent1.memory:
            print(mem)
        for q in agent1.meta_questions:
            print(q)
        #self.assertTrue(len(agent1.memory) > 0)

    def test_reflection(self):
        agent_data = {
            "name": "John",
            "description": "You are a simulated persona.",
            "goal": "Answer questions, think, be rational.",
        }
        agent = Agent(agent_data)
        unix_time = 1704067200
        try:
            with open('tests/input_memory.txt', 'r') as file:
                for mem in file:
                    timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
                    agent.addMemory("test", mem, timestamp, random.randint(0, 9))
                    unix_time = unix_time + 10
        except Exception as e:
            print(f"Error {e}")

        agent.reflect(timestamp, True)
        # agent.reflect_old(timestamp, True)

        # print(agent.memory)
        for mem in agent.memory[-15:]:
            print(mem)
        self.assertTrue(len(agent.memory) > 0)

    def test_relevance(self):
        context = "dog car driving"
        agent_data = {
            "name": "John",
            "description": "You are a simulated persona.",
            "goal": "Answer questions, think, be rational.",
        }
        agent = Agent(agent_data)

        unix_time = 1704067200
        try:
            with open('tests/input_memory.txt', 'r') as file:
                for mem in file:
                    timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
                    agent.addMemory("test", mem, timestamp, random.randint(0, 9))
                    unix_time = unix_time + 10
        except Exception as e:
            print(f"Error {e}")

        context_embedding = llm.embeddings(context)
        memories = agent.getMemories(context, timestamp)

        print(f"Context: {context}")
        for mem in memories:
            print(f"Current Memory: {mem}")
        self.assertTrue(len(memories) > 0)

    def test_embeddings(self):
        context = "travel"
        agent_data = {
            "name": "John",
            "description": "You are a simulated persona.",
            "goal": "Answer questions, think, be rational.",
        }
        agent = Agent(agent_data)

        unix_time = 1704067200
        try:
            with open('tests/input_memory.txt', 'r') as file:
                for mem in file:
                    if mem.startswith('#'):
                        continue
                    timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
                    agent.addMemory("test", mem.strip(), timestamp, random.randint(0, 9))
                    unix_time = unix_time + 10
        except Exception as e:
            print(f"Error {e}")

        context_embedding = llm.embeddings(context)
        sorted_memory = sorted(agent.memory,
                              key=lambda mem: Memory.calculateRelevanceScore(mem.embedding, context_embedding),
                              reverse=True)

        print(f"Context: {context}")
        for mem in sorted_memory:
            print(f"Current Memory: {mem}")
            print(f"Relevance Score: {Memory.calculateRelevanceScore(mem.embedding, context_embedding)}")
        self.assertTrue(len(sorted_memory) > 0)

    def test_talk(self):
        agent1_data = {
            "name": "Viktor",
            "description": "You love physics",
            "goal": "Answer questions, think, be rational.",
        }

        agent2_data = {
            "name": "Natasha",
            "description": "You love art",
            "goal": "Answer questions, think, be rational.",
        }
        agent1 = Agent(agent1_data)
        agent2 = Agent(agent2_data)

        agent1.connections.append(str(agent2))
        agent2.connections.append(str(agent1))

        unix_time = 1704067200

        for i in range(5):
            timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
            agent1.talk({ "target": "Natasha", "other_agents": [agent2], "timestamp": timestamp })
            agent2.talk({ "target": "Viktor", "other_agents": [agent1], "timestamp": timestamp })

            # matrix.print_matrix()
            unix_time = unix_time + 10

    def test_llmaction(self):
        matrix_data = {
            "scenario": "configs/def.json",
            "environment": "configs/largev2.tmj",
            "id": "test-id",
            "llm_action": 1,
            "allow_plan": 0,
            "allow_reflect": 0
        }

        matrix = Matrix(matrix_data)

        for i in range(2):  # Assuming 10 steps for the test
            #matrix.print_matrix()
            for agent in matrix.agents:
                agent = matrix.llm_action(agent, matrix.unix_time)

            matrix.unix_time = matrix.unix_time + 10

    def test_location(self):
        """
        The test will make the agent walk from front of House A1 to House A5.
        The agent should learn House A1 to House A5 and Town
        """
        agent_data = {
            "name": "John",
            "description": "You are a simulated persona.",
            "goal": "Answer questions, think, be rational.",
            "x": 20,
            "y": 17
        }

        path_to_walk = [(20, 17), (20, 18), (20, 19), (20, 20), (20, 21), (20, 22), (20, 23), (20, 24), (20, 25), (20, 26), (20, 27), (20, 28), (20, 29), (20, 30), (20, 31), (20, 32), (20, 33), (20, 34), (20, 35), (20, 36), (20, 37), (20, 38), (20, 39), (20, 40), (20, 41), (20, 42), (20, 43), (20, 44), (20, 45), (20, 46), (20, 47), (20, 48), (20, 49), (20, 50), (20, 51), (20, 52), (20, 53), (20, 54), (20, 55), (20, 56)]
        agent = Agent(agent_data)
        environment = Environment({ "filename": "configs/largev2.tmj" })
        agent.destination_cache = path_to_walk
        for loc in environment.locations:
            if loc.name == "House A5":
                agent.current_destination = loc
                break

        print("Agent Spatial Memories at start:")
        for loc in agent.spatial_memory:
            print(f"{loc.name}")
            for area in loc.areas:
                print(f"\t-{area.name}")
                for obj in area.objects:
                    print(f"\t\t-{obj.name}")

        for i in path_to_walk:
            agent.perceive([], environment, "2023-01-01 00:00:00")
            agent.move({ "environment": environment })


        print("\nAgent Spatial Memories at end:")
        for loc in agent.spatial_memory:
            print(f"{loc.name}")
            for area in loc.areas:
                print(f"\t-{area.name}")
                for obj in area.objects:
                    print(f"\t\t-{obj.name}")

        agent.answer("What are the locations you discovered?")

    def test_speed(self, test_vllm=False):
        if test_vllm:
            AVAILABLE_MODELS = VLLM_MODELS + ["mistral", "orca-mini"]
        else:
            AVAILABLE_MODELS = ["mistral", "orca-mini"]
        MODEL_TIMES = []
        prompt = """
Your name is Alice
Description: Alice loves exploring.; Alice loves hanging out at the park;
Goal: Alice wants to find friend that will hang out at the Park with her.;

Memory 1:
2023-01-01 00:00:00 - Alice saw Charlie

Memory 1:
2023-01-01 00:00:00 - Charlie said to Alice: "Hello Alice"

Currently, Alice is in House A1 and perceives the following:
Charlie, Bed, Closet

Alice knows these places:
House A1, Park

Alice can choose to do one of the following:
move, talk, stay

What will Alice do? Give explanation and provide the answer. Can only choose 1 action towards 1 person at a time. Format your answer like these:

Examples:

Explanation: George will talk to Anne because he is trying to make new friends.
Answer: talk Anne

Explanation: George will kill Anne because she is alone and this is the perfect chance.
Answer: kill Anne

Explanation: George will stay because because he is too shy to do anything.
Answer: stay

Explanation: George will move because he needs to be at the Park at 18:00.
Answer: move Park
        """
        for model in AVAILABLE_MODELS:
            print(f"Creating LLM Instance for model: {model}")
            new_llm = Llm(model=model)
            start_time = time.time()
            for i in range(10):
                new_llm.generate(prompt)
            end_time = time.time()
            print(f"Deleting LLM Instance for model: {model}")
            del new_llm
            MODEL_TIMES.append({ model: end_time - start_time })

        for time_log in MODEL_TIMES:
            print(f"{time_log}")

    def test_thread(self):
        agent_data = {
            "name": "John",
            "description": "You are a simulated persona.",
            "goal": "Answer questions, think, be rational."
        }
        agent1 = Agent(agent_data)
        agent_data = {
            "name": "Michael",
            "description": "You are a simulated persona.",
            "goal": "Answer questions, think, be rational."
        }
        agent2 = Agent(agent_data)
        environment = Environment()
        print("Agent 1 memory before")
        print(agent1.short_memory)
        print("Agent 2 memory before")
        print(agent2.short_memory)
        for i in range(10):
            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                print("Agent 1 memory during")
                print(agent1.short_memory)
                print("Agent 2 memory during")
                print(agent2.short_memory)
                timestamp = "2023-12-08 21:30:40"
                futures = []
                futures.append(executor.submit(agent1.talk, { "target": agent2.name, "other_agents": [agent2], "timestamp": timestamp }))
                futures.append(executor.submit(agent2.talk, { "target": agent1.name, "other_agents": [agent1], "timestamp": timestamp }))
                results = [future.result() for future in futures]

        print("Agent 1 memory after")
        print(agent1.short_memory)
        print("Agent 2 memory after")
        print(agent2.short_memory)

    def test_agent_decision_zombie(self):
        matrix_data = {
            "scenario": None,
            "environment": "configs/largev2.tmj",
            "id": "test-agent-decision-zombie",
            "llm_action": 1,
            "allow_plan": 0,
            "allow_reflect": 0
        }

        matrix = Matrix(matrix_data)
        matrix.interview_questions = [{"who": "all", "question": "Is the park a safe place?" }, {"who": "all", "question": "What do you plan to do now?" }]

        agent_data = {
            "name": "John",
            "kind": "human",
            "description": "Town is now zombie infested. You live at House A1.",
            "goal": "Survive.",
            "x": 36, "y": 87 # This is just outside park
        }
        zombie_data = {
            "name": "Zombie",
            "kind": "zombie",
            "x": 36, "y": 93 # This is just inside park
        }
        agent = Agent(agent_data)
        zombie = Agent(zombie_data)

        agent.matrix = matrix
        zombie.matrix = matrix

        for loc in matrix.environment.locations:
            if loc.name == "Park" or loc.name == "House A1":
                agent.spatial_memory.append(loc)
            if loc.name == "Park":
                agent.current_destination = loc
                zombie.current_destination = loc
            zombie.spatial_memory.append(loc)

        agent.destination_cache = [(36, 88), (36, 89), (36, 90)]
        zombie.destination_cache = [(36, 93), (36, 93), (36, 93)]

        agent.addMemory("reflect", f"{matrix.unix_to_strftime(matrix.unix_time)} - {agent} wants to check if the Park is a safe place to go to or no.", matrix.unix_to_strftime(matrix.unix_time), 9)

        matrix.agents.append(agent)
        matrix.agents.append(zombie)
        for i in range(10):
            for a in matrix.agents:
                if matrix.llm_action_flag == 1 and a.kind != 'zombie':
                    matrix.llm_action(a, matrix.unix_time)
                else:
                    matrix.agent_action(a, matrix.unix_time)

            matrix.unix_time = matrix.unix_time + 10

        for a in matrix.agents:
            print(a.__str__(verbose=True))

        matrix.run_interviews()

    def test_summary(self):
        agent1_data = {
            "name": "Natasha",
            "description": "Natasha is confident and loves sports. Natasha lives at 'House B1'.",
            "goal": "Natasha is planning to host a Christmas Party with her friends. Natasha decides on the location and time of the party. Natasha's mission is to extend invitations to every person encountered, fostering a joyous gathering filled with laughter, music, and festive cheer. Additionally, Natasha will encourage others to join in the celebration and invite their acquaintances, creating an unforgettable experience for everyone involved."
        }
        agent2_data = {
            "name": "James"
        }

        conversation_arr = [
            '''2023-12-08 21:30:40 - Natasha said to James: "James, I'm hosting a Christmas party at House B1. Would you and your friends be interested in joining us?"''',
            '''2023-12-08 21:30:40 - James said to Natasha: I'd be happy to attend, Natasha. Thank you for inviting us. Paul and I will make sure to be there.''',
            '''2023-12-08 21:30:50 - Natasha said to James:  2023-12-08 21:35:00 - I'm glad you can make it, James. Looking forward to a wonderful Christmas party at House B1 with you and Paul. Let me know if there's anything specific you or your friends would like to contribute to the celebration.''',
            '''2023-12-08 21:30:50 - James said to Natasha:  I'll let Natasha know if Paul and I bring anything for the party. Thanks for asking, Natasha.''',
            '''2023-12-08 21:31:00 - Natasha said to James:  I'm glad you both can make it, James. Looking forward to your contribution to the Christmas party at House B1. Let me know if there's anything specific Paul and you would like to bring.'''
        ]

        agent1 = Agent(agent1_data)
        agent2 = Agent(agent2_data)

        new_convo = Conversation(agent1, agent2, conversation_arr)
        print(f"=========== Conversation summary for {agent1.name}")
        agent1.last_conversation = new_convo
        agent1.summarize_conversation("2023-12-08 21:31:00")

def main():
    parser = argparse.ArgumentParser(description='Matrix Test Suite')
    parser.add_argument('--all', action='store_true', help='Enable all test flag')
    parser.add_argument('--test', type=str, default='all', help='Context for relevance score test')
    parser.add_argument('--context', type=str, default='racing', help='Context for relevance score test')
    parser.add_argument('--history', action='store_true', help='Agents know each other flag')
    parser.add_argument('--steps', type=int, default=10, help='Steps for llm_action test.')
    args = parser.parse_args()

    if args.test and args.test != "all":
        suite = unittest.TestLoader().loadTestsFromName(f"test.TestMemoryFunctions.{args.test}")
    elif args.test == "all" or args.all:
        suite = unittest.TestLoader().loadTestsFromTestCase(TestMemoryFunctions)
    else:
        print("No valid test specified.")
        return

    runner = unittest.TextTestRunner()
    result = runner.run(suite)

    # Access test results
    print("Tests run:", result.testsRun)
    print("Errors:", len(result.errors))
    print("Failures:", len(result.failures))

if __name__ == '__main__':
    main()
