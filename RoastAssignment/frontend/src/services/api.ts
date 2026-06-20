import axios from 'axios';

/** snake_case -> camelCase for a single object key, e.g. `full_name` -> `fullName`. */
function toCamelKey(key: string): string {
  return key.replace(/_([a-z0-9])/g, (_match, char: string) => char.toUpperCase());
}

/**
 * Recursively converts every snake_case object key in a JSON response to
 * camelCase, so the FastAPI backend (snake_case Pydantic schemas) lines up
 * with the frontend's camelCase `types/index.ts` interfaces without every
 * hook needing its own wire-shape mapping.
 */
function camelCaseKeysDeep(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map((item) => camelCaseKeysDeep(item));
  }
  if (value !== null && typeof value === 'object' && value.constructor === Object) {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>).map(([key, val]) => [
        toCamelKey(key),
        camelCaseKeysDeep(val),
      ])
    );
  }
  return value;
}

const defaultResponseTransforms = Array.isArray(axios.defaults.transformResponse)
  ? axios.defaults.transformResponse
  : axios.defaults.transformResponse
    ? [axios.defaults.transformResponse]
    : [];

const api = axios.create({
  baseURL: `${import.meta.env.VITE_API_URL}/api/v1`,
  transformResponse: [...defaultResponseTransforms, camelCaseKeysDeep],
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true;
      const refresh = localStorage.getItem('refresh_token');
      const { data } = await axios.post(`${import.meta.env.VITE_API_URL}/api/v1/auth/refresh`, {
        refresh_token: refresh,
      });
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      return api(error.config);
    }
    return Promise.reject(error);
  }
);

export default api;
