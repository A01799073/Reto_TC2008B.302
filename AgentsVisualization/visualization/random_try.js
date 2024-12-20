'use strict';

import * as twgl from 'twgl.js'; // Librería para el manejo de WebGL
import { GUI } from 'lil-gui';

// Importación del mapa
import mapData from '../../city_files/2022_base.txt?raw'

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
out vec3 v_position;

void main() {
    gl_Position = u_worldViewProjection * a_position;
    v_normal = mat3(u_world) * a_normal;
    v_position = (u_world * a_position).xyz;  // Set the position in world space

}
`;

// Fragment Shader
const fsGLSL = `#version 300 es
precision highp float;

in vec3 v_normal;
in vec3 v_position;  // Nueva variable para la posición del fragmento


uniform vec3 u_lightDirection; // Dirección de la luz
uniform vec3 u_lightColor;     // Color de la luz
uniform vec3 u_objectColor;    // Color base del objeto

//Luces para semaforos
uniform vec3 u_pointLightPosition; // Posición del punto de luz
uniform vec3 u_pointLightColor;   // Color del punto de luz

out vec4 outColor;

void main() {

  //Luces direccionales
    vec3 normal = normalize(v_normal);
    vec3 lightDir = normalize(u_lightDirection); // Usa la dirección de luz uniforme

     // Cálculo de iluminación difusa
    float diff = max(dot(normal, lightDir), 0.0);

    // Color final combinando luz y color base
    vec3 diffuse = diff * u_lightColor * u_objectColor;

    // Mezcla con un término ambiental para iluminar sombras
    vec3 ambient = 0.2 * u_objectColor;

    vec3 totalLighting = ambient + diffuse;

    //outColor = vec4(diffuse + ambient, 1.0); // Combina difusión y luz ambiental

    // Calcular la contribución de la luz puntual
    vec3 lightToFrag = u_pointLightPosition - v_position;
    float distance = length(lightToFrag);
    float attenuation = 1.0 / (distance * distance);  // Atenuación por distancia
    vec3 pointLightColor = attenuation * u_pointLightColor;

    // Cálculo de la luz puntual
    vec3 pointLightDiffuse = max(dot(normal, normalize(lightToFrag)), 0.0) * pointLightColor * u_objectColor;
    
    // Combinación de luz ambiental, difusa y puntual
    totalLighting += pointLightDiffuse;

    outColor = vec4(totalLighting, 1.0);
}
`;

// Variables
let cars = [];
let trafficLights = [];
let frameCount = 0;

// Define el URI del servidor para agentes (si lo necesitas más adelante)
const agent_server_uri = "http://localhost:8585";

// Variables relacionadas con WebGL
let gl, programInfo, buffers;

// Arrays para almacenar objetos en la escena
let objects = [];  // was const objects = []

// Define la posición inicial de la cámara
let cameraPosition = { x: 80, y: 322, z: 77 };
let cameraTarget = { x: 80, y: -8000, z: -46 };     // Punto al que apunta la cámara


// Parámetros de iluminación direccional
const lightDirection = [1, 1, 0]; // Dirección de la luz (simulando el sol)- amanecer
/*
  Si quieres simular un atardecer es = [-1,1,0]
  Si quieres simular el medio día es = [0,-1,0]
*/

let lightColor = [1.0, 1.0, 1.0]; // Luz inicial /tono cálido

const objectColors = {
  road: [0.4, 0.4, 0.6],
  specialRoad: [1.0, 1.0, 0.0],
  building: [0.0, 0.0, 0.8],
  trafficLight: [1, 1, 1],
  car: [0.0, 0.0, 0.0], // Bright red for better visibility
};

// Clase para representar objetos 3D
class Object3D {
  constructor(type, id, position = [0, 0, 0], rotation = [0, 0, 0], scale = [1, 1, 1], isPointLight = false, state=false) {
    this.type = type; // Tipo de objeto (carretera, semáforo, etc.)
    this.id = id; // Identificador único
    this.position = position;
    this.rotation = rotation;
    this.scale = scale;
    this.matrix = twgl.m4.identity();
    this.isPointLight = isPointLight; // Nueva propiedad para las luces de semáforo
    this.state = state;
  }
}

let simulationInitialized = false;
// Initialize the simulation
async function initSimulation(nAgents) {
  try {
    //console.log('Initializing simulation with', nAgents, 'agents');
    const response = await fetch(`${agent_server_uri}/init`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ NAgents: nAgents })
    });
    if (!response.ok) throw new Error('Failed to initialize simulation');
    simulationInitialized = true;
    //console.log('Simulation initialized successfully');
    return await response.json();
  } catch (error) {
    console.error('Error initializing simulation:', error);
    simulationInitialized = false;
  }
}

// Add check in stepSimulation
async function stepSimulation() {
  if (!simulationInitialized) {
    //console.log('Simulation not initialized, initializing now...');
    await initSimulation(100);
    return;
  }

  try {
    const response = await fetch(`${agent_server_uri}/step`, {
      method: 'POST'
    });
    if (!response.ok) {
      simulationInitialized = false; // Reset if we get an error
      throw new Error('Failed to step simulation');
    }
    return await response.json();
  } catch (error) {
    console.error('Error stepping simulation:', error);
  }
}
// Get current state
// Add check in getState
async function getState() {
  if (!simulationInitialized) {
    //console.log('Simulation not initialized, initializing now...');
    await initSimulation(100);
    return;
  }

  try {
    const response = await fetch(`${agent_server_uri}/state`);
    if (!response.ok) {
      simulationInitialized = false; // Reset if we get an error
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error getting state:', error);
    return null;
  }
}

async function updateSimulation() {
  try {
    const response = await fetch(`${agent_server_uri}/state`);
    if (!response.ok) throw new Error('Network response was not ok');

    const data = await response.json();

    cars = data.cars.map(car => {
      const carObject = new Object3D('car', car.id, [car.x, car.y, car.z]);
      return carObject;
    });
    //cars = data.cars.map(car => new Object3D('car', car.id, [car.x, car.y, car.z]));
    trafficLights = data.traffic_lights.map(light => {
      const tLight = new Object3D('trafficLight', light.id, [light.x, light.y, light.z]);
      tLight.state = light.state;
      console.log("Traffic Lights State:", trafficLights);
      return tLight;
    });

  } catch (error) {
    console.error('Error updating simulation:', error);
  }
}

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
// Función para actualizar los valores de la luz:
function updateLighting() {
  twgl.setUniforms(programInfo, {
    u_lightDirection: lightDirection,
    u_lightColor: lightColor,
  });
}

function updateTrafficLights() {
  // Actualiza la luz puntual para cada semáforo
  trafficLights.forEach(tLight => {
      console.log("Updating point light color for traffic light:", tLight.state ? [0.0, 1.0, 0.0] : [1.0, 0.0, 0.0]);
      if (tLight.isPointLight) {
          const pointLightColor = tLight.state ? [0.0, 1.0, 0.0] : [1.0, 0.0, 0.0];  // Verde o Rojo
          twgl.setUniforms(programInfo, {
              u_pointLightPosition: tLight.position,  // Posición de la luz puntual
              u_pointLightColor: pointLightColor      // Color de la luz puntual
          });
      }
  });
}

// Procesa el mapa para crear los objetos
function processMap() {
  const lines = mapData.trim().split('\n');
  const size = 5; // Grid cell size

  lines.forEach((line, row) => {
    [...line].forEach((char, col) => {
      const x = col * size;
      const z = row * size;  // Make this match the car coordinates

      if (char === 'v' || char === '<' || char === '>' || char === '^') {
        objects.push(new Object3D('road', `road-${row}-${col}`, [x, 0, z]));
      } else if (char === 'D') {
        objects.push(new Object3D('specialRoad', `specialRoad-${row}-${col}`, [x, 0, z]));
      } else if (char === '#') {
        objects.push(new Object3D('building', `building-${row}-${col}`, [x, 0, z], [0, 0, 0], [0.75, 1, 0.75]));
      // } else if (char === 'S' || char === 's') {
      //   objects.push(new Object3D('trafficLight', `light-${row}-${col}`, [x, 0, z], [0, 0, 0], [0.7, 0.5, 0.7]));
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
  //const carData = createCubeData();
  const carData=parseOBJ(carModel)

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
    await initSimulation(100);
    if (!simulationInitialized) {
      throw new Error('Failed to initialize simulation');
    }

    setupUI();
    render();
  } catch (error) {
    console.error('Error during initialization:', error);
  }
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
  console.log(lights)
  lights.forEach(light => {
    console.log('Traffic light state:', light.state); // Verifica el estado del semáforo
    drawObject(light, lightBuffer, programInfo, viewProjection, objectColors.trafficLight);
  });
}

// Función para dibujar edificios
function drawBuildings(viewProjection) {
  const buildingBuffer = buffers.building;
  const buildings = objects.filter(obj => obj.type === "building");
  buildings.forEach(building => drawObject(building, buildingBuffer, programInfo, viewProjection, objectColors.building));
}


// Add drawCars function (similar to your other draw functions)
function drawCars(viewProjection) {
  if (!buffers.car) {
    console.error('Car buffer is missing');
    return;
  }

  const cars = objects.filter(obj => obj.type === "car");

  cars.forEach(car => {
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
    console.log('Traffic light state:', obj.state); // Verifica el estado del semáforo
    finalColor = obj.state ? [0.0, 0.8, 0.0] : [0.8, 0.0, 0.0]; // Green when true, red when false
  }

  // Si el objeto es una fuente de luz (point light), asignamos la luz correspondiente
  if (obj.isPointLight) {
    // Cambiar para agregar un punto de luz (point light) que afecte a la escena
    twgl.setUniforms(programInfo, {
      u_pointLightPosition: obj.position,  // Posición del punto de luz
      u_lightColor: finalColor,            // Color de la luz del semáforo
    });
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

async function render() {
  try {
    if (!simulationInitialized) {
      //console.log('Simulation not initialized, retrying...');
      await initSimulation(100);
      if (!simulationInitialized) {
        requestAnimationFrame(render);
        return;
      }
    }

    await stepSimulation();
    const state = await getState();

    if (state && state.cars && state.traffic_lights) {
      // Verificar el estado de los semáforos en cada ciclo de renderizado
      state.traffic_lights.forEach(lightData => {
        // console.log('Traffic light state in render loop:', lightData.state);
        const webGLPosition = [
          (lightData.x * 5),
          1,
          (29 - lightData.z) * 5  // Invert and offset Z coordinate
        ];

        const light = new Object3D(
          "trafficLight",
          lightData.id,
          webGLPosition,
          [0, 0, 0],
          [0.5, 0.5, 0.5],
          lightData.state
          // Made cars smaller
        );
        objects.push(light);
        
        
      });

      // Remove all existing cars
      const nonCarObjects = objects.filter(obj => obj.type !== 'car');
      objects.length = 0;
      objects.push(...nonCarObjects);

      state.cars.forEach(carData => {
        // Log raw car data

        // Convert Mesa coordinates to WebGL coordinates
        // Invert both x and z
        const webGLPosition = [
          (carData.x * 5),
          1,
          (29 - carData.z) * 5  // Invert and offset Z coordinate
        ];

        const car = new Object3D(
          'car',
          carData.id,
          webGLPosition,
          [0, 0, 0],
          [0.5, 0.5, 0.5]  // Made cars smaller
        );
        objects.push(car);
        //console.log('Raw car data:', carData);
        //console.log('WebGL position:', webGLPosition);
      });

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
      drawCars(viewProjection);
    }

    // Add a small delay to avoid overwhelming the server
    await new Promise(resolve => setTimeout(resolve, 100));

    requestAnimationFrame(render);
  } catch (error) {
    console.error('Error in render loop:', error);
    simulationInitialized = false; // Reset on error
    requestAnimationFrame(render);
  }
}

// Configura la interfaz gráfica
function setupUI() {
  const gui = new GUI();
  const cameraFolder = gui.addFolder('Controles de Cámara');
  gui.add(cameraPosition, 'x', -500, 500).name("Posición X");
  gui.add(cameraPosition, 'y', -500, 500).name("Posición Y");
  gui.add(cameraPosition, 'z', -500, 500).name("Posición Z");

  // Controles para mover el objetivo de la cámara
  const targetFolder = gui.addFolder('Objetivo de Cámara');
  gui.add(cameraTarget, 'x', -500, 500).name("Target X");
  gui.add(cameraTarget, 'y', -8000, 8000).name("Target Y");
  gui.add(cameraTarget, 'z', -500, 500).name("Target Z");

  //Controles para la luz direccional:
  // Nueva carpeta para la luz direccional
  const lightFolder = gui.addFolder('Lighting - Direccional');
  lightFolder.add(lightDirection, '0', -1, 1).name("Dirección X");
  lightFolder.add(lightDirection, '1', -1, 1).name("Dirección Y");
  lightFolder.add(lightDirection, '2', -1, 1).name("Dirección Z");

  lightFolder.addColor({ color: lightColor }, 'color').name('Color de Luz').onChange(value => {
    lightColor = value;
    updateLighting(); // Re-aplica los cambios
  });

  cameraFolder.open();
  targetFolder.open();
  lightFolder.open();
}

// Inicia la aplicación
main();