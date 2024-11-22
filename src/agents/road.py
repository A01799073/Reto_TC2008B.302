# src/agenas/road.py
from mesa import Agent


class Road(Agent):
    """Road agent. Determines where the cars can move, and in which direction."""

    def __init__(self, unique_id, model, direction="Left"):
        super().__init__(unique_id, model)
        self.direction = direction

    def step(self):
        pass
