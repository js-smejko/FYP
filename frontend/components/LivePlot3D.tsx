import { useSelector } from "react-redux";
import { useEffect, useState } from "react";
import { IScatter3dData, IScatter3dDataLive } from "../util/interfaces";

import Scatter3d from "./Scatter3d";
import { colours, scene } from "../util/view3dParams";

/**
 * Implements the Scatter3d component to display live data from the WebSocket.
 * @returns {JSX.Element} The LivePlot3D component.
 */
const LivePlot3d = () => {
    // Get the scatter data from the Redux store
    const scatterData = useSelector<any, IScatter3dData[]>((state) => state.socket.scatterData);
    const [trackScatterData, setTrackScatterData] = useState<IScatter3dDataLive[]>([]);
    // Pausing the flow of new data frees the view to be adjusted
    const [pause, setPause] = useState(false);

    // Combine the new coordinate data with the existing track/no track selections
    useEffect(() => {
        if (scatterData) {
            setTrackScatterData(prev =>
                scatterData.map(next => ({
                    ...next,
                    track: prev.find(o => o.id === next.id)?.track
                })) as IScatter3dDataLive[]
            );
        }
    }, [scatterData]);

    // Toggle track to true/false when the ID is clicked
    const handleIdClick = (id: number) => {
        setTrackScatterData((prev) => {
            const newData = prev.map((item) => {
                if (item.id === id) {
                    return { ...item, track: !item.track };
                }
                return item;
            });
            return newData;
        });
    };

    return (
        <div style={{ display: "flex", height: "85%" }} >
            <Scatter3d data={trackScatterData} traceColours={colours} scene={scene} pause={pause} style={{ flex: 9 }} onPointClick={handleIdClick} interactive />
            <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
                <div>
                    <p>Press on an ID to toggle its tracks</p>
                    <ul style={{ listStyleType: "none", paddingInlineStart: "0px" }}>
                        {trackScatterData.length ? (
                            trackScatterData.map(({ id, track }) => (
                                <li key={id} style={{ paddingBlock: "0.25em" }}>
                                    <button
                                        // className="fill"
                                        onClick={() => handleIdClick(id)}
                                        style={track ? { backgroundColor: colours[id % 3] } : undefined}
                                    >
                                        Fish {id}
                                    </button>
                                </li>
                            ))
                        ) : (
                            <strong>No data yet</strong>
                        )}
                    </ul>
                </div>
                <div>
                    <p>Pause to enable freely adjusting the view</p>
                    <button
                        onClick={() => setPause(prev => !prev)}
                    >
                        {pause ? "Resume" : "Pause"}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default LivePlot3d;