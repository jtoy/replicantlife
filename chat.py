"""
This module handles the chat functionality of the system.
"""

from src.agents import Agent
from src.conversation import Conversation
from utils.utils import *


def chat_with_agent(agent, you):
    """
    This function lets a user to chat with an agent.
    """

    print(f"Welcome, chat with {agent}, the meta cognizing LLM agent!")
    timestamp = 1
    # unix_time = 1704067200
    agent.last_conversation = Conversation(agent, you)
    you.last_conversation = Conversation(you, agent)
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit()", "quit()"]:
            print("Goodbye!")
            break
        if user_input.lower() in ["meta()"]:
            agent.meta_cognize(unix_to_strftime(timestamp))
        elif user_input.lower() in ["mem()"]:
            print("long")
            for m in agent.memory:
                print(m)
            print("short")
            for m in agent.short_memory:
                print(m)
        else:

            # agent_response = agent.answer(user_input)
            timestamp += 10
            interaction = f"{timestamp} - Jason said to {agent}: {user_input}"
            you.last_conversation.messages.append(interaction)
            agent.last_conversation.messages.append(interaction)
            agent_response = agent.talk(
                {"other_agents": [you], "timestamp": unix_to_strftime(timestamp)}
            )  # "timestamp": self.unix_to_strftime(unix_time) })
            print(f"{agent}: {agent_response}")


if __name__ == "__main__":
    # Create an instance of the Agent
    sim_agent = Agent({"name": "Jarvis", "goal": "Serve Jason"})
    person = Agent({"name": "Jason"})

    # Start the CLI chat interface
    chat_with_agent(sim_agent, person)
