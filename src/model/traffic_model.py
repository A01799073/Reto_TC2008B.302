from mesa import Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from ..agents.car import Car
from ..agents.road import Road
from ..agents.traffic_light import TrafficLight


class TrafficModel(Model):
    def __init__(self, width, height, n_cars, n_traffic_lights=2):
        self.width = width
        self.height = height
        self.n_cars = n_cars
        self.n_traffic_lights = n_traffic_lights

        self.grid = MultiGrid(width, height, True)
        self.schedule = RandomActivation(self)

        # Create roads with multiple lanes
        self.create_roads()

        # Create traffic lights
        self.create_traffic_lights()

        # Create cars
        self.create_cars()

        # Data collection
        self.datacollector = DataCollector(
            model_reporters={
                "Car_Count": lambda m: len(
                    [agent for agent in m.schedule.agents if isinstance(agent, Car)]
                ),
                "Average_Speed": self.get_average_speed,
                "Traffic_Density": self.get_traffic_density,
                "Stopped_Cars": self.get_stopped_cars,
            }
        )

    def create_roads(self):
        # Create two lanes
        road_y_positions = [self.height // 2, (self.height // 2) - 1]
        for y in road_y_positions:
            for x in range(self.width):
                road = Road(f"road_{x}_{y}", self)
                self.grid.place_agent(road, (x, y))

    def create_traffic_lights(self):
        # Place traffic lights at regular intervals
        interval = self.width // (self.n_traffic_lights + 1)
        road_y = self.height // 2

        for i in range(self.n_traffic_lights):
            x_pos = (i + 1) * interval
            light = TrafficLight(f"light_{i}", self)
            self.grid.place_agent(light, (x_pos, road_y))
            self.schedule.add(light)

    def create_cars(self):
        road_y_positions = [self.height // 2, (self.height // 2) - 1]
        for i in range(self.n_cars):
            car = Car(f"car_{i}", self)
            x = self.random.randrange(self.width)
            y = self.random.choice(road_y_positions)
            self.grid.place_agent(car, (x, y))
            self.schedule.add(car)

    def get_average_speed(self):
        cars = [agent for agent in self.schedule.agents if isinstance(agent, Car)]
        if not cars:
            return 0
        return sum(car.speed for car in cars) / len(cars)

    def get_traffic_density(self):
        # Calculate cars per unit of road
        road_cells = self.width * 2  # Two lanes
        return (
            len([agent for agent in self.schedule.agents if isinstance(agent, Car)])
            / road_cells
        )

    def get_stopped_cars(self):
        return len(
            [
                agent
                for agent in self.schedule.agents
                if isinstance(agent, Car) and agent.state == "stopped"
            ]
        )

    def step(self):
        self.datacollector.collect(self)
        self.schedule.step()
