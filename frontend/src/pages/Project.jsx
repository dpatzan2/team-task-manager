import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";

export default function Project() {
  const { id } = useParams(); const [data, setData] = useState({ results: [] }); const [title, setTitle] = useState(""); const [error, setError] = useState("");
  const load = (url = `/tasks/?project=${id}`) => api(url).then(setData).catch((e) => setError(e.message)); useEffect(() => { load(); }, [id]);
  async function create(e) { e.preventDefault(); try { await api("/tasks/", { method: "POST", body: { project: id, title } }); setTitle(""); load(); } catch (e) { setError(e.message); } }
  return <div className="card"><h1>Project tasks</h1><form className="task-form" onSubmit={create}><label>New task<input value={title} onChange={(e) => setTitle(e.target.value)} required /></label><button>Add task</button></form>{error && <p className="error">{error}</p>}<ul className="task-list">{data.results.map((task) => <li key={task.id}><strong>{task.title}</strong><span className="badge">{task.status}</span><button className="secondary" onClick={() => api(`/tasks/${task.id}/`, { method: "PATCH", body: { status: task.status === "DONE" ? "TODO" : "DONE" } }).then(() => load()).catch((e) => setError(e.message))}>Toggle done</button><button className="secondary" onClick={() => api(`/tasks/${task.id}/`, { method: "DELETE" }).then(() => load()).catch((e) => setError(e.message))}>Delete</button></li>)}</ul><div className="row">{data.previous && <button onClick={() => load(data.previous.replace("/api", ""))}>Previous</button>}{data.next && <button onClick={() => load(data.next.replace("/api", ""))}>Next</button>}</div></div>;
}
