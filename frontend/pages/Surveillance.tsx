import VideoSyncPlayer from "../components/VideoSyncPlayer";

const SurveillancePage = () => {
    return (
        <>
            <h1>Surveillance</h1>
            <sub>Click on either view to fullscreen it or use the synchronised controls below</sub>
            <VideoSyncPlayer />
        </>
    );
};

export default SurveillancePage;