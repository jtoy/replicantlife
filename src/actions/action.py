"""
This module declares the Action class.
"""

class Action:
    """
    Agent's action class
    """

    # pylint: disable=missing-function-docstring
    def __init__(self, name):
        self.name = name

    # pylint: disable=missing-function-docstring
    def execute(self):
        raise NotImplementedError("Subclasses must implement the execute method")

    # pylint: disable=no-method-argument
    def example():
        raise NotImplementedError("Subclasses must implement the example method")
