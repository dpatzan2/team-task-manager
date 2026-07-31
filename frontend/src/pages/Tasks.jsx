import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api, clearToken } from "../api";
import TaskForm from "../components/TaskForm";

const PRIORITY_LABEL = { LOW: "Low", MEDIUM: "Medium", HIGH: "High" };

export default function Tasks() {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState([]);
  const [filters, setFilters] = useState({ completed: "", priority: "" });
  const [editing, setEditing] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const query = new URLSearchParams(
        Object.entries(filters).filter(([, value]) => value)
      );
      setTasks(await api(`/tasks/?${query}`));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    load();
  }, [load]);

  // ponytail: every mutation refetches the list instead of patching local
  // state. One extra request, zero chances of the UI drifting from the server.
  async function save(data) {
    await api(editing ? `/tasks/${editing.id}/` : "/tasks/", {
      method: editing ? "PATCH" : "POST",
      body: data,
    });
    setEditing(null);
    load();
  }

  async function run(request) {
    setError("");
    try {
      await request;
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  function logout() {
    clearToken();
    navigate("/login");
  }

  return (
    <div className="card">
      <header className="row">
        <h1>My tasks</h1>
        <button className="secondary" onClick={logout}>
          Log out
        </button>
      </header>

      <TaskForm
        key={editing?.id ?? "new"}
        task={editing}
        onSubmit={save}
        onCancel={editing ? () => setEditing(null) : undefined}
      />

      <div className="row">
        <label>
          Status
          <select
            value={filters.completed}
            onChange={(e) =>
              setFilters({ ...filters, completed: e.target.value })
            }
          >
            <option value="">All</option>
            <option value="false">Pending</option>
            <option value="true">Completed</option>
          </select>
        </label>

        <label>
          Priority
          <select
            value={filters.priority}
            onChange={(e) =>
              setFilters({ ...filters, priority: e.target.value })
            }
          >
            <option value="">All</option>
            <option value="LOW">Low</option>
            <option value="MEDIUM">Medium</option>
            <option value="HIGH">High</option>
          </select>
        </label>
      </div>

      {error && <p className="error">{error}</p>}

      {loading ? (
        <p className="muted">Loading tasks...</p>
      ) : tasks.length === 0 ? (
        <p className="muted">No tasks to show.</p>
      ) : (
        <ul className="task-list">
          {tasks.map((task) => (
            <li key={task.id} className={task.completed ? "done" : undefined}>
              <input
                type="checkbox"
                checked={task.completed}
                onChange={() =>
                  run(api(`/tasks/${task.id}/toggle/`, { method: "POST" }))
                }
                aria-label={`Mark "${task.title}" as ${
                  task.completed ? "pending" : "completed"
                }`}
              />

              <div className="task-body">
                <strong>{task.title}</strong>
                {task.description && <p className="muted">{task.description}</p>}
              </div>

              <span className={`badge ${task.priority.toLowerCase()}`}>
                {PRIORITY_LABEL[task.priority]}
              </span>

              <button className="secondary" onClick={() => setEditing(task)}>
                Edit
              </button>
              <button
                className="secondary"
                onClick={() =>
                  run(api(`/tasks/${task.id}/`, { method: "DELETE" }))
                }
              >
                Delete
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
