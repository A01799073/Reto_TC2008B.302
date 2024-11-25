from flask import Flask, request, jsonify
from flask_cors import CORS
from randomAgents.model import CityModel
from randomAgents.agents import Car, Traffic_Light, Road, Obstacle, Destination

# Size of the board:
number_agents = 10
width = 20
height = 20
city_model = None
current_step = 0

# Inicialización del servidor Flask
app = Flask("Traffic example")
cors = CORS(app, origins=['http://localhost'])


# Ruta para inicializar el modelo
@app.route('/init', methods=['POST'])
def init_model():
    global city_model, number_agents, width, height, current_step
    try:
        data = request.get_json()
        number_agents = int(data.get('NAgents', 10))
        width = int(data.get('width', 20))
        height = int(data.get('height', 20))
        current_step = 0

        # Crear el modelo de ciudad
        city_model = CityModel(number_agents)
        return jsonify({"message": "Modelo inicializado con éxito"})
    except Exception as e:
        return jsonify({"message": f"Error al inicializar el modelo: {str(e)}"}), 500

# Ruta para obtener posiciones de autos
@app.route('/getCars', methods=['GET'])

def get_cars():
    try:
        car_positions = [
            {"id": car.unique_id, "x": pos[0], "y": 1, "z": pos[1]}
            for car, pos in city_model.grid.coord_iter()
            if isinstance(car, Car)
        ]
        return jsonify({"positions": car_positions})
    except Exception as e:
        return jsonify({"message": f"Error al obtener autos: {str(e)}"}), 500

# Ruta para obtener posiciones de semáforos
@app.route('/getTrafficLights', methods=['GET'])
def get_traffic_lights():
    try:
        traffic_light_positions = [
            {"id": light.unique_id, "x": pos[0], "y": 1, "z": pos[1], "state": light.state}
            for light, pos in city_model.grid.coord_iter()
            if isinstance(light, Traffic_Light)
        ]
        return jsonify({"positions": traffic_light_positions})
    except Exception as e:
        return jsonify({"message": f"Error al obtener semáforos: {str(e)}"}), 500

# Ruta para obtener posiciones de carreteras
@app.route('/getRoads', methods=['GET'])
def get_roads():
    try:
        road_positions = [
            {"id": road.unique_id, "x": pos[0], "y": 0, "z": pos[1], "direction": road.direction}
            for road, pos in city_model.grid.coord_iter()
            if isinstance(road, Road)
        ]
        return jsonify({"positions": road_positions})
    except Exception as e:
        return jsonify({"message": f"Error al obtener carreteras: {str(e)}"}), 500

# Ruta para obtener posiciones de obstáculos
@app.route('/getObstacles', methods=['GET'])
def get_obstacles():
    try:
        obstacle_positions = [
            {"id": obs.unique_id, "x": pos[0], "y": 1, "z": pos[1]}
            for obs, pos in city_model.grid.coord_iter()
            if isinstance(obs, Obstacle)
        ]
        return jsonify({"positions": obstacle_positions})
    except Exception as e:
        return jsonify({"message": f"Error al obtener obstáculos: {str(e)}"}), 500

# Ruta para avanzar el modelo un paso
@app.route('/update', methods=['GET'])
def update_model():
    global current_step
    try:
        city_model.step()
        current_step += 1
        return jsonify({"message": f"Modelo actualizado a paso {current_step}"})
    except Exception as e:
        return jsonify({"message": f"Error al actualizar el modelo: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host="localhost", port=8585, debug=True)