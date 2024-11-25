# src/agents/car.py

from mesa import Agent
from .road import Road
from .traffic_light import Traffic_Light
from .destination import Destination
from typing import Tuple, Optional, List
import heapq


class Car(Agent):
    """A car agent that moves through the city following roads and traffic rules."""

    ###################
    # INITIALIZATION
    ###################

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.state = "moving"
        self.speed = 1
        self.destination = self._assign_destination()
        self.path = None
        self.last_position = None
        self.stuck_counter = 0

    def _assign_destination(self) -> Optional["Destination"]:
        """Assigns a random destination to the car"""
        destinations = [
            agent
            for agents, pos in self.model.grid.coord_iter()
            for agent in agents
            if isinstance(agent, Destination)
        ]
        return self.random.choice(destinations) if destinations else None

    ###################
    # POSITION AND DISTANCE CALCULATIONS
    ###################

    def _calculate_manhattan_distance(
        self, pos1: Tuple[int, int], pos2: Tuple[int, int]
    ) -> int:
        """Calculate Manhattan distance between two positions"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def _is_valid_position(self, position: Tuple[int, int]) -> bool:
        """Validates if a position is within grid bounds"""
        return (
            0 <= position[0] < self.model.grid.width
            and 0 <= position[1] < self.model.grid.height
        )

    ###################
    # GRID CONTENT CHECKS
    ###################

    def _is_valid_path(self, position: Tuple[int, int]) -> bool:
        """Checks if a position is a valid path (road or traffic light only)"""
        if not self._is_valid_position(position):
            return False

        cell_contents = self.model.grid.get_cell_list_contents(position)
        return any(
            isinstance(content, (Road, Traffic_Light)) for content in cell_contents
        ) and all(
            isinstance(content, (Road, Traffic_Light)) for content in cell_contents
        )

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

    ###################
    # ROAD AND TRAFFIC LIGHT HANDLING
    ###################

    def _get_current_road(self) -> Optional["Road"]:
        """Gets the road at current position"""
        cell_contents = self.model.grid.get_cell_list_contents(self.pos)
        return next((obj for obj in cell_contents if isinstance(obj, Road)), None)

    def _get_adjacent_road(self) -> Optional["Road"]:
        """Gets adjacent road when on traffic light"""
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            check_pos = (self.pos[0] + dx, self.pos[1] + dy)
            if self._is_valid_position(check_pos):
                cell_contents = self.model.grid.get_cell_list_contents(check_pos)
                road = next(
                    (obj for obj in cell_contents if isinstance(obj, Road)), None
                )
                if road:
                    return road
        return None

    ###################
    # MOVEMENT LOGIC
    ###################

    def _get_next_position(self) -> Optional[Tuple[int, int]]:
        """Determines next position based on current location and destination"""
        current_contents = self.model.grid.get_cell_list_contents(self.pos)

        if any(isinstance(obj, Traffic_Light) for obj in current_contents):
            return self._handle_traffic_light_movement()
        return self._handle_road_movement()

    def _handle_traffic_light_movement(self) -> Optional[Tuple[int, int]]:
        """Handle movement when car is on a traffic light"""
        current_road = self._get_adjacent_road()
        if not current_road:
            return None

        direction_map = {
            "Right": (1, 0),
            "Left": (-1, 0),
            "Up": (0, 1),
            "Down": (0, -1),
        }

        if current_road.direction in direction_map:
            dx, dy = direction_map[current_road.direction]
            next_pos = (self.pos[0] + dx, self.pos[1] + dy)
            return next_pos if self._is_valid_path(next_pos) else None

        return None

    def _handle_road_movement(self) -> Optional[Tuple[int, int]]:
        """Handle movement when car is on a regular road"""
        current_road = self._get_current_road()
        if not current_road:
            return None

        direction_map = {
            "Right": (1, 0),
            "Left": (-1, 0),
            "Up": (0, 1),
            "Down": (0, -1),
        }

        if current_road.direction in direction_map:
            dx, dy = direction_map[current_road.direction]
            next_pos = (self.pos[0] + dx, self.pos[1] + dy)
            return next_pos if self._is_valid_path(next_pos) else None

        return None

    ###################
    # PATHFINDING
    ###################

    def find_path(self):
        """Find a valid path using A* that respects road direction constraints."""
        if not self.destination:
            return []

        start, goal = self.pos, self.destination.pos
        open_set = [
            (0 + self._calculate_manhattan_distance(start, goal), 0, start, [start])
        ]
        closed_set = set()

        while open_set:
            f_score, g_score, current, path = heapq.heappop(open_set)

            if current == goal:
                return path[1:]

            if current in closed_set:
                continue
            closed_set.add(current)

            for neighbor in self._get_valid_neighbors(current):
                if neighbor in closed_set:
                    continue

                tentative_g_score = g_score + 1
                if not self._is_better_path(neighbor, tentative_g_score, open_set):
                    continue

                heapq.heappush(
                    open_set,
                    (
                        tentative_g_score
                        + self._calculate_manhattan_distance(neighbor, goal),
                        tentative_g_score,
                        neighbor,
                        path + [neighbor],
                    ),
                )

        return []

    def _get_valid_neighbors(self, current: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get valid neighboring positions for pathfinding."""
        neighbors = self.model.grid.get_neighborhood(
            current, moore=False, include_center=False
        )
        return [n for n in neighbors if self._is_valid_move(current, n)]

    def _is_valid_move(
        self, current: Tuple[int, int], neighbor: Tuple[int, int]
    ) -> bool:
        """Check if move from current to neighbor is valid."""
        if self._check_collision(neighbor):
            return False

        intended_direction = (neighbor[0] - current[0], neighbor[1] - current[1])
        direction_map = {
            (1, 0): "Left",
            (-1, 0): "Right",
            (0, 1): "Down",
            (0, -1): "Up",
        }

        cell_contents = self.model.grid.get_cell_list_contents([neighbor])

        # Check if there's a road going in the wrong direction
        for agent in cell_contents:
            if isinstance(agent, Road) and agent.direction == direction_map.get(
                intended_direction, ""
            ):
                return False

        # Check if the cell is traversable (contains road, destination, or traffic light)
        if not any(
            isinstance(agent, (Road, Destination, Traffic_Light))
            for agent in cell_contents
        ):
            return False

        return True

    def _is_better_path(
        self, neighbor: Tuple[int, int], g_score: int, open_set: List
    ) -> bool:
        """Check if this path to neighbor is better than existing ones."""
        return not any(item[2] == neighbor and g_score >= item[1] for item in open_set)

    def find_alternate_path(self):
        """Find an alternate path when stuck."""
        return self.find_path()

    ###################
    # MAIN MOVEMENT AND STEP FUNCTIONS
    ###################

    def move(self):
        """Handle car movement with collision detection and path following."""
        if self._handle_destination_arrival():
            return

        if not self.path:
            self.path = self.find_path()
            if not self.path:
                self._handle_no_path()
                return

        if not self._attempt_move():
            self._handle_blocked_movement()

    def _handle_destination_arrival(self) -> bool:
        """Handle arrival at destination."""
        if self.destination and self.pos == self.destination.pos:
            self.state = "arrived"
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)

            if (
                len(
                    [
                        agent
                        for agent in self.model.schedule.agents
                        if isinstance(agent, Car)
                    ]
                )
                < self.model.num_agents
            ):
                self.model.add_new_car()
            return True
        return False

    def _handle_no_path(self):
        """Handle situation when no path is found."""
        self.state = "stopped"
        self.stuck_counter += 1
        if self.stuck_counter > 15:
            self.path = self.find_alternate_path()
            self.stuck_counter = 0

    def _attempt_move(self) -> bool:
        """Attempt to move to next position in path."""
        if not self.path:
            return False

        next_move = self.path[0]
        if self._check_collision(next_move) or not self._get_traffic_light_state(
            next_move
        ):
            return False

        self.model.grid.move_agent(self, next_move)
        self.state = "moving"
        self.path.pop(0)
        self.stuck_counter = 0
        self.last_position = self.pos
        return True

    def _handle_blocked_movement(self):
        """Handle situation when movement is blocked."""
        self.state = "stopped"
        self.stuck_counter += 1
        if self.stuck_counter > 15:
            self.path = self.find_alternate_path()
            self.stuck_counter = 0

    def step(self):
        """Mesa model step function"""
        self.move()
