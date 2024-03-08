import uuid


class Conversation:
    def __init__(self, agent, other_agent, messages=None):
        self.agent = agent
        self.other_agent = other_agent
        self.mid = str(uuid.uuid4())
        self.messages = messages

        if self.messages is None:
            self.messages = []
        else:
            self.messages = messages
