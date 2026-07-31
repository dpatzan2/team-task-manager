const TOKEN_KEY = "access";

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setToken = (token) => localStorage.setItem(TOKEN_KEY, token);
export const clearToken = () => localStorage.removeItem(TOKEN_KEY);

/** Turns a DRF error body into a single readable message. */
async function errorMessage(response) {
  const data = await response.json().catch(() => null);
  if (!data) return `Request failed (${response.status})`;
  if (data.detail) return data.detail;
  return Object.entries(data)
    .map(([field, messages]) => `${field}: ${[].concat(messages).join(" ")}`)
    .join("\n");
}

export async function api(path, { body, ...options } = {}) {
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

  if (!response.ok) throw new Error(await errorMessage(response));
  return response.status === 204 ? null : response.json();
}
