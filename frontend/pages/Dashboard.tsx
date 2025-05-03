import { useSelector } from "react-redux";
import HlsPlayer from "../components/HlsPlayer";
import Scatter3d from "../components/Scatter3d";
import classes from "../modules/Dashboard.module.css";
import { IScatter3dDataLive } from "../util/interfaces";
import { colours, scene } from "../util/view3dParams";
import { useNavigate } from "react-router-dom";
// Adjust to a better placeholder image
import placeholder from "../../public/favicon.ico";

const HomePage = () => {
    // Provide an example of the Scatter3d component
    const scatterData = useSelector<any, IScatter3dDataLive[]>((state) => state.socket.scatterData);
    // Calling navigate() will change the URL to the one provided, changing the page
    const navigate = useNavigate();

    return (
        <>
            <h1>Dashboard</h1>
            <sub>Click the widgets below for more details</sub>
            <div className={classes.dashboard}>
                <Scatter3d 
                    data={scatterData} 
                    traceColours={colours} 
                    scene={scene} 
                    className={classes.item} 
                    onPointClick={() => navigate("/three-dimensional-view")}
                />
                <HlsPlayer 
                    className={classes.item}
                    src="http://192.168.2.162:8080/wide/playlist.m3u8"
                    controls={false}
                    onClick={() => navigate("/surveillance")}
                    poster={placeholder}
                />
                <HlsPlayer 
                    className={classes.item}
                    src="http://192.168.2.162:8080/deep/playlist.m3u8"
                    controls={false}
                    onClick={() => navigate("/surveillance")}
                    poster={placeholder}
                />
            </div>
        </>
    )
};

export default HomePage;