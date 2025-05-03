import LivePlot3d from "../components/LivePlot3D";

const View3DPage = () => {
    return (
        <>
            <h1>3D View</h1>
            <sub>This is the real-time 3D projection of the fish. Click on an ID to toggle historical tracks. Press pause before adjusting the view for the best experience.</sub>
            <LivePlot3d />
        </>
    );
};

export default View3DPage;