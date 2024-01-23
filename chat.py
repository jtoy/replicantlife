import argparse
from src.agents import Agent
from src.conversation import Conversation

def chat_with_agent(agent,you):
    print("Welcome to the Agent Chat CLI!")
    timestamp = 1
    agent.last_conversation = Conversation(agent,you )
    you.last_conversation = Conversation(you, agent)
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("Goodbye!")
            break
        #agent_response = agent.answer(user_input)
        timestamp += 1
        interaction = f"{timestamp} - Jason said to {agent}: {user_input}"
        you.last_conversation.messages.append(interaction)
        agent.last_conversation.messages.append(interaction)
        agent_response = agent.talk({ "other_agents": [you],"timestamp":timestamp})   #"timestamp": self.unix_to_strftime(unix_time) })
        print(f"Agent: {agent_response}")

if __name__ == "__main__":
    # Create an instance of the Agent
    agent = Agent()
    you = Agent()

    # Start the CLI chat interface
    chat_with_agent(agent,you)

