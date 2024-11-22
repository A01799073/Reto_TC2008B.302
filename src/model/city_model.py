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
        dataDictionary = json.load(open("static/city_files/mapDictionary.json"))
        self.num_agents = N
        self.traffic_lights = []

        with open("city_files/2022_base.txt") as baseFile:
            lines = baseFile.readlines()
            self.width = len(lines[0]) - 1
            self.height = len(lines)
            self.grid = MultiGrid(self.width, self.height, torus=False)
            self.schedule = RandomActivation(self)

            for r, row in enumerate(lines):
                for c, col in enumerate(row):
                    if col in ["v", "^", ">", "<"]:
                        agent = Road(f"r_{r*self.width+c}", self, dataDictionary[col])
                        self.grid.place_agent(agent, (c, self.height - r - 1))
                    elif col in ["S", "s"]:
                        agent = Traffic_Light(
                            f"tl_{r*self.width+c}",
                            self,
                            False if col == "S" else True,
                            int(dataDictionary[col]),
                        )
                        self.grid.place_agent(agent, (c, self.height - r - 1))
                        self.schedule.add(agent)
                        self.traffic_lights.append(agent)
                    elif col == "#":
                        agent = Obstacle(f"ob_{r*self.width+c}", self)
                        self.grid.place_agent(agent, (c, self.height - r - 1))
                    elif col == "D":
                        agent = Destination(f"d_{r*self.width+c}", self)
                        self.grid.place_agent(agent, (c, self.height - r - 1))

        # Create cars
        road_cells = []
        for y in range(self.height):
            cell_contents = self.grid.get_cell_list_contents((0, y))
            if any(isinstance(obj, Road) for obj in cell_contents):
                road_cells.append(y)

        road_cells.sort()
        num_cars = min(2, len(road_cells))
        for i in range(num_cars):
            car = Car(f"car_{i}", self)
            self.grid.place_agent(car, (0, road_cells[i]))
            self.schedule.add(car)

        self.datacollector = DataCollector(
            model_reporters={
                "Car_Count": lambda m: len(
                    [agent for agent in m.schedule.agents if isinstance(agent, Car)]
                ),
                "Average_Speed": lambda m: sum(
                    agent.speed for agent in m.schedule.agents if isinstance(agent, Car)
                )
                / len([agent for agent in m.schedule.agents if isinstance(agent, Car)])
                if len([agent for agent in m.schedule.agents if isinstance(agent, Car)])
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

    def step(self):
        """Advance the model by one step."""
        self.datacollector.collect(self)
        self.schedule.step()
