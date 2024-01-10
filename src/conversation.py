class Conversation:
    def __init__(self, agent, other_agent, messages=None):
        self.agent = agent
        self.other_agent = other_agent
        self.messages = messages

        if self.messages is None:
            self.messages = []
        else:
            self.messages = messages

