import { Link } from 'react-router-dom';

export default function Header() {
    return (
        <nav className="navbar">
            <span className="navbar-brand">// SITE_AVAILABILITY_CHECKER</span>
            <div className="navbar-links">
                <Link to="/" style={{ fontWeight: 'bold' }}>[ Main Page ]</Link>
                <Link to="/api" style={{ fontWeight: 'bold' }}>[ API ]</Link>
            <Link to="/delete-account" style={{ fontWeight: 'bold' }}>[ Delete Account ]</Link>
            <Link to="/logout" style={{ fontWeight: 'bold' }}>[ Log out ]</Link>
            </div>
        </nav>
    )
}