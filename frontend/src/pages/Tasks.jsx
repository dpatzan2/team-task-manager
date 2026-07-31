import { useNavigate } from "react-router-dom";

import { clearToken } from "../api";

export default function Tasks() {
  const navigate = useNavigate();

  function handleLogout() {
    clearToken();
    navigate("/login");
  }

  return (
    <div className="card">
      <header className="row">
        <h1>My tasks</h1>
        <button onClick={handleLogout}>Log out</button>
      </header>
    </div>
  );
}
