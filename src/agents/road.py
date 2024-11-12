from mesa import Agent


class Road(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.type = "road"  # Can be "road" or "boundary"
