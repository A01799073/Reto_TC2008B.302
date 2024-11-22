from mesa import Agent
from .road import Road
from .traffic_light import Traffic_Light

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
            
        print(f"\nCar {self.unique_id} at {self.pos} trying to move to {next_pos}")
        
        # Get contents of next cell
        cell_contents = self.model.grid.get_cell_list_contents(next_pos)
        print(f"Cell contents: {[type(obj).__name__ for obj in cell_contents]}")
        
        # First check for cars
        has_car = any(isinstance(obj, Car) for obj in cell_contents)
        if has_car:
            print(f"Has car ahead: {has_car}")
            self.state = "stopped"
            print(f"Car {self.unique_id} stopped at {self.pos}")
            return

        # Then check for traffic light
        traffic_light = next((obj for obj in cell_contents if isinstance(obj, Traffic_Light)), None)
        if traffic_light is not None:
            print(f"Traffic light state: {'Green' if traffic_light.state else 'Red'}")
            if not traffic_light.state:  # Red light (state=False)
                self.state = "stopped"
                print(f"Car {self.unique_id} stopped at red light at {self.pos}")
                return
            else:  # Green light (state=True)
                self.model.grid.move_agent(self, next_pos)
                self.state = "moving"
                print(f"Car {self.unique_id} passed through green light to {next_pos}")
                return

        # Finally check for road
        has_road = any(isinstance(obj, Road) for obj in cell_contents)
        if has_road:
            self.model.grid.move_agent(self, next_pos)
            self.state = "moving"
            print(f"Car {self.unique_id} moved to {next_pos}")
            return
        
        # If none of the above, car can't move
        self.state = "stopped"
        print(f"Car {self.unique_id} stopped at {self.pos}")

    def step(self):
        """Moves the car"""
        self.move()
