export const clearToken = () => fetch("/api/auth/logout/", { method: "POST", credentials: "same-origin" });
export const localApiPath = (url) => {
  const { pathname, search } = new URL(url, "http://local");
  return `${pathname.replace(/^\/api/, "")}${search}`;
};

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
  const response = await fetch(`/api${path}`, {
    ...options,
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...(body && { body: JSON.stringify(body) }),
  });

  if (response.status === 401 && retry && path !== "/auth/refresh/") {
    const refresh = await fetch("/api/auth/refresh/", { method: "POST", credentials: "same-origin" });
    if (refresh.ok) return api(path, { body, retry: false, ...options });
    clearToken();
  }
  if (!response.ok) throw new Error(await errorMessage(response));
  return response.status === 204 ? null : response.json();
}
