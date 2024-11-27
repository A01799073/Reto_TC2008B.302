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
let cameraPosition = { x: 50, y: 50, z: 50 };

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

            if (char === 'v' || char=== '<' || char=== '>'|| char === '^') {
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
        console.error("WebGL 2 no está soportado en este navegador.");
        return;
    }

    // Programa de shaders
    programInfo = twgl.createProgramInfo(gl, [vsGLSL, fsGLSL]);

    // Procesa los modelos OBJ
    const roadData = parseOBJ(roadModel);
    const trafficLightData = parseOBJ(trafficLightModel);
    const buildingData = parseOBJ(buildModel);

    //Mapa
    processMap();

    // Crea los buffers solo después de inicializar WebGL
    buffers = {
        road: twgl.createBufferInfoFromArrays(gl, roadData),
        trafficLight: twgl.createBufferInfoFromArrays(gl, trafficLightData),
        building: twgl.createBufferInfoFromArrays(gl, buildingData),
    };

    // Configura la interfaz de usuario
    setupUI();
    // Renderiza la escena
    render();
}

// Función para dibujar carreteras
function drawRoads(viewProjection) {
    const roadBuffer = buffers.road;
    const roads = objects.filter(obj => obj.type === "road");
    roads.forEach(road => drawObject(road, roadBuffer, programInfo, viewProjection));
}

// Función para dibujar semáforos
function drawTrafficLights(viewProjection) {
    const lightBuffer = buffers.trafficLight;
    const lights = objects.filter(obj => obj.type === "trafficLight");
    lights.forEach(light => drawObject(light, lightBuffer, programInfo, viewProjection));
}

// Función para dibujar edificios
function drawBuildings(viewProjection) {
    const buildingBuffer = buffers.building;
    const buildings = objects.filter(obj => obj.type === "building");
    buildings.forEach(building => drawObject(building, buildingBuffer, programInfo, viewProjection));
}

/*
//función para dibujar carros
function drawCars(viewProjection) {
    const carBuffer = buffers.trafficLight;
    const cars = objects.filter(obj => obj.type === "car");
    lights.forEach(light => drawObject(car, carBufferBuffer, programInfo, viewProjection));
*/

function render() {
    gl.clearColor(0.3, 0.3, 0.3, 1.0);
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
        3,
        400
    );
    const viewProjection = twgl.m4.multiply(projection, twgl.m4.inverse(camera));

    gl.useProgram(programInfo.program);

    drawRoads(viewProjection);
    drawBuildings(viewProjection);
    drawTrafficLights(viewProjection);

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
    gui.add(cameraPosition, 'x', -200, 200).name("Posición X");
    gui.add(cameraPosition, 'y', -200, 200).name("Posición Y");
    gui.add(cameraPosition, 'z', -200, 200).name("Posición Z");
}

// Inicia la aplicación
main();