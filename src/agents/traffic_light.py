from mesa import Agent


class TrafficLight(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.state = "red"  # Start in red
        self.countdown = 3  # Start with 3 steps in red
        self.timing = {
            "red": 3,  # Red light lasts 3 steps
            "green": 3,  # Green light lasts 1 step
        }

    def step(self):
        self.countdown -= 1
        if self.countdown <= 0:
            if self.state == "red":
                self.state = "green"
                self.countdown = self.timing["green"]
            else:
                self.state = "red"
                self.countdown = self.timing["red"]
