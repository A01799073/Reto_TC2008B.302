'use strict';

import * as twgl from 'twgl.js'; // Librería para el manejo de WebGL
import { GUI } from 'lil-gui';

// Text
import mapData from '../../city_files/2022_base.txt?raw'

let cars = [];
let trafficLights = [];
let frameCount = 0;

// Modelos 3D
import roadModel from './3D_models/Simple_Funcionales/roadnew.obj?raw';
import specialModel from './3D_models/Simple_Funcionales/specialroad.obj?raw'
import trafficLightModel from './3D_models/Simple_Funcionales/semaforo_cuadrado.obj?raw';
import buildModel from './3D_models/Simple_Funcionales/build.newobj.obj?raw';
import carModel from './3D_models/Auto/car.obj?raw';


// Vertex Shadeor
const vsGLSL = `#version 300 es
in vec4 a_position;
in vec3 a_normal;

uniform mat4 u_worldViewProjection;
uniform mat4 u_world;
uniform mat4 u_worldInverseTranspose;

out vec3 v_normal;

void main() {
    gl_Position = u_worldViewProjection * a_position;
    v_normal = mat3(u_world) * a_normal;
}
`;

// Fragment Shader
const fsGLSL = `#version 300 es
precision highp float;

in vec3 v_normal;

uniform vec3 u_lightDirection; // Dirección de la luz
uniform vec3 u_lightColor;     // Color de la luz
uniform vec3 u_objectColor;    // Color base del objeto

out vec4 outColor;

void main() {
    vec3 normal = normalize(v_normal);
    vec3 lightDir = normalize(u_lightDirection); // Usa la dirección de luz uniforme


     // Cálculo de iluminación difusa
    float diff = max(dot(normal, lightDir), 0.0);

    // Color final combinando luz y color base
    vec3 diffuse = diff * u_lightColor * u_objectColor;

    // Mezcla con un término ambiental para iluminar sombras
    vec3 ambient = 0.2 * u_objectColor;

    outColor = vec4(diffuse + ambient, 1.0); // Combina difusión y luz ambiental

}
`;

// Clase para representar objetos 3D
class Object3D {
  constructor(type, id, position = [0, 0, 0], rotation = [0, 0, 0], scale = [1, 1, 1]) {
    this.type = type; // Tipo de objeto (carretera, semáforo, etc.)
    this.id = id; // Identificador único
    this.position = position;
    this.rotation = rotation;
    this.scale = scale;
    this.matrix = twgl.m4.identity();
  }
}

// Initialize the simulation
async function initSimulation(nAgents) {
  try {
    const response = await fetch(`${agent_server_uri}/init`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ NAgents: nAgents })
    });
    return await response.json();
  } catch (error) {
    console.error('Error initializing simulation:', error);
  }
}

// Get current state
async function getState() {
  try {
    const response = await fetch(`${agent_server_uri}/state`);
    return await response.json();
  } catch (error) {
    console.error('Error getting state:', error);
  }
}

async function updateSimulation() {
  try {
    const response = await fetch(`${agent_server_uri}/state`);
    if (!response.ok) throw new Error('Network response was not ok');

    const data = await response.json();

    cars = data.cars.map(car => new Object3D('car', car.id, [car.x, car.y, car.z]));
    trafficLights = data.traffic_lights.map(light => {
      const tLight = new Object3D('trafficLight', light.id, [light.x, light.y, light.z]);
      tLight.state = light.state;
      return tLight;
    });

  } catch (error) {
    console.error('Error updating simulation:', error);
  }
}
// Define el URI del servidor para agentes (si lo necesitas más adelante)
const agent_server_uri = "http://localhost:8585";

// Variables relacionadas con WebGL
let gl, programInfo, buffers;

// Arrays para almacenar objetos en la escena
const objects = [];

// Define la posición inicial de la cámara
let cameraPosition = { x: 34.6, y: 300, z: 27 };
let cameraTarget = { x: 35.6, y: 200, z: 40.4 };     // Punto al que apunta la cámara


// Parámetros de iluminación direccional
const lightDirection = [0, -1, -1]; // Dirección de la luz (simulando el sol)
const lightColor = [1.5, 1.5, 1.5]; // Luz amarilla
const objectColors = {
  road: [0.8, 0.8, 0.8],
  specialRoad: [1.0, 1.0, 0.0],
  building: [0.0, 0.0, 0.8],
  trafficLight: [0.8, 0.2, 0.2],
  car: [0.2, 0.2, 0.8], // Add car color (blue in this case)
};

