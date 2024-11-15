from trafficBase.model import CityModel
from trafficBase.agent import *


def test_basic_setup():
    try:
        # Test agent creation
        road = Road("road_1", None, "Left")
        traffic_light = Traffic_Light("light_1", None)
        destination = Destination("dest_1", None)
        obstacle = Obstacle("obs_1", None)
        car = Car("car_1", None)
        print("✓ All agents created successfully")

        # Test model creation
        model = CityModel(N=5)
        print("✓ Model created successfully")
        print(f"Grid dimensions: {model.grid.width} x {model.grid.height}")
        print(f"Number of traffic lights: {len(model.traffic_lights)}")

    except Exception as e:
        print(f"Error during testing: {e}")


if __name__ == "__main__":
    test_basic_setup()
