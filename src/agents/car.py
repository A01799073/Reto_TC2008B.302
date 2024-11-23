from mesa import Agent
from .road import Road
from .traffic_light import Traffic_Light
from .destination import Destination
from typing import Tuple, Optional, List


class Car(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.state = "moving"
        self.speed = 1
        self.destination = self._assign_destination()
        self.just_crossed_light = False  # New state variable

    def _assign_destination(self) -> Optional["Destination"]:
        """Assigns a random destination to the car"""
        destinations = []
        for agents, pos in self.model.grid.coord_iter():
            for agent in agents:
                if isinstance(agent, Destination):
                    destinations.append(agent)

        chosen_dest = self.random.choice(destinations) if destinations else None

        return chosen_dest

    def _calculate_manhattan_distance(
        self, pos1: Tuple[int, int], pos2: Tuple[int, int]
    ) -> int:
        """Calculate Manhattan distance between two positions"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def _get_possible_turns(self) -> List[Tuple[int, int]]:
        """Get all possible turning positions from current location"""
        possible_turns = []
        x, y = self.pos

        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            check_pos = (x + dx, y + dy)
            if self._is_valid_position(check_pos):
                cell_contents = self.model.grid.get_cell_list_contents(check_pos)
                # Valid turn if position contains road or traffic light
                if any(isinstance(obj, (Road, Traffic_Light)) for obj in cell_contents):
                    possible_turns.append(check_pos)

        return possible_turns

    def _is_valid_path(self, position: Tuple[int, int]) -> bool:
        """Checks if a position is a valid path (road or traffic light only)"""
        if not self._is_valid_position(position):
            return False

        cell_contents = self.model.grid.get_cell_list_contents(position)

        # Check if the position contains ONLY roads or traffic lights
        # If there's anything else (like a building), it's not a valid path
        for content in cell_contents:
            if not isinstance(content, (Road, Traffic_Light)):
                return False

        # Must contain at least one road or traffic light
        return any(
            isinstance(content, (Road, Traffic_Light)) for content in cell_contents
        )

    def _choose_best_turn(
        self, possible_turns: List[Tuple[int, int]]
    ) -> Optional[Tuple[int, int]]:
        """Choose the turn that gets us closest to destination"""
        if not self.destination or not possible_turns:
            return None

        # Calculate distances to destination for each possible turn
        turn_distances = [
            (turn, self._calculate_manhattan_distance(turn, self.destination.pos))
            for turn in possible_turns
        ]

        # Sort by distance (closest first)
        turn_distances.sort(key=lambda x: x[1])

        return turn_distances[0][0]

    def _check_collision(self, position: Tuple[int, int]) -> bool:
        """Checks if there's a collision at the given position"""
        cell_contents = self.model.grid.get_cell_list_contents(position)
        return any(isinstance(obj, Car) for obj in cell_contents)

    def _get_traffic_light_state(self, position: Tuple[int, int]) -> bool:
        """Gets traffic light state at position. Returns True if green or no light."""
        cell_contents = self.model.grid.get_cell_list_contents(position)
        traffic_light = next(
            (obj for obj in cell_contents if isinstance(obj, Traffic_Light)), None
        )
        return traffic_light.state if traffic_light else True

    def _is_valid_position(self, position: Tuple[int, int]) -> bool:
        """Validates if a position is within grid bounds"""
        return (
            0 <= position[0] < self.model.grid.width
            and 0 <= position[1] < self.model.grid.height
        )

    def _get_current_road(self) -> Optional["Road"]:
        """Gets the road at current position"""
        cell_contents = self.model.grid.get_cell_list_contents(self.pos)
        return next((obj for obj in cell_contents if isinstance(obj, Road)), None)

    def _get_adjacent_road(self) -> Optional["Road"]:
        """Gets adjacent road when on traffic light"""
        x, y = self.pos
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            check_pos = (x + dx, y + dy)
            print(f"Checking position {check_pos} for adjacent road")
            if self._is_valid_position(check_pos):
                cell_contents = self.model.grid.get_cell_list_contents(check_pos)
                road = next(
                    (obj for obj in cell_contents if isinstance(obj, Road)), None
                )
                if road:
                    print(f"Found adjacent road at {check_pos} with direction {road.direction}")
                    return road
        print("No adjacent road found")
        return None

    def _get_next_position(self) -> Optional[Tuple[int, int]]:
        """Determines next position based on current location and destination"""
        x, y = self.pos
        current_contents = self.model.grid.get_cell_list_contents(self.pos)
        on_traffic_light = any(isinstance(obj, Traffic_Light) for obj in current_contents)
        next_pos = None

        # If we're on a traffic light
        if on_traffic_light:
            next_pos = self._handle_traffic_light_movement()
            if next_pos:
                return next_pos

        # If not at traffic light, follow road direction
        return self._handle_road_movement()

    def _handle_traffic_light_movement(self) -> Optional[Tuple[int, int]]:
        """Handle movement when car is on a traffic light"""
        x, y = self.pos
        current_contents = self.model.grid.get_cell_list_contents(self.pos)
        next_pos = None
        
        print(f"Car {self.unique_id} is on traffic light at position {self.pos}")
        
        traffic_light = next(
            (obj for obj in current_contents if isinstance(obj, Traffic_Light)),
            None,
        )
        if traffic_light:
            print(f"Traffic light orientation: {traffic_light.orientation}")
            
            current_road = self._get_adjacent_road()
            print(f"Adjacent road found: {current_road is not None}")
            if current_road:
                print(f"Adjacent road direction: {current_road.direction}")
                # Handle all possible directions regardless of traffic light orientation
                if current_road.direction == "Right":
                    next_pos = (x + 1, y)
                elif current_road.direction == "Left":
                    next_pos = (x - 1, y)
                elif current_road.direction == "Up":
                    next_pos = (x, y + 1)
                elif current_road.direction == "Down":
                    next_pos = (x, y - 1)

            if next_pos:
                print(f"Proposed next position: {next_pos}")
                print(f"Is valid path: {self._is_valid_path(next_pos)}")
                if self._is_valid_path(next_pos):
                    return next_pos
        
        return None

    def _handle_road_movement(self) -> Optional[Tuple[int, int]]:
        """Handle movement when car is on a regular road"""
        x, y = self.pos
        current_road = self._get_current_road()
        
        if current_road:
            direction_map = {
                "Right": (1, 0),
                "Left": (-1, 0),
                "Up": (0, 1),
                "Down": (0, -1),
            }

            if current_road.direction in direction_map:
                dx, dy = direction_map[current_road.direction]
                next_pos = (x + dx, y + dy)

                if self._is_valid_path(next_pos):
                    return next_pos

        return None

    def move(self):
        """Executes movement logic"""
        # Check if arrived at destination
        if self.destination and self.pos == self.destination.pos:
            self.state = "arrived"
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            return

        next_pos = self._get_next_position()

        # If no valid position found or position is not a valid path
        if next_pos is None or not self._is_valid_path(next_pos):
            self.state = "stopped"
            return

        # Check for collision
        if self._check_collision(next_pos):
            self.state = "stopped"
            return

        # Check traffic light
        if not self._get_traffic_light_state(next_pos):
            self.state = "stopped"
            return

        # Move to next position
        self.model.grid.move_agent(self, next_pos)
        self.state = "moving"

    def step(self):
        """Mesa model step function"""
        self.move()
