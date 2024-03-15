"""
This module runs tests for the overall program.
"""

import unittest
import argparse
import concurrent.futures
import random

from datetime import datetime
from unittest.mock import MagicMock

from engine import Matrix
from utils.utils import *

from src.agents import Agent
from src.memory import Memory
from src.environment import Environment
from src.conversation import Conversation
from src.actions.fine_move_action import FineMoveAction


class TestMemoryFunctions(unittest.TestCase):
    """
    This class handles testing of memory functions.
    """

    def test_fine_move_action_direction(self):
        """
        This function tests the direction of the agent's move.
        """

        agent = MagicMock(x=0, y=0)
        FineMoveAction.act(agent, "up with random text")
        self.assertEqual(agent.x, 0)
        self.assertEqual(agent.y, -1)

    def test_fine_move_action_invalid_direction(self):
        """
        This function tests invalid direction of the agent's move.
        """

        agent = MagicMock(x=0, y=0)
        FineMoveAction.act(agent, "invalid-direction")
        self.assertEqual(agent.x, 0)
        self.assertEqual(agent.y, 0)

    def test_fine_move_action_moves_away(self):
        """
        This function tests agents to move away.
        """

        # real agent here, real zombie here. decide
        matrix = Matrix({"environment": "configs/small.tmj"})
        real_agent = Agent(
            {"name": "John", "actions": ["fine_move"], "x": 5, "y": 5, "matrix": matrix}
        )
        matrix.add_agent_to_simulation(real_agent)
        zombie = Agent(
            {
                "name": "Zombie",
                "kind": "zombie",
                "actions": ["kill"],
                "x": 6,
                "y": 5,
                "matrix": matrix,
            }
        )
        matrix.add_agent_to_simulation(zombie)
        matrix.llm_action(real_agent, matrix.unix_time)
        self.assertEqual(real_agent.x, 4)
    
    def test_matrix_runs_step(self):
        """
        This function tests if matrix runs a step successfully.
        (If yes, the pylint-fix branch can be merged).
        """

        matrix = Matrix(
            {"scenario":"configs/empty.json","environment":"configs/largev2.tmj"}
        )
        #run for one step
        matrix.steps = 1
        matrix.boot()
        matrix.run_singlethread()
        self.assertTrue(len(matrix.agents) > 0)
        self.assertEqual(matrix.status,"complete")

    def test_memory(self):
        """
        This function tests if an agent can have a memory.
        """

        agent_data = {
            "name": "John",
            "description": "You are a simulated persona.",
            "goal": "Answer questions, think, be rational.",
        }
        agent = Agent(agent_data)

        unix_time = 1704067200
        try:
            with open("tests/input_memory.txt", "r", encoding="utf-8") as file:
                for mem in file:
                    timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
                    agent.addMemory("test", mem, timestamp, random.randint(0, 9))
                    unix_time = unix_time + 10
        except Exception as e: # pylint: disable=broad-except
            print(f"Error {e}")

        for mem in agent.memory:
            print(mem)
        self.assertTrue(len(agent.memory) > 0)

    def test_eval(self):
        """
        This function tests the progress evaluation of the agent.
        """

        agent1_data = {
            "name": "John",
            "description": "software engineer",
            "goal": "have a hello kitty themed party",
            # "meta_questions": ["how can I be more like Elon Musk?"],
        }
        agent1 = Agent(agent1_data)

        # agent2_data = {
        #     "name": "Paul",
        #     "description": "bar tender",
        # }
        # agent2 = Agent(agent2_data)

        unix_time = 1704067200
        try:
            with open("tests/input_memory.txt", "r", encoding="utf-8") as file:
                for mem in file:
                    timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
                    # agent1.addMemory("test", mem, timestamp, (CLEAR_TEST_MEMORIES != 1))
                    unix_time = unix_time + 10
        except Exception as e: # pylint: disable=broad-except
            print(f"Error {e}")

        timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
        agent1.evaluate_progress(timestamp)

    def test_askmetaquestions(self):
        """
        This function tests the agent to ask meta questions.
        """

        agent1_data = {
            "name": "John",
            "description": "software engineer",
            "goal": "have a hello kitty themed party",
        }
        agent1 = Agent(agent1_data)

        # agent2_data = {
        #     "name": "Paul",
        #     "description": "bar tender",
        # }
        # agent2 = Agent(agent2_data)

        # if random <  1 always happen
        unix_time = 1704067200
        try:
            with open("tests/input_memory.txt", "r", encoding="utf-8") as file:
                for mem in file:
                    timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
                    # agent1.addMemory("test", mem, timestamp, (CLEAR_TEST_MEMORIES != 1))
                    unix_time = unix_time + 10
        except Exception as e: # pylint: disable=broad-except
            print(f"Error {e}")

        timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
        agent1.ask_meta_questions(timestamp)
        # agent2.ask_meta_questions(timestamp)

        print(f"====== DATA FOR {agent1} ======\nMEMORIES:")
        for i, mem in enumerate(agent1.memory):
            print(f"{i}: {mem}")
        print("QUESTIONS:")
        for i, q in enumerate(agent1.meta_questions):
            print(f"{i}: {q}")

    def test_metacognition(self):
        """
        This function tests the agent's metacognition.
        """

        agent1_data = {
            "name": "John",
            "description": "software engineer",
            "goal": "have a hello kitty themed party",
            # "meta_questions": ["how can I be more like Elon Musk?"],
        }
        agent2_data = {
            "name": "Paul",
            "description": "bar tender",
        }
        agent1 = Agent(agent1_data)
        agent2 = Agent(agent2_data)

        # agent1.connections.append(str(agent2))
        # agent2.connections.append(str(agent1))
        # if random <  1 always happen
        unix_time = 1704067200
        try:
            with open("tests/input_memory.txt", "r", encoding="utf-8") as file:
                for mem in file:
                    timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
                    # agent1.addMemory("test", mem, timestamp, (CLEAR_TEST_MEMORIES != 1))
                    unix_time = unix_time + 10
        except Exception as e: # pylint: disable=broad-except
            print(f"Error {e}")

        timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
        agent1.meta_cognize(timestamp, True)
        for _ in range(2):
            timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
            agent1.talk(
                {
                    "target": agent2.name,
                    "other_agents": [agent2],
                    "timestamp": timestamp,
                }
            )
            agent2.talk(
                {
                    "target": agent1.name,
                    "other_agents": [agent1],
                    "timestamp": timestamp,
                }
            )

            # matrix.print_matrix()
            unix_time = unix_time + 10

        # takes memories and returns questions
        # agent.meta_reflect(timestamp, True)

        # print(agent.memory)
        for mem in agent1.memory:
            print(mem)
        for q in agent1.meta_questions:
            print(q)
        # self.assertTrue(len(agent1.memory) > 0)

    def test_reflection(self):
        """
        This function tests the agent's reflections.
        """

        agent_data = {
            "name": "John",
            "description": "You are a simulated persona.",
            "goal": "Answer questions, think, be rational.",
        }
        agent = Agent(agent_data)
        unix_time = 1704067200
        try:
            with open("tests/input_memory.txt", "r", encoding="utf-8") as file:
                for mem in file:
                    timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
                    agent.addMemory("test", mem, timestamp, random.randint(0, 9))
                    unix_time = unix_time + 10
        except Exception as e: # pylint: disable=broad-except
            print(f"Error {e}")

        agent.reflect(timestamp, True)
        # agent.reflect_old(timestamp, True)

        # print(agent.memory)
        for mem in agent.memory[-15:]:
            print(mem)
        self.assertTrue(len(agent.memory) > 0)

    def test_relevance(self):
        """
        This function tests the relevance of
        agent's memories to a certain context.
        """

        context = "dog car driving"
        agent_data = {
            "name": "John",
            "description": "You are a simulated persona.",
            "goal": "Answer questions, think, be rational.",
        }
        agent = Agent(agent_data)

        unix_time = 1704067200
        try:
            with open("tests/input_memory.txt", "r", encoding="utf-8") as file:
                for mem in file:
                    timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
                    agent.addMemory("test", mem, timestamp, random.randint(0, 9))
                    unix_time = unix_time + 10
        except Exception as e: # pylint: disable=broad-except
            print(f"Error {e}")

        # context_embedding = llm.embeddings(context)
        memories = agent.getMemories(context, timestamp)

        print(f"Context: {context}")
        for mem in memories:
            print(f"Current Memory: {mem}")
        self.assertTrue(len(memories) > 0)

    def test_embeddings(self):
        """
        This function tests the agents to recognize context embeddings.
        """

        context = "travel"
        agent_data = {
            "name": "John",
            "description": "You are a simulated persona.",
            "goal": "Answer questions, think, be rational.",
        }
        agent = Agent(agent_data)

        unix_time = 1704067200
        try:
            with open("tests/input_memory.txt", "r", encoding="utf-8") as file:
                for mem in file:
                    if mem.startswith("#"):
                        continue
                    timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
                    agent.addMemory("test", mem.strip(), timestamp, random.randint(0, 9))
                    unix_time = unix_time + 10
        except Exception as e: # pylint: disable=broad-except
            print(f"Error {e}")

        context_embedding = llm.embeddings(context)
        sorted_memory = sorted(
            agent.memory,
            key=lambda mem: Memory.calculateRelevanceScore(mem.embedding, context_embedding),
            reverse=True,
        )

        print(f"Context: {context}")
        for mem in sorted_memory:
            print(f"Current Memory: {mem}")
            print(
                f"Relevance Score: "
                f"{Memory.calculateRelevanceScore(mem.embedding, context_embedding)}"
            )
        self.assertTrue(len(sorted_memory) > 0)

    def test_information_spreading(self):
        """
        This function tests spread of information among agents.
        """

        a1_data = {"name": "Viktor", "goal": "wants to throw a party next week"}
        a2_data = {"name": "John", "description": "loves art"}
        a3_data = {"name": "Paul", "description": "loves eating"}
        agent1 = Agent(a1_data)
        agent2 = Agent(a2_data)
        agent3 = Agent(a3_data)
        unix_time = 1704067200
        timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
        for _ in range(2):
            timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
            response = agent1.talk(
                {
                    "target": agent2.name,
                    "other_agents": [agent2],
                    "timestamp": timestamp,
                }
            )
            msg = f"{agent1} said to {agent2}: {response}"
            print(msg)
            response = agent2.talk(
                {
                    "target": agent1.name,
                    "other_agents": [agent1],
                    "timestamp": timestamp,
                }
            )
            msg = f"{agent2} said to {agent1}: {response}"
            print(msg)
            unix_time = unix_time + 10
        agent2.summarize_conversation(timestamp)
        print("*" * 20)
        for _ in range(2):
            timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
            response = agent2.talk(
                {
                    "target": agent3.name,
                    "other_agents": [agent3],
                    "timestamp": timestamp,
                }
            )
            msg = f"{agent2} said to {agent3}: {response}"
            print(msg)
            response = agent3.talk(
                {
                    "target": agent2.name,
                    "other_agents": [agent2],
                    "timestamp": timestamp,
                }
            )
            msg = f"{agent3} said to {agent2}: {response}"
            print(msg)
            unix_time = unix_time + 10
        agent3.summarize_conversation(timestamp)
        print(f"{agent2} memories")
        for mem in agent2.memory:
            print(mem)
        print(f"{agent3} memories")
        for mem in agent3.memory:
            print(mem)

    def test_talk_stranger(self):
        """
        This function tests agent's ability to talk to strangers.
        """

        agent1_data = {
            "name": "Viktor",
            "description": "You love physics, you hate talking to people",
            "goal": "Answer questions, think, be rational.",
        }
        agent2_data = {"name": "Natasha", "description": "You love art"}
        agent1 = Agent(agent1_data)
        agent2 = Agent(agent2_data)
        unix_time = 1704067200
        for _ in range(2):
            timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
            response = agent1.talk(
                {
                    "target": agent2.name,
                    "other_agents": [agent2],
                    "timestamp": timestamp,
                }
            )
            msg = f"{agent1} said to {agent2}: {response}"
            print(msg)
            response = agent2.talk(
                {
                    "target": agent1.name,
                    "other_agents": [agent1],
                    "timestamp": timestamp,
                }
            )
            msg = f"{agent2} said to {agent1}: {response}"
            print(msg)
            unix_time = unix_time + 10
        agent1_data = {
            "name": "John",
            "description": "outgoing and likes to talk",
        }
        agent2_data = {"name": "Alucard", "description": "shy"}
        agent1 = Agent(agent1_data)
        agent2 = Agent(agent2_data)
        unix_time = 1704067200
        for _ in range(2):
            timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
            response = agent1.talk(
                {
                    "target": agent2.name,
                    "other_agents": [agent2],
                    "timestamp": timestamp,
                }
            )
            msg = f"{agent1} said to {agent2}: {response}"
            print(msg)
            response = agent2.talk(
                {
                    "target": agent1.name,
                    "other_agents": [agent1],
                    "timestamp": timestamp,
                }
            )
            msg = f"{agent2} said to {agent1}: {response}"
            print(msg)
            unix_time = unix_time + 10

    def test_talk(self):
        """
        This function tests agent's ability to talk.
        """

        agent1_data = {
            "name": "Viktor",
            "description": "You love physics",
            "goal": "Answer questions, think, be rational.",
        }

        agent2_data = {"name": "Natasha", "description": "You love art"}
        agent1 = Agent(agent1_data)
        agent2 = Agent(agent2_data)

        agent1.connections.append(str(agent2))
        agent2.connections.append(str(agent1))

        unix_time = 1704067200
        convos = []
        for _ in range(5):
            timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
            response = agent1.talk(
                {"target": "Natasha", "other_agents": [agent2], "timestamp": timestamp}
            )
            msg = f"{agent1} said to {agent2}: {response}"
            print(msg)
            convos.append(msg)

            response = agent2.talk(
                {"target": "Viktor", "other_agents": [agent1], "timestamp": timestamp}
            )
            msg = f"{agent2} said to {agent1}: {response}"
            print(msg)
            convos.append(msg)

            # matrix.print_matrix()
            unix_time = unix_time + 10
        convos_string = "\n".join(convos)
        prompt = (
            f"evaluate on a score of 1-10 to tell me if the conversation "
            f"sounds like a real spoke conversation ,give your explanation, "
            f"and suggestions for improvements. Does the conversation go on too long? "
            f"are they repeating themselves?:\n\n{convos_string} \n\n "
            f"write your response like this:\nScore: 2\nExplanation: "
            f"It has problems with ....\nSuggestions: how to improve it"
        )
        result = llm.generate(prompt)
        print(prompt)
        print(result)

    def test_llmaction(self):
        """
        This function tests agent actions from llm calls.
        """

        matrix_data = {
            "scenario": "configs/def.json",
            "environment": "configs/largev2.tmj",
            "id": "test-id",
            "llm_action": 1,
            "allow_plan": 0,
            "allow_reflect": 0,
        }

        matrix = Matrix(matrix_data)

        for _ in range(2):  # Assuming 10 steps for the test
            # matrix.print_matrix()
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
            "y": 17,
        }

        path_to_walk = [
            (20, 17),
            (20, 18),
            (20, 19),
            (20, 20),
            (20, 21),
            (20, 22),
            (20, 23),
            (20, 24),
            (20, 25),
            (20, 26),
            (20, 27),
            (20, 28),
            (20, 29),
            (20, 30),
            (20, 31),
            (20, 32),
            (20, 33),
            (20, 34),
            (20, 35),
            (20, 36),
            (20, 37),
            (20, 38),
            (20, 39),
            (20, 40),
            (20, 41),
            (20, 42),
            (20, 43),
            (20, 44),
            (20, 45),
            (20, 46),
            (20, 47),
            (20, 48),
            (20, 49),
            (20, 50),
            (20, 51),
            (20, 52),
            (20, 53),
            (20, 54),
            (20, 55),
            (20, 56),
        ]
        agent = Agent(agent_data)
        environment = Environment({"filename": "configs/largev2.tmj"})
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

        for _ in path_to_walk:
            agent.perceive([], environment, "2023-01-01 00:00:00")
            agent.move({"environment": environment})

        print("\nAgent Spatial Memories at end:")
        for loc in agent.spatial_memory:
            print(f"{loc.name}")
            for area in loc.areas:
                print(f"\t-{area.name}")
                for obj in area.objects:
                    print(f"\t\t-{obj.name}")

        agent.answer("What are the locations you discovered?")

    def test_speed(self, test_vllm=False):
        """
        This function tests the speed of the llm model.
        """

        if test_vllm:
            available_models = VLLM_MODELS + ["mistral", "orca-mini"]
        else:
            available_models = ["mistral", "orca-mini"]
        model_times = []
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
        for model in available_models:
            print(f"Creating LLM Instance for model: {model}")
            new_llm = Llm(model=model)
            start_time = time.time()
            for _ in range(10):
                new_llm.generate(prompt)
            end_time = time.time()
            print(f"Deleting LLM Instance for model: {model}")
            del new_llm
            model_times.append({model: end_time - start_time})

        for time_log in model_times:
            print(f"{time_log}")

    def test_thread(self):
        """
        This function tests agents' memories running in threads.
        """

        agent_data = {
            "name": "John",
            "description": "You are a simulated persona.",
            "goal": "Answer questions, think, be rational.",
        }
        agent1 = Agent(agent_data)
        agent_data = {
            "name": "Michael",
            "description": "You are a simulated persona.",
            "goal": "Answer questions, think, be rational.",
        }
        agent2 = Agent(agent_data)
        # environment = Environment()
        print("Agent 1 memory before")
        print(agent1.short_memory)
        print("Agent 2 memory before")
        print(agent2.short_memory)
        for _ in range(10):
            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                print("Agent 1 memory during")
                print(agent1.short_memory)
                print("Agent 2 memory during")
                print(agent2.short_memory)
                timestamp = "2023-12-08 21:30:40"
                futures = []
                futures.append(
                    executor.submit(
                        agent1.talk,
                        {
                            "target": agent2.name,
                            "other_agents": [agent2],
                            "timestamp": timestamp,
                        },
                    )
                )
                futures.append(
                    executor.submit(
                        agent2.talk,
                        {
                            "target": agent1.name,
                            "other_agents": [agent1],
                            "timestamp": timestamp,
                        },
                    )
                )
                # results = [future.result() for future in futures]

        print("Agent 1 memory after")
        print(agent1.short_memory)
        print("Agent 2 memory after")
        print(agent2.short_memory)

    def test_agent_decision_zombie(self):
        """
        This function tests agent's decision on a zombie encounter.
        """

        matrix_data = {
            "scenario": None,
            "environment": "configs/largev2.tmj",
            "id": "test-agent-decision-zombie",
            "llm_action": 1,
            "allow_plan": 0,
            "allow_reflect": 0,
        }

        matrix = Matrix(matrix_data)
        matrix.interview_questions = [
            {"who": "all", "question": "Is the park a safe place?"},
            {"who": "all", "question": "What do you plan to do now?"},
        ]

        agent_data = {
            "name": "John",
            "kind": "human",
            "description": "Town is now zombie infested. You live at House A1.",
            "goal": "Survive.",
            "x": 36,
            "y": 87,  # This is just outside park
        }
        zombie_data = {
            "name": "Zombie",
            "kind": "zombie",
            "x": 36,
            "y": 93,  # This is just inside park
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

        agent.addMemory(
            "reflect",
            (
                f"{matrix.unix_to_strftime(matrix.unix_time)} - {agent} "
                f"wants to check if the Park is a safe place to go to or no."
            ),
            matrix.unix_to_strftime(matrix.unix_time),
            9,
        )

        matrix.agents.append(agent)
        matrix.agents.append(zombie)
        for _ in range(10):
            for a in matrix.agents:
                if matrix.llm_action_flag == 1 and a.kind != "zombie":
                    matrix.llm_action(a, matrix.unix_time)
                else:
                    matrix.agent_action(a, matrix.unix_time)

            matrix.unix_time = matrix.unix_time + 10

        for a in matrix.agents:
            print(str(a))

        matrix.run_interviews()

    def test_summary(self):
        """
        This function tests summary of agent conversations.
        """

        agent1_data = {
            "name": "Natasha",
            "description": "Natasha is confident and loves sports. Natasha lives at 'House B1'.",
            "goal": (
                "Natasha is planning to host a Christmas Party with her friends. "
                "Natasha decides on the location and time of the party. "
                "Natasha's mission is to extend invitations to every person encountered, "
                "fostering a joyous gathering filled with laughter, music, and festive cheer. "
                "Additionally, Natasha will encourage others to join in the celebration and invite "
                "their acquaintances, creating an unforgettable experience for everyone involved."
            ),
        }
        agent2_data = {"name": "James"}

        conversation_arr = [
            '''2023-12-08 21:30:40 - Natasha said to James: "James, I'm hosting a Christmas party 
            at House B1. Would you and your friends be interested in joining us?"''',
            """2023-12-08 21:30:40 - James said to Natasha: I'd be happy to attend, Natasha. 
            Thank you for inviting us. Paul and I will make sure to be there.""",
            """2023-12-08 21:30:50 - Natasha said to James:  2023-12-08 21:35:00 - 
            I'm glad you can make it, James. Looking forward to a wonderful Christmas party 
            at House B1 with you and Paul. Let me know if there's anything specific you or 
            your friends would like to contribute to the celebration.""",
            """2023-12-08 21:30:50 - James said to Natasha:  I'll let Natasha know if Paul 
            and I bring anything for the party. Thanks for asking, Natasha.""",
            """2023-12-08 21:31:00 - Natasha said to James:  I'm glad you both can make it, 
            James. Looking forward to your contribution to the Christmas party at House B1. 
            Let me know if there's anything specific Paul and you would like to bring.""",
        ]

        agent1 = Agent(agent1_data)
        agent2 = Agent(agent2_data)

        new_convo = Conversation(agent1, agent2, conversation_arr)
        print(f"=========== Conversation summary for {agent1.name}")
        agent1.last_conversation = new_convo
        agent1.summarize_conversation("2023-12-08 21:31:00")


def main():
    """
    This method runs all test functions.
    """

    parser = argparse.ArgumentParser(description="Matrix Test Suite")
    parser.add_argument("--all", action="store_true", help="Enable all test flag")
    parser.add_argument("--test", type=str, default="all", help="Context for relevance score test")
    parser.add_argument(
        "--context", type=str, default="racing", help="Context for relevance score test"
    )
    parser.add_argument("--history", action="store_true", help="Agents know each other flag")
    parser.add_argument("--steps", type=int, default=10, help="Steps for llm_action test.")
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


if __name__ == "__main__":
    main()
