import { Scene } from "plotly.js"

    export const colours = ['red', 'blue', 'green']

    export const scene: Partial<Scene> = {
        xaxis: { range: [0, 220], autorange: false },
        yaxis: { range: [0, 280], autorange: false },
        zaxis: { range: [0, 170], autorange: false },
        aspectmode: 'manual',
        aspectratio: {
            x: 22,
            y: 27.5,
            z: 16.5
        },
        camera: {
            eye: { x: 35, y: 35, z: 35 }
        }
    }