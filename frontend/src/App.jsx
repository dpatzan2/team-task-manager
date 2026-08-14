import { useEffect, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { api } from "./api";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Organizations from "./pages/Organizations";
import Organization from "./pages/Organization";
import Project from "./pages/Project";

function Protected({ children }) {
  const [authenticated, setAuthenticated] = useState(null);
  useEffect(() => { api("/auth/session/").then(() => setAuthenticated(true)).catch(() => setAuthenticated(false)); }, []);
  if (authenticated === null) return null;
  return authenticated ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/"
          element={
            <Protected>
              <Organizations />
            </Protected>
          }
        />
        <Route path="/organizations/:id" element={<Protected><Organization /></Protected>} />
        <Route path="/projects/:id" element={<Protected><Project /></Protected>} />
      </Routes>
    </BrowserRouter>
  );
}
