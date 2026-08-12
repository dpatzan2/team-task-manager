import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";

export default function Organization() {
  const { id } = useParams(); const [org, setOrg] = useState(null); const [projects, setProjects] = useState([]); const [members, setMembers] = useState([]); const [name, setName] = useState(""); const [error, setError] = useState("");
  const load = () => Promise.all([api(`/organizations/${id}/`), api(`/projects/?organization=${id}`), api(`/memberships/?organization=${id}`)]).then(([o, p, m]) => { setOrg(o); setProjects(p.results); setMembers(m.results.filter((x) => String(x.organization) === id)); }).catch((e) => setError(e.message));
  useEffect(load, [id]);
  async function create(e) { e.preventDefault(); try { await api("/projects/", { method: "POST", body: { organization: id, name } }); setName(""); load(); } catch (e) { setError(e.message); } }
  return <div className="card"><h1>{org?.name ?? "Organization"}</h1>{error && <p className="error">{error}</p>}<h2>Projects</h2><form className="task-form" onSubmit={create}><label>New project<input value={name} onChange={(e) => setName(e.target.value)} required /></label><button>Create project</button></form><ul className="task-list">{projects.map((p) => <li key={p.id}><Link to={`/projects/${p.id}`}>{p.name}</Link></li>)}</ul><h2>Members</h2><ul>{members.map((m) => <li key={m.id}>{m.username} — {m.role}</li>)}</ul></div>;
}
