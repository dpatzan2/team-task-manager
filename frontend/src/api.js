const TOKEN_KEY = "access";
const REFRESH_KEY = "refresh";

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setToken = (token, refresh) => { localStorage.setItem(TOKEN_KEY, token); if (refresh) localStorage.setItem(REFRESH_KEY, refresh); };
export const clearToken = () => { localStorage.removeItem(TOKEN_KEY); localStorage.removeItem(REFRESH_KEY); };

/** Turns a DRF error body into a single readable message. */
async function errorMessage(response) {
  const data = await response.json().catch(() => null);
  if (!data) return `Request failed (${response.status})`;
  if (data.detail) return data.detail;
  return Object.entries(data)
    .map(([field, messages]) => `${field}: ${[].concat(messages).join(" ")}`)
    .join("\n");
}

export async function api(path, { body, retry = true, ...options } = {}) {
  const token = getToken();
  const response = await fetch(`/api${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
    ...(body && { body: JSON.stringify(body) }),
  });

  if (response.status === 401 && retry && localStorage.getItem(REFRESH_KEY) && path !== "/auth/refresh/") {
    const refresh = await fetch("/api/auth/refresh/", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ refresh: localStorage.getItem(REFRESH_KEY) }) });
    if (refresh.ok) { const tokens = await refresh.json(); setToken(tokens.access); return api(path, { body, retry: false, ...options }); }
    clearToken();
  }
  if (!response.ok) throw new Error(await errorMessage(response));
  return response.status === 204 ? null : response.json();
}
