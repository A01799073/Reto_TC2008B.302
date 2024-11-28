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
    def __init__(self, N):
        self.num_agents = N
        self.current_agents = 0
        self.reached_destination = 0
        self.spawn_delay = 1 
        self.steps_since_spawn = 0
        self.traffic_lights = []
        self.initialize_model()
        self.initialize_data_collector()
        self.running = True

    ###################
    # MAP INITIALIZATION
    ###################

    def initialize_model(self):
        self.load_map_data()
        self.create_grid()
        self.create_agents()
        self.spawn_initial_cars()

    def load_map_data(self):
        self.map_dictionary = json.load(open("static/city_files/mapDictionary.json"))
        with open("city_files/2022_base.txt") as baseFile:
            self.map_lines = baseFile.readlines()
            self.width = len(self.map_lines[0]) - 1
            self.height = len(self.map_lines)
            self.grid = MultiGrid(self.width, self.height, torus=False)
            self.schedule = RandomActivation(self)

    def create_grid(self):
        traffic_light_positions = self.collect_traffic_light_positions()
        self.paired_lights = self.pair_traffic_lights(traffic_light_positions)

    def collect_traffic_light_positions(self):
        positions = []
        for r, row in enumerate(self.map_lines):
            for c, col in enumerate(row):
                if col in ["S", "s"]:
                    pos = (c, self.height - r - 1)
                    positions.append((pos, col))
        return positions

    # END MAP INITIALIZATION

    ###################
    # AGENT CREATION
    ###################

    def create_agents(self):
        for r, row in enumerate(self.map_lines):
            for c, col in enumerate(row):
                self.create_agent_at_position(r, c, col)

    def create_agent_at_position(self, r, c, col):
        pos = (c, self.height - r - 1)

        if col in ["v", "^", ">", "<"]:
            self.create_road(r, c, pos, col)
        elif col in ["S", "s"]:
            self.create_traffic_light(r, c, pos, col)
        elif col == "#":
            self.create_obstacle(r, c, pos)
        elif col == "D":
            self.create_destination(r, c, pos)

    def create_road(self, r, c, pos, col):
        agent = Road(f"r_{r*self.width+c}", self, self.map_dictionary[col])
        self.grid.place_agent(agent, pos)

    def create_traffic_light(self, r, c, pos, col):
        pair_id = self.paired_lights.get((pos, col))
        agent = Traffic_Light(
            f"tl_{r*self.width+c}",
            self,
            False if col == "S" else True,
            int(self.map_dictionary[col]),
            pair_id=pair_id,
        )
        self.grid.place_agent(agent, pos)
        agent.post_init()
        self.schedule.add(agent)
        self.traffic_lights.append(agent)

    def create_obstacle(self, r, c, pos):
        agent = Obstacle(f"ob_{r*self.width+c}", self)
        self.grid.place_agent(agent, pos)

    def create_destination(self, r, c, pos):
        agent = Destination(f"d_{r*self.width+c}", self)
        self.grid.place_agent(agent, pos)
        self.schedule.add(agent)

    # END AGENT CREATION

    ###################
    # TRAFFIC LIGHT MANAGEMENT
    ###################

    def pair_traffic_lights(self, positions):
        paired_lights = {}
        remaining_positions = positions.copy()
        pair_id = 1

        while remaining_positions:
            pos1, col1 = remaining_positions.pop(0)
            closest_pair = None
            min_distance = float("inf")

            for i, (pos2, col2) in enumerate(remaining_positions):
                dx = abs(pos1[0] - pos2[0])
                dy = abs(pos1[1] - pos2[1])

                if (dx == 0 and dy == 1) or (dy == 0 and dx == 1):
                    dist = dx + dy
                    if dist < min_distance:
                        min_distance = dist
                        closest_pair = i

            if closest_pair is not None:
                pos2, col2 = remaining_positions.pop(closest_pair)
                paired_lights[pos1, col1] = pair_id
                paired_lights[pos2, col2] = pair_id

                is_horizontal = pos1[1] == pos2[1]
                self.pair_orientations = getattr(self, "pair_orientations", {})
                self.pair_orientations[pair_id] = (
                    "horizontal" if is_horizontal else "vertical"
                )

                pair_id += 1
            else:
                paired_lights[pos1, col1] = pair_id
                pair_id += 1

        return paired_lights

    # END TRAFFIC LIGHT MANAGEMENT

    ###################
    # CAR SPAWNING AND MANAGEMENT
    ###################

    def spawn_initial_cars(self):
        spawn_points = self.find_spawn_points()
        if not spawn_points:
            print("Warning: No valid corner spawn points found")
            return

        initial_cars = min(len(spawn_points), self.num_agents)
        for i in range(initial_cars):
            car = Car(f"car_{i}", self)
            self.grid.place_agent(car, spawn_points[i % len(spawn_points)])
            self.schedule.add(car)
            self.current_agents += 1

    def find_spawn_points(self):
        corner_checks = [
            (0, self.height - 1),
            (self.width - 1, self.height - 1),
            (self.width - 1, 0),
            (0, 0),
        ]

        return [
            corner
            for corner in corner_checks
            if any(
                isinstance(obj, Road)
                for obj in self.grid.get_cell_list_contents(corner)
            )
        ]

    def add_new_car(self):
        """Add a new car to the simulation with unique ID"""
        existing_cars = [
            agent for agent in self.schedule.agents if isinstance(agent, Car)
        ]

        if self.current_agents >= self.num_agents:
            return False

        # Find the highest existing car ID and add 1
        existing_ids = [int(car.unique_id.split("_")[1]) for car in existing_cars]
        next_id = max(existing_ids) + 1 if existing_ids else 0

        max_attempts = 3
        for _ in range(max_attempts):
            spawn_point = self.find_valid_spawn_point()
            if spawn_point:
                car_id = f"car_{next_id}"
                new_car = Car(car_id, self)

                cell_contents = self.grid.get_cell_list_contents(spawn_point)
                if not any(isinstance(agent, Car) for agent in cell_contents):
                    self.grid.place_agent(new_car, spawn_point)
                    self.schedule.add(new_car)
                    self.current_agents += 1
                    return True

        return False

    def find_valid_spawn_point(self):
        corner_checks = [
            (0, self.height - 1),
            (self.width - 1, self.height - 1),
            (self.width - 1, 0),
            (0, 0),
        ]

        valid_corners = []
        for corner in corner_checks:
            cell_contents = self.grid.get_cell_list_contents(corner)
            if any(isinstance(obj, Road) for obj in cell_contents) and not any(
                isinstance(obj, Car) for obj in cell_contents
            ):
                valid_corners.append(corner)

        if valid_corners:
            best_corner = None
            min_nearby_cars = float("inf")

            for corner in valid_corners:
                nearby_cars = 0
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nearby_pos = (corner[0] + dx, corner[1] + dy)
                    if (
                        0 <= nearby_pos[0] < self.grid.width
                        and 0 <= nearby_pos[1] < self.grid.height
                    ):
                        cell_contents = self.grid.get_cell_list_contents(nearby_pos)
                        if any(isinstance(obj, Car) for obj in cell_contents):
                            nearby_cars += 1

                if nearby_cars < min_nearby_cars:
                    min_nearby_cars = nearby_cars
                    best_corner = corner

            return best_corner

        for x in range(self.grid.width):
            for y in [0, self.height - 1]:
                pos = (x, y)
                cell_contents = self.grid.get_cell_list_contents(pos)
                if any(isinstance(obj, Road) for obj in cell_contents) and not any(
                    isinstance(obj, Car) for obj in cell_contents
                ):
                    return pos

        return None

    # END CAR SPAWNING AND MANAGEMENT

    ###################
    # DATA COLLECTION
    ###################

    def initialize_data_collector(self):
        self.datacollector = DataCollector(
            model_reporters={
                "Num_Agents": lambda m: m.num_agents,
                "Current_Agents": lambda m: m.current_agents,
                "Reached_Destination": lambda m: m.reached_destination,
                "Average_Speed": self.calculate_average_speed,
                "Traffic_Density": self.calculate_traffic_density,
                "Stopped_Cars": self.count_stopped_cars,
            }
        )

    def calculate_average_speed(self):
        cars = [agent for agent in self.schedule.agents if isinstance(agent, Car)]
        return sum(car.speed for car in cars) / len(cars) if cars else 0

    def calculate_traffic_density(self):
        return len(
            [agent for agent in self.schedule.agents if isinstance(agent, Car)]
        ) / (self.grid.width * self.grid.height)

    def count_stopped_cars(self):
        return len(
            [
                agent
                for agent in self.schedule.agents
                if isinstance(agent, Car) and agent.state == "stopped"
            ]
        )

    # END DATA COLLECTION

    ###################
    # MODEL STEPPING
    ###################

    def step(self):
        """Mesa model step function"""
        self.datacollector.collect(self)
        self.steps_since_spawn += 1
        
        if self.steps_since_spawn >= self.spawn_delay:
            current_cars = len([agent for agent in self.schedule.agents if isinstance(agent, Car)])
            cars_to_add = min(self.num_agents - current_cars, 3)
            for _ in range(cars_to_add):
                self.add_new_car()
            self.steps_since_spawn = 0

        self.schedule.step()
