import { NavLink, NavLinkRenderProps } from "react-router-dom";

import { ISidebarItem } from "../util/interfaces";
import classes from '../modules/Sidebar.module.css';

/**
 * To be used with the Sidebar component.
 * @param path - The path to the page.
 * @param img - The image to display.
 * @param text - The text to display.
 * @returns {JSX.Element} The SidebarItem component.
 */
const SidebarItem = ({ path, img, text }: ISidebarItem) => {
    return (
        <li>
            <NavLink 
                to={path} 
                // Style the active link differently
                className={(o: NavLinkRenderProps) => o.isActive ? classes.active : ""}
            >
                <img src={img} draggable={false} />
                <strong>{text}</strong>
            </NavLink>
        </li>
    );
}

export default SidebarItem;