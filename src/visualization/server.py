# src/visualization/server.py
from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import Slider
from ..model.city_model import CityModel
from ..agents.car import Car
from ..agents.road import Road
from ..agents.traffic_light import Traffic_Light
from ..agents.destination import Destination
from ..agents.obstacle import Obstacle


def agent_portrayal(agent):
    if agent is None:
        return
    portrayal = {"Shape": "rect", "Filled": "true", "Layer": 1, "w": 1, "h": 1}

    if isinstance(agent, Road):
        portrayal["Color"] = "grey"
        portrayal["Layer"] = 0
        # Añadir flechas según la dirección
        if agent.direction == "Up":
            portrayal["text"] = "↑"
        elif agent.direction == "Down":
            portrayal["text"] = "↓"
        elif agent.direction == "Left":
            portrayal["text"] = "←"
        elif agent.direction == "Right":
            portrayal["text"] = "→"
        portrayal["text_color"] = "white"

    if isinstance(agent, Destination):
        portrayal["Color"] = "lightgreen"
        portrayal["Layer"] = 0

    if isinstance(agent, Traffic_Light):
        portrayal["Color"] = "red" if not agent.state else "green"
        portrayal["Layer"] = 0
        portrayal["w"] = 0.8
        portrayal["h"] = 0.8

    if isinstance(agent, Obstacle):
        portrayal["Color"] = "cadetblue"
        portrayal["Layer"] = 0
        portrayal["w"] = 0.8
        portrayal["h"] = 0.8

    if isinstance(agent, Car):
        portrayal.update(
            {
                "Shape": "rect",
                "Color": "blue",
                "Layer": 2,
                "text_color": "white",
            }
        )

    return portrayal


def create_server():
    # Get grid dimensions from the map file
    with open("city_files/2022_base.txt") as baseFile:
        lines = baseFile.readlines()
        width = len(lines[0]) - 1
        height = len(lines)

    grid = CanvasGrid(agent_portrayal, width, height, 500, 500)

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
        "N": Slider("Number of Cars", 100, 1, 150, 1),
    }

    server = ModularServer(
        CityModel,
        [grid, traffic_chart, density_chart],
        "Traffic Simulation",
        model_params,
    )

    return server
