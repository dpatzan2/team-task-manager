import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, clearToken } from "../api";

export default function Organizations() {
  const [items, setItems] = useState([]); const [name, setName] = useState(""); const [error, setError] = useState(""); const navigate = useNavigate();
  const load = () => api("/organizations/").then((data) => setItems(data.results)).catch((err) => setError(err.message));
  useEffect(() => { load(); }, []);
  async function create(e) { e.preventDefault(); try { const slug = name.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, ""); await api("/organizations/", { method: "POST", body: { name, slug } }); setName(""); load(); } catch (err) { setError(err.message); } }
  return <div className="card"><header className="row"><div><h1>My organizations</h1><p className="muted">Choose a workspace to manage its projects and team.</p></div><button className="secondary" onClick={() => { clearToken(); navigate("/login"); }}>Log out</button></header><form className="task-form" onSubmit={create}><label>Name<input value={name} onChange={(e) => setName(e.target.value)} required /></label><button>Create organization</button></form>{error && <p className="error">{error}</p>}{items.length === 0 ? <p className="muted empty-state">Create your first organization to get started.</p> : <ul className="resource-list">{items.map((item) => <li key={item.id}><Link to={`/organizations/${item.id}`}><span className="resource-icon">O</span><span><strong>{item.name}</strong><small>{item.slug}</small></span><span aria-hidden="true">→</span></Link></li>)}</ul>}</div>;
}
