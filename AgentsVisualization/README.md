## Dependencies

### Mesa flask server

You must have the following dependencies in your python installation, or in a virtual environment (usually with venv).

- Python
- Mesa version 2.4.0: pip install mesa==2.4.0
- Flask: pip install flask
- Flask Cors: pip install flask_cors

### Visualization server

The following are installed when you use `npm i` inside of the **visualization** folder.

- Lil-gui: lil-gui ^0.19.2
- Twgl: twgl.js ^5.5.4
- Vite: vite ^5.3.4

## Instructions to run the local server and the application

- Make sure that you have the dependencies installed.
- Move to the Proyect folder 
- Run the flask server:

```
python -m src.visualization.trafficServer                                                           ─╯
```

- The script is listening to port 8585 (http://localhost:8585). **Double check that your server is launching on that port.**

## Running the WebGL application

- Move to the `visualization` folder.
- Make sure that you installed the depoendencies with `npm i`.
- Run the vite server:

```
npx vite
```