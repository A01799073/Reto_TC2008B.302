from mesa import Agent
from .traffic_light import TrafficLight


class Car(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.direction = "right"
        self.speed = 1
        self.state = "moving"

    def check_traffic_light_ahead(self):
        # Check the next position for a traffic light
        next_pos = (self.pos[0] + self.speed, self.pos[1])
        if next_pos[0] < self.model.grid.width:
            cell_contents = self.model.grid.get_cell_list_contents(next_pos)
            for obj in cell_contents:
                if isinstance(obj, TrafficLight):
                    return obj.state
        return None

    def move(self):
        # Check for traffic light in next position
        light_ahead = self.check_traffic_light_ahead()

        # Only move if there's no red light ahead
        if light_ahead != "red":
            next_pos = (self.pos[0] + self.speed, self.pos[1])
            if 0 <= next_pos[0] < self.model.grid.width:
                self.model.grid.move_agent(self, next_pos)
                self.state = "moving"
        else:
            self.state = "stopped"

    def step(self):
        self.move()
