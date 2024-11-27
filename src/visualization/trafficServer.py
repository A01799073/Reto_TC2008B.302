from mesa.visualization.modules import CanvasGrid, ChartModule, TextElement
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import Slider
from flask import Flask, request, jsonify
from flask_cors import CORS
from src.model.city_model import CityModel
from src.agents.car import Car
from src.agents.road import Road
from src.agents.traffic_light import Traffic_Light
from src.agents.destination import Destination
from src.agents.obstacle import Obstacle

# Global variables for Flask server
number_agents = 100
width = 28
height = 28
cityModel = None
currentStep = 0

# Flask application
app = Flask("Traffic Simulation")
CORS(app)


@app.route("/init", methods=["POST"])
def init_model():
    global cityModel, currentStep, number_agents

    if request.method == "POST":
        try:
            number_agents = int(request.json.get("NAgents", 1))
            currentStep = 0
            cityModel = CityModel(number_agents)
            return jsonify({"message": "Model initialized"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500


@app.route("/state", methods=["GET"])
def get_state():
    if cityModel is None:
        return jsonify({"error": "Model not initialized"}), 400

    # Only get cars and traffic lights
    cars = []
    traffic_lights = []

    for agent in cityModel.schedule.agents:
        if isinstance(agent, Car):
            pos = agent.pos
            cars.append({"id": str(agent.unique_id), "x": pos[0], "y": 0, "z": pos[1]})
        elif isinstance(agent, Traffic_Light):
            pos = agent.pos
            traffic_lights.append(
                {
                    "id": str(agent.unique_id),
                    "x": pos[0],
                    "y": 0,
                    "z": pos[1],
                    "state": agent.state,
                }
            )

    return jsonify({"cars": cars, "traffic_lights": traffic_lights})


@app.route("/step", methods=["POST"])
def step_model():
    global currentStep, cityModel
    if cityModel is None:
        return jsonify({"error": "Model not initialized"}), 400

    try:
        cityModel.step()
        currentStep += 1
        return jsonify(
            {
                "message": f"Model updated to step {currentStep}",
                "currentStep": currentStep,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/info", methods=["GET"])
def get_info():
    if cityModel is None:
        return jsonify({"error": "Model not initialized"}), 400

    return jsonify(
        {
            "number_of_cars": len(
                [agent for agent in cityModel.schedule.agents if isinstance(agent, Car)]
            ),
            "number_of_traffic_lights": len(
                [
                    agent
                    for agent in cityModel.schedule.agents
                    if isinstance(agent, Traffic_Light)
                ]
            ),
            "grid_size": cityModel.grid.width * cityModel.grid.height,
            "current_step": currentStep,
        }
    )


@app.route("/reset", methods=["POST"])
def reset_simulation():
    global cityModel, currentStep
    if cityModel is not None:
        cityModel = CityModel(number_agents)
        currentStep = 0
        return jsonify({"message": "Simulation reset"})
    return jsonify({"error": "Model not initialized"}), 400


def agent_portrayal(agent):
    if agent is None:
        return

    portrayal = {"Shape": "rect", "Filled": "true", "Layer": 1, "w": 1, "h": 1}

    if isinstance(agent, Road):
        portrayal["Color"] = "grey"
        portrayal["Layer"] = 0
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


class CarInfoElement(TextElement):
    def __init__(self):
        pass

    def render(self, model):
        current_cars = len(
            [agent for agent in model.schedule.agents if isinstance(agent, Car)]
        )
        return f"Current Cars: {current_cars} / Maximum Cars: {model.num_agents}"


def create_server():
    # Get grid dimensions from the map file
    with open("city_files/2022_base.txt") as baseFile:
        lines = baseFile.readlines()
        width = len(lines[0]) - 1
        height = len(lines)

    grid = CanvasGrid(agent_portrayal, width, height, 500, 500)
    car_info = CarInfoElement()
    traffic_chart = ChartModule(
        [
            {"Label": "Average_Speed", "Color": "#00FF00"},
            {"Label": "Stopped_Cars", "Color": "#FF00FF"},
        ]
    )
    density_chart = ChartModule(
        [
            {"Label": "Traffic_Density", "Color": "#0000FF"},
        ]
    )

    model_params = {
        "N": Slider("Number of Cars", 1, 1, 150, 1),
    }

    mesa_server = ModularServer(
        CityModel,
        [car_info, grid, traffic_chart, density_chart],
        "Traffic Simulation",
        model_params,
    )

    return mesa_server, app


if __name__ == "__main__":
    mesa_server, flask_app = create_server()
    # Run Mesa server on port 8521
    mesa_server.port = 8521
    # Run Flask server on port 8585
    flask_app.run(host="localhost", port=8585, debug=True)
