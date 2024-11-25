from mesa import Agent

class Car(Agent):
    """Car agent that moves in the city"""

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.state = "moving"
        self.speed = 1

    def move(self):
        """Moves the car one cell to the right"""
        next_pos = self.get_next_position()
        if next_pos is None or not (
            0 <= next_pos[0] < self.model.grid.width
            and 0 <= next_pos[1] < self.model.grid.height
        ):
            self.state = "stopped"
            return

        # Get contents of next cell
        cell_contents = self.model.grid.get_cell_list_contents(next_pos)

        # Check for cars
        has_car = any(isinstance(obj, Car) for obj in cell_contents)
        if has_car:
            self.state = "stopped"
            return

        # Check for traffic light
        traffic_light = next(
            (obj for obj in cell_contents if isinstance(obj, Traffic_Light)), None
        )
        if traffic_light and not traffic_light.state:  # Red light (state=False)
            self.state = "stopped"
            return

        # Check for road
        has_road = any(isinstance(obj, Road) for obj in cell_contents)
        if has_road:
            self.model.grid.move_agent(self, next_pos)
            self.state = "moving"
            return

        # Stop if no valid position is found
        self.state = "stopped"

    def get_next_position(self):
        """Determines next position based on current road direction"""
        current_cell_contents = self.model.grid.get_cell_list_contents(self.pos)

        road = next(
            (obj for obj in current_cell_contents if isinstance(obj, Road)), None
        )

        if not road:
            return None

        x, y = self.pos
        if road.direction == "Right":
            next_pos = (x + 1, y)
        elif road.direction == "Left":
            next_pos = (x - 1, y)
        elif road.direction == "Up":
            next_pos = (x, y + 1)
        elif road.direction == "Down":
            next_pos = (x, y - 1)
        else:
            return None

        # Ensure the next cell has either a road or a traffic light
        next_cell_contents = self.model.grid.get_cell_list_contents(next_pos)
        has_road_or_light = any(
            isinstance(obj, (Road, Traffic_Light)) for obj in next_cell_contents
        )
        return next_pos if has_road_or_light else None

    def step(self):
        """Moves the car"""
        self.move()


class Destination(Agent):
    """Destination agent. Represents where cars should go."""

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        pass


class Obstacle(Agent):
    """Obstacle agent. Represents a fixed object that blocks movement."""

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        pass


class Road(Agent):
    """Road agent. Determines where cars can move and their direction."""

    def __init__(self, unique_id, model, direction="Left"):
        super().__init__(unique_id, model)
        self.direction = direction

    def step(self):
        pass


class Traffic_Light(Agent):
    """Traffic Light agent. Controls traffic flow at intersections."""

    def __init__(self, unique_id, model, state=False, timeToChange=10, pair_id=None):
        super().__init__(unique_id, model)
        self.pair_id = pair_id
        self.timeToChange = timeToChange
        self.state = state  # False for red, True for green
        self.time_since_change = 0

    def step(self):
        """Switch state every `timeToChange` steps."""
        self.time_since_change += 1
        if self.time_since_change >= self.timeToChange:
            self.state = not self.state  # Toggle state
            self.time_since_change = 0
