from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import Slider
from src.model.traffic_model import TrafficModel
from src.agents.car import Car
from src.agents.road import Road
from src.agents.traffic_light import TrafficLight


def agent_portrayal(agent):
    if agent is None:
        return

    portrayal = {"Shape": "rect", "Filled": "true", "Layer": 0, "w": 1, "h": 1}

    if isinstance(agent, Car):
        portrayal.update(
            {
                "Shape": "rect",
                "Color": "red",
                "Layer": 2,
                "text_color": "white",
            }
        )
    elif isinstance(agent, Road):
        portrayal.update({"Color": "gray", "Layer": 0})
    elif isinstance(agent, TrafficLight):
        portrayal.update(
            {
                "Shape": "rect",
                "Color": "red" if agent.state == "red" else "green",
                "Layer": 1,
            }
        )

    return portrayal


def create_server():
    GRID_SIZE = 20

    grid = CanvasGrid(agent_portrayal, GRID_SIZE, GRID_SIZE, 500, 500)

    traffic_chart = ChartModule(
        [
            {"Label": "Car_Count", "Color": "#FF0000"},
            {"Label": "Stopped_Cars", "Color": "#FF00FF"},
        ]
    )

    model_params = {
        "width": GRID_SIZE,
        "height": GRID_SIZE,
        "n_cars": Slider("Number of Cars", 5, 1, 20, 1),
        "n_traffic_lights": Slider("Number of Traffic Lights", 2, 1, 5, 1),
    }

    server = ModularServer(
        TrafficModel, [grid, traffic_chart], "Traffic Simulation", model_params
    )

    return server


def create_server():
    GRID_SIZE = 20

    grid = CanvasGrid(agent_portrayal, GRID_SIZE, GRID_SIZE, 500, 500)

    traffic_chart = ChartModule(
        [
            {"Label": "Car_Count", "Color": "#FF0000"},
            {"Label": "Average_Speed", "Color": "#00FF00"},
        ]
    )

    density_chart = ChartModule(
        [
            {"Label": "Traffic_Density", "Color": "#0000FF"},
            {"Label": "Stopped_Cars", "Color": "#FF00FF"},
        ]
    )

    model_params = {
        "width": GRID_SIZE,
        "height": GRID_SIZE,
        "n_cars": Slider("Number of Cars", 5, 1, 20, 1),
        "n_traffic_lights": Slider("Number of Traffic Lights", 2, 1, 5, 1),
    }

    server = ModularServer(
        TrafficModel,
        [grid, traffic_chart, density_chart],
        "Traffic Simulation",
        model_params,
    )

    return server
