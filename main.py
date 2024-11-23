from src.visualization.server import create_server

if __name__ == "__main__":
    server = create_server()
    server.port = 8522  # The default
    server.launch()
