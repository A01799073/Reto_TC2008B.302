'use strict';

import * as twgl from 'twgl.js'; // Librería para el manejo de WebGL
import { GUI } from 'lil-gui';

// Modelos 3D
import roadModel from '../3D_models/Road/road1_reto.obj?raw';
import trafficLightModel from '../3D_models/Semaforo/semaforo_horizontalobj.obj?raw';

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

// Arrays para almacenar objetos en la escena
const objects = [];

// Variables relacionadas con WebGL
let gl, programInfo, buffers;

// Define la posición inicial de la cámara
let cameraPosition = { x: 0, y: 9, z: 9 };

// Función para parsear archivos OBJ
function parseOBJ(objText) {
    const vertices = [];
    const normals = [];
    const indices = [];
    const lines = objText.split('\n');

    for (const line of lines) {
        const parts = line.trim().split(' ');
        switch (parts[0]) {
            case 'v': // Vértices
                vertices.push(...parts.slice(1).map(Number));
                break;
            case 'vn': // Normales
                normals.push(...parts.slice(1).map(Number));
                break;
            case 'f': // Caras (índices)
                const face = parts.slice(1).map(part => part.split('/')[0] - 1);
                indices.push(...face);
                break;
        }
    }
    return { vertices, normals, indices };
}

// Procesa los modelos OBJ
const roadData = parseOBJ(roadModel);
const trafficLightData = parseOBJ(trafficLightModel);

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

    // Crea los buffers para cada modelo
    buffers = {
        road: twgl.createBufferInfoFromArrays(gl, {
            a_position: { numComponents: 3, data: roadData.vertices },
            a_normal: { numComponents: 3, data: roadData.normals },
            indices: roadData.indices,
        }),
        trafficLight: twgl.createBufferInfoFromArrays(gl, {
            a_position: { numComponents: 3, data: trafficLightData.vertices },
            a_normal: { numComponents: 3, data: trafficLightData.normals },
            indices: trafficLightData.indices,
        }),
    };

    // Agrega objetos 3D a la escena
    objects.push(
        new Object3D("road", "road1", [0, 0, 0], [0, 0, 0], [1, 1, 1]),
        new Object3D("trafficLight", "light1", [5, 0, 0], [0, Math.PI / 2, 0], [0.5, 0.5, 0.5])
    );

    // Configura la interfaz de usuario
    setupUI();

    // Renderiza la escena
    render();
}

// Renderiza la escena
function render(time = 0) {
    time *= 0.001; // Convierte el tiempo a segundos

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
        100
    );
    const viewProjection = twgl.m4.multiply(projection, twgl.m4.inverse(camera));

    // Renderiza cada objeto
    objects.forEach(obj => {
        const world = twgl.m4.identity();
        twgl.m4.translate(world, obj.position, world);
        twgl.m4.rotateY(world, time, world); // Rotación animada
        twgl.m4.scale(world, obj.scale, world);

        const matrix = twgl.m4.multiply(viewProjection, world);

        // Selecciona el buffer según el tipo de objeto
        const bufferInfo = buffers[obj.type];

        twgl.setUniforms(programInfo, {
            u_worldViewProjection: matrix,
            u_world: world,
        });

        // Configura y dibuja el buffer
        twgl.setBuffersAndAttributes(gl, programInfo, bufferInfo);
        twgl.drawBufferInfo(gl, bufferInfo);
    });

    // Solicita el próximo cuadro
    requestAnimationFrame(render);
}

// Configura la interfaz gráfica
function setupUI() {
    const gui = new GUI();
    gui.add(cameraPosition, 'x', -50, 50).name("Posición X");
    gui.add(cameraPosition, 'y', -50, 50).name("Posición Y");
    gui.add(cameraPosition, 'z', -50, 50).name("Posición Z");
}

// Inicia la aplicación
main();
