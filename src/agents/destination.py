# src/agents/destination.py
from mesa import Agent


class Destination(Agent):
    """Destination agent. Where each car should go."""

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        pass
