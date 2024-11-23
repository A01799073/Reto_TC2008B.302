# src/model/city_model.py
from mesa import Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from mesa.space import MultiGrid
from ..agents.car import Car
from ..agents.road import Road
from ..agents.traffic_light import Traffic_Light
from ..agents.destination import Destination
from ..agents.obstacle import Obstacle
import json


class CityModel(Model):
    # src/model/city_model.py

    def __init__(self, N):
        """
        Initialize the CityModel.
        Args:
            N: Number of cars to create
        """
        # Load the map dictionary
        dataDictionary = json.load(open("static/city_files/mapDictionary.json"))
        self.num_agents = N
        self.traffic_lights = []

        # Load the map file to get dimensions
        with open("city_files/2022_base.txt") as baseFile:
            lines = baseFile.readlines()
            self.width = len(lines[0]) - 1
            self.height = len(lines)
            self.grid = MultiGrid(self.width, self.height, torus=False)
            self.schedule = RandomActivation(self)

            # First pass: Store traffic light positions
            traffic_light_positions = []
            for r, row in enumerate(lines):
                for c, col in enumerate(row):
                    if col in ["S", "s"]:
                        pos = (c, self.height - r - 1)
                        traffic_light_positions.append((pos, col))

            # Pair traffic lights based on proximity
            paired_lights = self.pair_traffic_lights(traffic_light_positions)

            # Second pass: Create all agents
            for r, row in enumerate(lines):
                for c, col in enumerate(row):
                    pos = (c, self.height - r - 1)

                    if col in ["v", "^", ">", "<"]:
                        agent = Road(f"r_{r*self.width+c}", self, dataDictionary[col])
                        self.grid.place_agent(agent, pos)

                    elif col in ["S", "s"]:
                        pair_id = paired_lights.get((pos, col))
                        agent = Traffic_Light(
                            f"tl_{r*self.width+c}",
                            self,
                            False if col == "S" else True,
                            int(dataDictionary[col]),
                            pair_id=pair_id,
                        )
                        self.grid.place_agent(agent, pos)
                        agent.post_init()  # Call post_init after placement
                        self.schedule.add(agent)
                        self.traffic_lights.append(agent)

                    elif col == "#":
                        agent = Obstacle(f"ob_{r*self.width+c}", self)
                        self.grid.place_agent(agent, pos)

                    elif col == "D":
                        agent = Destination(f"d_{r*self.width+c}", self)
                        self.grid.place_agent(agent, pos)
                        self.schedule.add(agent)

            # Find corner spawn points
            spawn_points = []
            # Check corners (clockwise from top-left)
            corner_checks = [
                (0, self.height-1),  # Top-left
                (self.width-1, self.height-1),  # Top-right
                (self.width-1, 0),  # Bottom-right
                (0, 0)  # Bottom-left
            ]

            for corner in corner_checks:
                cell_contents = self.grid.get_cell_list_contents(corner)
                if any(isinstance(obj, Road) for obj in cell_contents):
                    spawn_points.append(corner)

            if not spawn_points:
                # Fallback in case no corners have roads
                print("Warning: No valid corner spawn points found")
                return

            # Create cars
            num_cars = N
            cars_per_spawn = num_cars // len(spawn_points)
            extra_cars = num_cars % len(spawn_points)

            car_id = 0
            for spawn_point in spawn_points:
                # Calculate how many cars to spawn at this point
                cars_to_spawn = cars_per_spawn + (1 if extra_cars > 0 else 0)
                extra_cars -= 1 if extra_cars > 0 else 0
                
                for _ in range(cars_to_spawn):
                    car = Car(f"car_{car_id}", self)
                    self.grid.place_agent(car, spawn_point)
                    self.schedule.add(car)
                    car_id += 1

            # Initialize data collector
            self.datacollector = DataCollector(
                model_reporters={
                    "Car_Count": lambda m: len(
                        [agent for agent in m.schedule.agents if isinstance(agent, Car)]
                    ),
                    "Average_Speed": lambda m: sum(
                        agent.speed
                        for agent in m.schedule.agents
                        if isinstance(agent, Car)
                    )
                    / len(
                        [agent for agent in m.schedule.agents if isinstance(agent, Car)]
                    )
                    if len(
                        [agent for agent in m.schedule.agents if isinstance(agent, Car)]
                    )
                    > 0
                    else 0,
                    "Traffic_Density": lambda m: len(
                        [agent for agent in m.schedule.agents if isinstance(agent, Car)]
                    )
                    / (m.grid.width * m.grid.height),
                    "Stopped_Cars": lambda m: len(
                        [
                            agent
                            for agent in m.schedule.agents
                            if isinstance(agent, Car) and agent.state == "stopped"
                        ]
                    ),
                }
            )

            self.running = True

    def pair_traffic_lights(self, positions):
        """
        Pair traffic lights based on their positions and orientation.
        Returns a dictionary mapping positions to pair IDs.
        """
        paired_lights = {}
        remaining_positions = positions.copy()
        pair_id = 1

        while remaining_positions:
            pos1, col1 = remaining_positions.pop(0)
            closest_pair = None
            min_distance = float("inf")

            # Find closest unpaired traffic light that forms a valid intersection pair
            for i, (pos2, col2) in enumerate(remaining_positions):
                dx = abs(pos1[0] - pos2[0])
                dy = abs(pos1[1] - pos2[1])

                # A valid pair should be:
                # 1. Close to each other (within 2 cells)
                # 2. Either on same vertical line (dx=0) or horizontal line (dy=0)
                # 3. Not diagonally placed
                if (dx == 0 and dy == 1) or (dy == 0 and dx == 1):
                    dist = dx + dy  # Manhattan distance
                    if dist < min_distance:
                        min_distance = dist
                        closest_pair = i

            if closest_pair is not None:
                pos2, col2 = remaining_positions.pop(closest_pair)
                paired_lights[pos1, col1] = pair_id
                paired_lights[pos2, col2] = pair_id

                # Determine orientation based on how lights are positioned
                is_horizontal = pos1[1] == pos2[1]
                self.pair_orientations = getattr(self, "pair_orientations", {})
                self.pair_orientations[pair_id] = (
                    "horizontal" if is_horizontal else "vertical"
                )

                pair_id += 1
            else:
                # If no valid pair found, this might indicate an issue
                paired_lights[pos1, col1] = pair_id
                pair_id += 1

        return paired_lights

    def step(self):
        """Advance the model by one step."""
        self.datacollector.collect(self)
        self.schedule.step()
