'use strict';

import * as twgl from 'twgl.js'; // Librería para el manejo de WebGL
import { GUI } from 'lil-gui';

// Modelos 3D
import roadModel from './3D_models/Simple_Funcionales/roadbasic.obj?raw';
import trafficLightModel from './3D_models/Simple_Funcionales/semaforo_cuadrado.obj?raw';
import buildModel from './3D_models/Simple_Funcionales/build_cuadrada.obj?raw';

// Vertex Shader
const vsGLSL = `#version 300 es
in vec4 a_position;
in vec3 a_normal;

uniform mat4 u_worldViewProjection;
uniform mat4 u_world;

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
out vec4 outColor;

void main() {
    vec3 normal = normalize(v_normal);
    vec3 lightDir = normalize(vec3(1, 1, 1));
    float light = max(dot(normal, lightDir), 0.0);
    outColor = vec4(vec3(0.7, 0.7, 0.7) * light, 1);
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
let cameraPosition = { x: 0, y: 10, z: 10 };

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

                const [posIndex, normIndex] = part.split('/').map(i => parseInt(i, 10) - 1);
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

// Función para cargar el mapa y procesarlo
async function loadMap(mapPath) {
    const response = await fetch(mapPath);
    const mapText = await response.text();
    const lines = mapText.split('\n');

    const size = 2; // Tamaño de cada celda en la cuadrícula
    lines.forEach((line, row) => {
        [...line].forEach((char, col) => {
            const x = col * size;
            const z = row * size;

            if (char === 'v') {
                objects.push(new Object3D('road', `road-${row}-${col}`, [x, 0, z]));
            } else if (char === '#') {
                objects.push(new Object3D('building', `building-${row}-${col}`, [x, 0, z], [0, 0, 0], [1, 2, 1]));
            } else if (char === 'S' || char === 's') {
                objects.push(new Object3D('trafficLight', `light-${row}-${col}`, [x, 0, z]));
            }
        });
    });
}

// Configuración principal de la aplicación
async function main() {
    const canvas = document.querySelector('canvas');
    gl = canvas.getContext('webgl2');

    if (!gl) {
        console.error("WebGL 2 no está soportado en este navegador.");
        return;
    }

    // Programa de shaders
    programInfo = twgl.createProgramInfo(gl, [vsGLSL, fsGLSL]);

    // Procesa los modelos OBJ
    const roadData = parseOBJ(roadModel);
    const trafficLightData = parseOBJ(trafficLightModel);
    const buildingData = parseOBJ(buildModel);

    //------Sí corren los datos------
    //console.log('Datos de carretera:', roadData);
    //console.log('Datos del semáforo:', trafficLightData);

    // Cargar mapa
    await loadMap('./city_files/2022_base.txt');

    // Crea los buffers solo después de inicializar WebGL
    buffers = {
        //road: twgl.createBufferInfoFromArrays(gl, roadData),
        //trafficLight: twgl.createBufferInfoFromArrays(gl, trafficLightData),
        building: twgl.createBufferInfoFromArrays(gl, buildingData),
    };

    objects.push(new Object3D('building', 'building1', [0, 0, 0]));

    // Configura la interfaz de usuario
    setupUI();

    // Renderiza la escena
    render();
}
/*
// Función para dibujar carreteras
function drawRoads(viewProjection) {
    const roadBuffer = buffers.road;
    objects
        .filter(obj => obj.type === "road")
        .forEach(road => drawObject(road, roadBuffer, programInfo, viewProjection));
}

// Función para dibujar semáforos
function drawTrafficLights(viewProjection) {
    const lightBuffer = buffers.trafficLight;
    objects
        .filter(obj => obj.type === "trafficLight")
        .forEach(light => drawObject(light, lightBuffer, programInfo, viewProjection));
}
*/
// Función para dibujar edificios
function drawBuildings(viewProjection) {
    const buildingBuffer = buffers.building;
    objects
        .filter(obj => obj.type === "building")
        .forEach(building => drawObject(building, buildingBuffer, programInfo, viewProjection));
}
// Renderiza la escena
function render(time = 0) {
    time *= 0.001; // Convierte el tiempo a segundos

    // Configura el color de fondo del canvas
    gl.clearColor(0.3, 0.3, 0.3, 1.0); // Cambia el fondo a un gris oscuro
    // Limpia el canvas
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    gl.enable(gl.DEPTH_TEST);

    // Configuración de la cámara y la proyección
    const camera = twgl.m4.lookAt(
        [cameraPosition.x, cameraPosition.y, cameraPosition.z],
        [0, 0, 0],
        [0, 1, 0]
    );
    const projection = twgl.m4.perspective(
        Math.PI / 4,
        gl.canvas.clientWidth / gl.canvas.clientHeight,
        0.5,
        1000
    );
    const viewProjection = twgl.m4.multiply(projection, twgl.m4.inverse(camera));

    gl.useProgram(programInfo.program); // Asegura que se está usando el programa correcto

//   drawRoads(viewProjection);
    drawBuildings(viewProjection);
//    drawTrafficLights(viewProjection);

    requestAnimationFrame(render);
}


function drawObject(obj, bufferInfo, programInfo, viewProjection) {
    const world = twgl.m4.identity();
    twgl.m4.translate(world, obj.position, world);
    twgl.m4.rotateY(world, obj.rotation[1], world);
    twgl.m4.scale(world, obj.scale, world);

    const matrix = twgl.m4.multiply(viewProjection, world);

    twgl.setUniforms(programInfo, {
        u_worldViewProjection: matrix,
        u_world: world,
    });

    twgl.setBuffersAndAttributes(gl, programInfo, bufferInfo);
    twgl.drawBufferInfo(gl, bufferInfo);
}

// Configura la interfaz gráfica
function setupUI() {
    const gui = new GUI();
    gui.add(cameraPosition, 'x', -100, 100).name("Posición X");
    gui.add(cameraPosition, 'y', -100, 100).name("Posición Y");
    gui.add(cameraPosition, 'z', -100, 100).name("Posición Z");
}

// Inicia la aplicación
main();