import { Color, Scene } from "plotly.js";

export interface ISidebarItem {
    img?: string;
    text: string;
    path: string;
    children?: ISidebarItem[];
}

export interface IHlsPlayer extends React.VideoHTMLAttributes<HTMLVideoElement> {
    src: string;
}

export interface IScatter3dOld extends React.HTMLAttributes<HTMLDivElement> {
    pause?: boolean;
}

export interface IScatter3d extends React.HTMLAttributes<HTMLDivElement> {
    data: IScatter3dDataLive[];
    traceColours: Color[];
    scene: Partial<Scene>;
    interactive?: boolean;
    pause?: boolean;
    onPointClick?: (id: number) => void
}

export interface IScatter3dData {
    id: number;
    coordinates: {
        x: number,
        y: number,
        z: number
    };
}

export interface IScatter3dDataLive extends IScatter3dData {
    track: boolean;
}