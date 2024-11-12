from mesa import Agent


class Car(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.direction = "right"  # Initial direction
        self.speed = 1  # Cells per step

    def move(self):
        # Simple straight line movement
        if self.direction == "right":
            next_pos = (self.pos[0] + self.speed, self.pos[1])
        elif self.direction == "left":
            next_pos = (self.pos[0] - self.speed, self.pos[1])

        # Check if the next position is within grid bounds
        if 0 <= next_pos[0] < self.model.grid.width:
            self.model.grid.move_agent(self, next_pos)

    def step(self):
        self.move()