// Función para parsear archivos OBJ
function parseOBJ(objText) {
  const positions = [];
  const normals = [];
  const indices = [];

  const positionData = [];
  const normalData = [];

  const lines = objText.split('\n');

  lines.forEach(line => {
    const parts = line.trim().split(/\s+/);
    const type = parts[0];
    if (type === 'v') {
      // Vértices
      positions.push(...parts.slice(1).map(Number));
    } else if (type === 'vn') {
      // Normales
      normals.push(...parts.slice(1).map(Number));
    } else if (type === 'f') {
      // Caras (índices)
      const face = parts.slice(1);
      const faceIndices = [];
      face.forEach(part => {

        const [posIndex, texIndex, normIndex] = part.split('/').map(i => parseInt(i, 10) - 1);
        positionData.push(...positions.slice(posIndex * 3, posIndex * 3 + 3));
        normalData.push(...normals.slice(normIndex * 3, normIndex * 3 + 3));
        faceIndices.push(positionData.length / 3 - 1);
      });

      // Genera triángulos para la cara
      for (let i = 1; i < faceIndices.length - 1; i++) {
        indices.push(faceIndices[0], faceIndices[i], faceIndices[i + 1]);
      }
    }
  });

  // Estructura requerida para graficar en
  return {
    a_position: {
      numComponents: 3,
      data: positionData,
    },
    a_normal: {
      numComponents: 3,
      data: normalData,
    },
    indices: {
      numComponents: 3,
      data: indices,
    },
  };
}

// Procesa el mapa para crear los objetos
function processMap() {
  const lines = mapData.trim().split('\n');
  const size = 5; // Tamaño de cada celda en la cuadrícula

  lines.forEach((line, row) => {
    [...line].forEach((char, col) => {
      const x = col * size;
      const z = row * size;
      //Agregar un road diferente para las destino?
      if (char === 'v' || char === '<' || char === '>' || char === '^') {
        objects.push(new Object3D('road', `road-${row}-${col}`, [x, 0, z],));
      } else if (char === 'D') {
        objects.push(new Object3D('specialRoad', `specialRoad-${row}-${col}`, [x, 0, z]));
      } else if (char === '#') {
        objects.push(new Object3D('building', `building-${row}-${col}`, [x, 0, z], [0, 0, 0], [0.75, 1, 0.75]));
      } else if (char === 'S' || char === 's') {
        objects.push(new Object3D('trafficLight', `light-${row}-${col}`, [x, 0, z], [0, 0, 0], [0.7, 0.5, 0.7]));
      }
    });
  });
}

// Configuración principal de la aplicación
async function main() {
  const canvas = document.querySelector('canvas');
  gl = canvas.getContext('webgl2');
  twgl.resizeCanvasToDisplaySize(gl.canvas);
  gl.viewport(0, 0, gl.canvas.clientWidth, gl.canvas.clientHeight)

  // Programa de shaders
  programInfo = twgl.createProgramInfo(gl, [vsGLSL, fsGLSL]);

  // Procesa los modelos OBJ
  const roadData = parseOBJ(roadModel);
  const specialRoadData = parseOBJ(specialModel);
  const trafficLightData = parseOBJ(trafficLightModel);
  const buildingData = parseOBJ(buildModel);
  const carData = parseOBJ(carModel);


  //Mapa
  processMap();

  // Initialize buffers object first
  buffers = {
    road: twgl.createBufferInfoFromArrays(gl, roadData),
    specialRoad: twgl.createBufferInfoFromArrays(gl, specialRoadData),
    trafficLight: twgl.createBufferInfoFromArrays(gl, trafficLightData),
    building: twgl.createBufferInfoFromArrays(gl, buildingData),
    car: twgl.createBufferInfoFromArrays(gl, carData),
  };

  try {
    const response = await fetch(`${agent_server_uri}/init`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ NAgents: 100 })
    });

    if (!response.ok) throw new Error('Failed to initialize simulation');
    await updateSimulation();
  } catch (error) {
    console.error('Error initializing simulation:', error);
  }

  setupUI();
  render();
}

// Función para dibujar carreteras
function drawRoads(viewProjection) {
  const roadBuffer = buffers.road;
  const roads = objects.filter(obj => obj.type === "road");
  roads.forEach(road => drawObject(road, roadBuffer, programInfo, viewProjection, objectColors.road));
}

// Función para dibujar carreteras especiales
function drawSpecialRoads(viewProjection) {
  const specialRoadBuffer = buffers.specialRoad;
  const specialRoads = objects.filter(obj => obj.type === "specialRoad");
  specialRoads.forEach(specialRoad => drawObject(specialRoad, specialRoadBuffer, programInfo, viewProjection, objectColors.specialRoad));
}

// Función para dibujar semáforos
function drawTrafficLights(viewProjection) {
  const lightBuffer = buffers.trafficLight;
  const lights = objects.filter(obj => obj.type === "trafficLight");
  lights.forEach(light => drawObject(light, lightBuffer, programInfo, viewProjection, objectColors.trafficLight));
}

