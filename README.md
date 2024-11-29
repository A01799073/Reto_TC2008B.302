Here's the updated README.md:

# Simulador de Movilidad Urbana - TC2008B.302

## 📚 Índice

1. [Demo del Proyecto](#-demo-del-proyecto)
2. [Diagramas](#-diagramas)
3. [Reporte Completo](#-reporte-completo)
4. [Descripción del Proyecto](#-descripción-del-proyecto)
5. [Equipo](#-equipo-del-proyecto)
6. [Funcionalidades](#-funcionalidades)
7. [Tecnologías](#️-tecnologías-y-herramientas)
8. [Instalación](#-instalación-y-uso)
9. [Métricas](#-métricas-y-análisis)

## 🎥 Demo del Proyecto

![Demostración del Proyecto](Demostration.gif)

## 📄 Reporte Completo

El reporte detallado del proyecto se puede encontrar en [Informe Final](Evidencias/Evidencia%201.%20Reporte%20del%20reto.pdf)

## 📊 Diagramas

### Diagrama de Clases

```mermaid

classDiagram
    class Model {
        -grid
        -schedule
        -running
        -num_agents
        -width
        -height
        +__init__(N)
        +step()
        +add_new_car()
        +reached_destination
    }

    class Car {
        -state: String
        -speed: Int
        -destination: Destination
        -path: List
        -last_position
        -stuck_counter: Int
        +__init__(unique_id, model)
        +move()
        +step()
        +find_path()
        -_handle_destination_arrival()
        -_handle_blocked_movement()
        -_handle_traffic_light_movement()
        -_handle_road_movement()
    }

    class TrafficLight {
        -state: Boolean
        -timeToChange: Int
        -pair_id: Int
        -orientation: String
        +__init__(unique_id, model, state, timeToChange, pair_id)
        +step()
        +coordinate_light_change()
        +get_neighboring_pairs()
        -is_pair_controller()
    }

    class Road {
        -direction: String
        +__init__(unique_id, model, direction)
    }

    class Agent {
        <<Mesa>>
        +unique_id
        +model
    }

    Agent <|-- Car
    Agent <|-- TrafficLight
    Agent <|-- Road
    Model *-- Car
    Model *-- TrafficLight
    Model *-- Road

```

### Diagrama de Interacción

```mermaid
sequenceDiagram
    participant Model
    participant Car
    participant TrafficLight
    participant Road

    Model->>Car: create(unique_id, model)
    Model->>TrafficLight: create(unique_id, model, state, timeToChange, pair_id)
    Model->>Road: create(unique_id, model, direction)
    
    loop Every Step
        Model->>Model: step()
        Model->>Car: step()
        Car->>Car: move()
        Car->>Road: check_direction()
        Car->>TrafficLight: check_state()
        
        alt Car at Traffic Light
            Car->>Car: _handle_traffic_light_movement()
        else Car on Road
            Car->>Car: _handle_road_movement()
        end

        alt Car Reached Destination
            Car->>Model: update reached_destination
            Model->>Model: add_new_car()
        end

        Model->>TrafficLight: step()
        TrafficLight->>TrafficLight: coordinate_light_change()
        TrafficLight->>TrafficLight: get_neighboring_pairs()
    end
```

## 📄 Reporte Completo

El reporte detallado del proyecto se puede encontrar en [Informe Final](Evidencias/Evidencia%201.%20Reporte%20del%20reto.pdf)

## 📋 Descripción del Proyecto

Sistema de simulación multiagente enfocado en resolver problemas de movilidad urbana en México. El proyecto implementa estrategias para reducir la congestión vehicular mediante:

- Optimización de rutas
- Control inteligente de semáforos
- Análisis de patrones de tráfico
- Visualización en tiempo real

## 👥 Equipo del Proyecto

### Profesores Titulares

- Octavio Navarro Hinojosa
- Gilberto Echeverría Furió

### Estudiantes Desarrolladores

- Emilio Ramírez Mascarúa - A01783980
- Kenia Esmeralda Ramos Javier - A01799073

## 🛠️ Instalación y Uso

### Requisitos Previos

- Python 3.x
- Node.js
- npm

### Backend (Servidor de Agentes)

1. Instalar dependencias de Python:

```bash
pip install mesa==2.1.1
pip install flask-cors
pip install flask
```

2. Ejecutar el servidor:

```bash
python -m src.visualization.trafficServer
```

### Frontend (Visualización)

1. Navegar al directorio de visualización:

```bash
cd AgentsVisualization/visualization
```

2. Instalar dependencias:

```bash
npm i
```

3. Iniciar el servidor de desarrollo:

```bash
npx vite
```

4. Abrir el navegador en la URL proporcionada o presionar 'o'

## 🚀 Funcionalidades

### 1. Sistema Base

- Grid 2D del ambiente urbano
- Agentes vehiculares básicos
- Sistema de visualización 3D con WebGL
- Métricas fundamentales

### 2. Sistema de Tráfico

- Red de calles y direcciones
- Control de semáforos con iluminación dinámica
- Gestión de velocidades
- Análisis de densidad

### 3. Sistema de Interacción

- Detección de colisiones
- Comportamiento vehicular realista
- Gestión de intersecciones
- Métricas de congestión

### 4. Sistema de Navegación

- Algoritmos de pathfinding A*
- Optimización de rutas
- Análisis de tiempos
- Visualización de trayectorias

## 📊 Métricas y Análisis

- Densidad de tráfico en tiempo real
- Tiempos de viaje por vehículo
- Niveles de congestión en intersecciones
- Eficiencia de rutas y llegadas exitosas
- Comportamiento de semáforos

## 📝 Licencia

MIT License

Este README proporcigna una visión completa del proyecto, incluyendo la demostración visual, documentación técnica y guías de instalación. Los diagramas y el reporte completo ayudan a entender la arquitectura y funcionamiento del sistema.
