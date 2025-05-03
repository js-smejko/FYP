import { Outlet } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import classes from '../modules/RootLayout.module.css';

/**
 * Lays out components that are common to all pages.
 * For now this is only the sidebar.
 * The outlet is where the page content will be rendered.
 * @returns {JSX.Element} The RootLayoutPage component.
 */
const RootLayoutPage = () => {
    return (
        <div className={classes.root}>
            <Sidebar />
            <div className={classes.outlet}>
                <Outlet />
            </div>
        </div>
    );
}

export default RootLayoutPage;