// Función para dibujar edificios
function drawBuildings(viewProjection) {
  const buildingBuffer = buffers.building;
  const buildings = objects.filter(obj => obj.type === "building");
  buildings.forEach(building => drawObject(building, buildingBuffer, programInfo, viewProjection, objectColors.building));
}

/*
//función para dibujar carros
function drawCars(viewProjection) {
    const carBuffer = buffers.trafficLight;
    const cars = objects.filter(obj => obj.type === "car");
    lights.forEach(light => drawObject(car, carBufferBuffer, programInfo, viewProjection));
*/

async function render() {
  // Get state from backend
  const state = await getState();
  if (state && state.cars && state.traffic_lights) {
    // Update or create car objects
    state.cars.forEach(carData => {
      // Find if the car already exists in objects array
      let car = objects.find(obj => obj.type === 'car' && obj.id === carData.id);

      if (!car) {
        // Create new car object if it doesn't exist
        car = new Object3D('car', carData.id, [carData.x, carData.y, carData.z]);
        objects.push(car);
      } else {
        // Update existing car position
        car.position = [carData.x, carData.y, carData.z];
      }
    });

    // Update traffic light states
    state.traffic_lights.forEach(lightData => {
      // Find corresponding traffic light in objects array
      let light = objects.find(obj => obj.type === 'trafficLight' && obj.id === lightData.id);
      if (light) {
        // Update traffic light color based on state
        light.state = lightData.state;
        // You might want to update the color in the drawObject function based on state
      }
    });
  }

  // Regular WebGL rendering
  gl.clearColor(0.0, 0.0, 0.0, 1.0);
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
  gl.enable(gl.DEPTH_TEST);

  const camera = twgl.m4.lookAt(
    [cameraPosition.x, cameraPosition.y, cameraPosition.z],
    [cameraTarget.x, cameraTarget.y, cameraTarget.z],
    [0, 1, 0]
  );

  const projection = twgl.m4.perspective(
    Math.PI / 6,
    gl.canvas.clientWidth / gl.canvas.clientHeight,
    1,
    1000
  );
  const viewProjection = twgl.m4.multiply(projection, twgl.m4.inverse(camera));

  gl.useProgram(programInfo.program);

  // Draw all objects
  drawRoads(viewProjection);
  drawSpecialRoads(viewProjection);
  drawBuildings(viewProjection);
  drawTrafficLights(viewProjection);
  // Add function to draw cars
  drawCars(viewProjection);

  // Continue animation loop
  requestAnimationFrame(render);
}

// Add drawCars function (similar to your other draw functions)
function drawCars(viewProjection) {
  if (!buffers.car) return; // Make sure car buffer exists
  const cars = objects.filter(obj => obj.type === "car");
  cars.forEach(car => {
    // You might want to add a color for cars in your objectColors
    drawObject(car, buffers.car, programInfo, viewProjection, objectColors.car);
  });
}


function drawObject(obj, bufferInfo, programInfo, viewProjection, color) {
  const world = twgl.m4.identity();
  twgl.m4.translate(world, obj.position, world);
  twgl.m4.rotateY(world, obj.rotation[1], world);
  twgl.m4.scale(world, obj.scale, world);

  const matrix = twgl.m4.multiply(viewProjection, world);
  const worldInverseTranspose = twgl.m4.transpose(twgl.m4.inverse(world));

  // Modify color for traffic lights based on state
  let finalColor = color;
  if (obj.type === 'trafficLight' && obj.state !== undefined) {
    finalColor = obj.state ? [0.0, 0.8, 0.0] : [0.8, 0.0, 0.0]; // Green when true, red when false
  }

  twgl.setUniforms(programInfo, {
    u_worldViewProjection: matrix,
    u_world: world,
    u_worldInverseTranspose: worldInverseTranspose,
    u_lightDirection: lightDirection,
    u_lightColor: lightColor,
    u_objectColor: finalColor,
  });

  twgl.setBuffersAndAttributes(gl, programInfo, bufferInfo);
  twgl.drawBufferInfo(gl, bufferInfo);
}

// Configura la interfaz gráfica
function setupUI() {
  const gui = new GUI();
  const cameraFolder = gui.addFolder('Controles de Cámara');
  gui.add(cameraPosition, 'x', -200, 200).name("Posición X");
  gui.add(cameraPosition, 'y', -200, 300).name("Posición Y");
  gui.add(cameraPosition, 'z', -200, 300).name("Posición Z");

  // Controles para mover el objetivo de la cámara
  const targetFolder = gui.addFolder('Objetivo de Cámara');
  gui.add(cameraTarget, 'x', -200, 200).name("Target X");
  gui.add(cameraTarget, 'y', -200, 200).name("Target Y");
  gui.add(cameraTarget, 'z', -200, 200).name("Target Z");

  cameraFolder.open();
  targetFolder.open()
}

// Inicia la aplicación
main();
