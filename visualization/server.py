from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import Slider
from src.model.traffic_model import TrafficModel
from src.agents.car import Car
from src.agents.road import Road


def agent_portrayal(agent):
    if agent is None:
        return

    portrayal = {"Shape": "rect", "Filled": "true", "Layer": 0, "w": 1, "h": 1}

    if isinstance(agent, Car):
        portrayal.update({"Shape": "circle", "r": 0.8, "Color": "red", "Layer": 1})
    elif isinstance(agent, Road):
        portrayal.update({"Color": "gray", "Layer": 0})

    return portrayal


def create_server():
    GRID_SIZE = 20

    grid = CanvasGrid(agent_portrayal, GRID_SIZE, GRID_SIZE, 500, 500)

    car_chart = ChartModule(
        [
            {"Label": "Car_Count", "Color": "#FF0000"},
            {"Label": "Average_Speed", "Color": "#00FF00"},
        ]
    )

    model_params = {
        "width": GRID_SIZE,
        "height": GRID_SIZE,
        "n_cars": Slider("Number of Cars", 5, 1, 20, 1),
    }

    server = ModularServer(
        TrafficModel, [grid, car_chart], "Traffic Simulation", model_params
    )

    return server
