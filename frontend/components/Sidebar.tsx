import SidebarItem from "./SidebarItem";
import classes from '../modules/Sidebar.module.css';
import { SIDEBAR_ITEMS } from "../util/sidebarItems";

/**
 * Maps items in util/sidebarItems to React Router's NavLink components.
 * @returns {JSX.Element} The Sidebar component.
 */
const Sidebar = () => {
    return (
        <aside className={classes.sidebar}>
            <ul className={classes["nav-links"]}>
                {SIDEBAR_ITEMS.map(item => (
                    <SidebarItem 
                        key={item.text}
                        {...item} 
                        text={item.text}
                    />
                ))}
            </ul>
        </aside>
    );
}

export default Sidebar;