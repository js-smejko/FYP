import { Link } from "react-router-dom";
import Sidebar from "../components/Sidebar";

/**
 * Placeholder for a page that isn't ready yet. At release, this should represent a real error like page not found.
 * @returns {JSX.Element} The ErrorPage component.
 */
const ErrorPage = () => {
    return (
        <div style={{ display: "flex", flexDirection: "row" }}>
            <Sidebar />
            <div style={{ justifyContent: "center", alignItems: "center", display: "flex", flexDirection: "column", width: "80vw"  }}>
                <h1>This page isn't ready yet!</h1>
                <Link to="/">
                    Go back to the dashboard
                </Link>
            </div>
        </div>
    );
};

export default ErrorPage;