'use strict';

import * as twgl from 'twgl.js'; // Librería para el manejo de WebGL
import { GUI } from 'lil-gui';

// Modelos 3D
import roadModel from './3D_models/Simple_Funcionales/roadnew.obj?raw';
import trafficLightModel from './3D_models/Simple_Funcionales/semaforo_cuadrado.obj?raw';
import buildModel from './3D_models/Simple_Funcionales/buildnew.obj?raw';
//import carModel from './3D_models/Auto/car.obj.?raw';

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
    //vec3 lightDir = normalize(vec3(1, 1, 1));
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

// Define el URI del servidor para agentes (si lo necesitas más adelante)
const agent_server_uri = "http://localhost:8585";

// Variables relacionadas con WebGL
let gl, programInfo, buffers;

// Arrays para almacenar objetos en la escena
const objects = [];

// Define la posición inicial de la cámara
let cameraPosition = { x: 50, y: 50, z: 50 };

// Parámetros de iluminación direccional
const lightDirection = [0, -1, -1]; // Dirección de la luz (simulando el sol)
const lightColor = [1.5, 1.5, 1.5]; // Luz amarilla
const objectColors = {
  road: [0.8, 0.8, 0.8], // Gris claro para carreteras
  building: [0.0, 0.0, 0.8], // Azul fuerte para edificios
  trafficLight: [0.8, 0.2, 0.2], // Rojo para semáforos
};
// Representación del mapa como una variable
const mapData = `
v<<<<<<<<<<<<<<<<<s<<<<<
v<<<<<<<<<<<<<<<<<s<<<<^
vv#D#########vv#SS###D^^
vv###########vv#^^####^^
vv##########Dvv#^^D###^^
vv#D#########vv#^^####^^
vv<<<<<<s<<<<vv#^^####^^
vv<<<<<<s<<<<vv#^^####^^
vv####SS#####vv#^^####^^
vvD##D^^####Dvv#^^####^^
vv####^^#####vv#^^D###^^
SS####^^#####vv#^^####^^
vvs<<<<<<<<<<<<<<<<<<<<<
vvs<<<<<<<<<<<<<<<<<<<<<
vv##########vv###^^###^^
vv>>>>>>>>>>>>>>>>>>>s^^
vv>>>>>>>>>>>>>>>>>>>s^^
vv####vv##D##vv#^^####SS
vv####vv#####vv#^^####^^
vv####vv#####vv#^^###D^^
vv###Dvv####Dvv#^^####^^
vv####vv#####vv#^^####^^
vv####SS#####SS#^^#D##^^
v>>>>s>>>>>>s>>>>>>>>>>^
>>>>>s>>>>>>s>>>>>>>>>>^
`;

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
      // Vertices
      positions.push(...parts.slice(1).map(Number));
    } else if (type === 'vn') {
      // Normals
      normals.push(...parts.slice(1).map(Number));
    } else if (type === 'f') {
      // Faces (indices)
      const face = parts.slice(1);
      const faceIndices = [];
      face.forEach(part => {
        const [posIndex, , normIndex] = part.split('/').map(i => parseInt(i, 10) - 1);
        positionData.push(...positions.slice(posIndex * 3, posIndex * 3 + 3));
        if (normIndex !== undefined) {
          normalData.push(...normals.slice(normIndex * 3, normIndex * 3 + 3));
        }
        faceIndices.push(positionData.length / 3 - 1);
      });

      // Generate triangles for the face
      for (let i = 1; i < faceIndices.length - 1; i++) {
        indices.push(faceIndices[0], faceIndices[i], faceIndices[i + 1]);
      }
    }
  });

  // Add error checking for empty arrays
  if (positionData.length === 0) {
    console.error('No vertex data found in OBJ file');
    return null;
  }

  // If no normals were provided, generate default ones
  if (normalData.length === 0) {
    console.warn('No normal data found, generating default normals');
    for (let i = 0; i < positionData.length; i += 3) {
      normalData.push(0, 1, 0); // Default normal pointing up
    }
  }

  // Add debugging information
  console.log('Parsed OBJ:', {
    vertices: positionData.length / 3,
    normals: normalData.length / 3,
    indices: indices.length
  });

  return {
    a_position: {
      numComponents: 3,
      data: new Float32Array(positionData),
    },
    a_normal: {
      numComponents: 3,
      data: new Float32Array(normalData),
    },
    indices: {
      numComponents: 3,
      data: new Uint16Array(indices),
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
  if (!gl) {
    console.error('WebGL 2 not supported');
    return;
  }

  console.log('Loading models...');
  console.log('Road model length:', roadModel.length);
  console.log('Traffic light model length:', trafficLightModel.length);
  console.log('Building model length:', buildModel.length);

  // Program creation
  programInfo = twgl.createProgramInfo(gl, [vsGLSL, fsGLSL]);
  if (!programInfo) {
    console.error('Failed to create shader program');
    return;
  }

  // Parse models
  console.log('Parsing models...');
  const roadData = parseOBJ(roadModel);
  const trafficLightData = parseOBJ(trafficLightModel);
  const buildingData = parseOBJ(buildModel);

  // Verify parsed data
  if (!roadData || !trafficLightData || !buildingData) {
    console.error('Failed to parse one or more models');
    return;
  }

  try {
    console.log('Creating buffers...');
    buffers = {
      road: twgl.createBufferInfoFromArrays(gl, roadData),
      trafficLight: twgl.createBufferInfoFromArrays(gl, trafficLightData),
      building: twgl.createBufferInfoFromArrays(gl, buildingData),
    };

    // Verify buffer creation
    Object.entries(buffers).forEach(([key, buffer]) => {
      if (!buffer || !buffer.attribs) {
        console.error(`Failed to create buffer for ${key}`);
      } else {
        console.log(`Successfully created buffer for ${key}`);
      }
    });
  } catch (error) {
    console.error('Error creating buffers:', error);
    return;
  }

  processMap();
  setupUI();
  render();
}

// Función para dibujar carreteras
function drawRoads(viewProjection) {
  const roadBuffer = buffers.road;
  const roads = objects.filter(obj => obj.type === "road");
  roads.forEach(road => drawObject(road, roadBuffer, programInfo, viewProjection, objectColors.road));
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

function render() {
  gl.clearColor(0.0, 0.0, 0.0, 1.0);
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
  gl.enable(gl.DEPTH_TEST);

  const camera = twgl.m4.lookAt(
    [cameraPosition.x, cameraPosition.y, cameraPosition.z],
    [0, 0, 0],
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

  drawRoads(viewProjection);
  drawBuildings(viewProjection);
  drawTrafficLights(viewProjection);

  requestAnimationFrame(render);
}

function drawObject(obj, bufferInfo, programInfo, viewProjection, color) {
  // Check if bufferInfo is valid
  if (!bufferInfo || !bufferInfo.attribs) {
    console.error('Invalid buffer info for object:', obj.type);
    return;
  }

  const world = twgl.m4.identity();
  twgl.m4.translate(world, obj.position, world);
  twgl.m4.rotateY(world, obj.rotation[1], world);
  twgl.m4.scale(world, obj.scale, world);

  const matrix = twgl.m4.multiply(viewProjection, world);
  const worldInverseTranspose = twgl.m4.transpose(twgl.m4.inverse(world));

  try {
    twgl.setBuffersAndAttributes(gl, programInfo, bufferInfo);
    twgl.setUniforms(programInfo, {
      u_worldViewProjection: matrix,
      u_world: world,
      u_worldInverseTranspose: worldInverseTranspose,
      u_lightDirection: lightDirection,
      u_lightColor: lightColor,
      u_objectColor: color,
    });

    // Add error checking before drawing
    if (bufferInfo.numElements > 0) {
      twgl.drawBufferInfo(gl, bufferInfo);
    } else {
      console.error('Buffer has no elements:', obj.type);
    }
  } catch (error) {
    console.error('Error drawing object:', obj.type, error);
  }
}

// Configura la interfaz gráfica
function setupUI() {
  const gui = new GUI();
  gui.add(cameraPosition, 'x', -200, 200).name("Posición X");
  gui.add(cameraPosition, 'y', -200, 200).name("Posición Y");
  gui.add(cameraPosition, 'z', -200, 200).name("Posición Z");
}

// Inicia la aplicación
main();
