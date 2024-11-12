from mesa import Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from ..agents.car import Car
from ..agents.road import Road


class TrafficModel(Model):
    def __init__(self, width, height, n_cars):
        self.width = width
        self.height = height
        self.n_cars = n_cars

        self.grid = MultiGrid(width, height, True)
        self.schedule = RandomActivation(self)

        # Create roads
        self.create_roads()

        # Create cars
        self.create_cars()

        # Data collection
        self.datacollector = DataCollector(
            model_reporters={
                "Car_Count": lambda m: len(
                    [agent for agent in m.schedule.agents if isinstance(agent, Car)]
                ),
                "Average_Speed": lambda m: self.get_average_speed(),
            }
        )

    def create_roads(self):
        # Create horizontal road in the middle
        road_y = self.height // 2
        for x in range(self.width):
            road = Road(f"road_{x}", self)
            self.grid.place_agent(road, (x, road_y))

    def create_cars(self):
        road_y = self.height // 2
        for i in range(self.n_cars):
            car = Car(f"car_{i}", self)
            x = self.random.randrange(self.width)
            self.grid.place_agent(car, (x, road_y))
            self.schedule.add(car)

    def get_average_speed(self):
        cars = [agent for agent in self.schedule.agents if isinstance(agent, Car)]
        if not cars:
            return 0
        return sum(car.speed for car in cars) / len(cars)

    def step(self):
        self.datacollector.collect(self)
        self.schedule.step()
