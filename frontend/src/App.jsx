import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { getToken } from "./api";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Tasks from "./pages/Tasks";

// ponytail: presence of a token is enough to route; a request with an expired
// token still fails server-side and the API layer reports it.
function Protected({ children }) {
  return getToken() ? children : <Navigate to="/login" replace />;
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
              <Tasks />
            </Protected>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
