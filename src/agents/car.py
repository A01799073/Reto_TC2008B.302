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
        next_pos = self.get_next_position()
        if next_pos is None or not (
            0 <= next_pos[0] < self.model.grid.width
            and 0 <= next_pos[1] < self.model.grid.height
        ):
            self.state = "stopped"
            return

        # Get contents of next cell
        cell_contents = self.model.grid.get_cell_list_contents(next_pos)

        # First check for cars
        has_car = any(isinstance(obj, Car) for obj in cell_contents)
        if has_car:
            self.state = "stopped"
            return

        # Then check for traffic light
        traffic_light = next(
            (obj for obj in cell_contents if isinstance(obj, Traffic_Light)), None
        )
        if traffic_light is not None:
            if not traffic_light.state:  # Red light (state=False)
                self.state = "stopped"
                return
            else:  # Green light (state=True)
                self.model.grid.move_agent(self, next_pos)
                self.state = "moving"
                return

        # Finally check for road
        has_road = any(isinstance(obj, Road) for obj in cell_contents)
        if has_road:
            self.model.grid.move_agent(self, next_pos)
            self.state = "moving"
            return

        # If no valid next position, stop
        if next_pos is None:
            self.state = "stopped"
            return

        # Check if next position is within grid bounds
        if not (
            0 <= next_pos[0] < self.model.grid.width
            and 0 <= next_pos[1] < self.model.grid.height
        ):
            self.state = "stopped"
            return

        # If none of the above, car can't move
        self.state = "stopped"

    def get_next_position(self):
        """Determines next position based on current road direction"""
        current_cell_contents = self.model.grid.get_cell_list_contents(self.pos)

        # Check for both Road and Traffic Light in current cell
        road = next(
            (obj for obj in current_cell_contents if isinstance(obj, Road)), None
        )
        traffic_light = next(
            (obj for obj in current_cell_contents if isinstance(obj, Traffic_Light)),
            None,
        )

        # If we're on a traffic light, look for adjacent road's direction
        if traffic_light is not None:
            # Check cells around traffic light for road
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                check_pos = (self.pos[0] + dx, self.pos[1] + dy)
                if (
                    0 <= check_pos[0] < self.model.grid.width
                    and 0 <= check_pos[1] < self.model.grid.height
                ):
                    check_contents = self.model.grid.get_cell_list_contents(check_pos)
                    road = next(
                        (obj for obj in check_contents if isinstance(obj, Road)), None
                    )
                    if road:
                        break

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

        # Check if next position contains either a road or a traffic light
        next_cell_contents = self.model.grid.get_cell_list_contents(next_pos)
        has_road_or_light = any(
            isinstance(obj, (Road, Traffic_Light)) for obj in next_cell_contents
        )

        return next_pos if has_road_or_light else None

    def step(self):
        """Moves the car"""
        self.move()
