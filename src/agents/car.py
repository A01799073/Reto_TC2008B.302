# src/agents/car.py
from mesa import Agent
from .road import Road


class Car(Agent):
    """Car agent that moves in the city"""

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.state = "moving"
        self.speed = 1

    def move(self):
        """Moves the car one cell to the right"""
        next_pos = (self.pos[0] + 1, self.pos[1])

        if next_pos[0] >= self.model.grid.width:
            next_pos = (0, self.pos[1])

        cell_contents = self.model.grid.get_cell_list_contents(next_pos)
        has_car = any(isinstance(obj, Car) for obj in cell_contents)
        has_road = any(isinstance(obj, Road) for obj in cell_contents)

        if has_road and not has_car:
            self.model.grid.move_agent(self, next_pos)
            self.state = "moving"
        else:
            self.state = "stopped"

    def step(self):
        """Moves the car"""
        self.move()
