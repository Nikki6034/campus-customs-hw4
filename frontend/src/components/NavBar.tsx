import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/context";
import { useCart } from "../cart/context";

const links = [
  { to: "/", label: "Home", end: true },
  { to: "/products", label: "Products" },
  { to: "/about", label: "About Us" },
];

export default function NavBar() {
  const { user, logout } = useAuth();
  const { count, open } = useCart();
  const navigate = useNavigate();

  function onLogout() {
    logout();
    navigate("/");
  }

  return (
    <header className="nav">
      <div className="nav-inner">
        <NavLink to="/" className="brand">
          Campus<span>Customs</span>
        </NavLink>

        <nav className="nav-links">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
            >
              {link.label}
            </NavLink>
          ))}
        </nav>

        <div className="nav-actions">
          {user ? (
            <>
              <span className="nav-greeting">
                Hi, {user.first_name ?? user.email}
              </span>
              <button type="button" className="btn btn-ghost" onClick={onLogout}>
                Log Out
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login" className="btn btn-ghost">
                Log In
              </NavLink>
              <NavLink to="/create-account" className="btn btn-solid">
                Create Account
              </NavLink>
            </>
          )}
          <button type="button" className="bag-btn" onClick={open} aria-label="Open bag">
            Bag{count > 0 && <span className="bag-count">{count}</span>}
          </button>
        </div>
      </div>
    </header>
  );
}
