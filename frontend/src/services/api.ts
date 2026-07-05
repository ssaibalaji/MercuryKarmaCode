import axios, {
  type AxiosError,
  type InternalAxiosRequestConfig,
} from 'axios';

interface RetryableRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

const api = axios.create({
  baseURL: `${import.meta.env.VITE_API_URL}/api/v1`,
  // Tokens live in httpOnly cookies set by the backend - the browser attaches
  // them automatically on same-site/CORS requests as long as credentials are
  // included, so there is nothing for this client to read/store manually.
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

let isRefreshing = false;
let refreshWaiters: Array<(ok: boolean) => void> = [];

function subscribeTokenRefresh(callback: (ok: boolean) => void): void {
  refreshWaiters.push(callback);
}

function notifyRefreshSubscribers(ok: boolean): void {
  refreshWaiters.forEach((callback) => callback(ok));
  refreshWaiters = [];
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetryableRequestConfig | undefined;

    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/auth/refresh')
    ) {
      originalRequest._retry = true;

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          subscribeTokenRefresh((ok) => {
            if (!ok) {
              reject(error);
              return;
            }
            resolve(api(originalRequest));
          });
        });
      }

      isRefreshing = true;

      try {
        // No body needed - the refresh token is sent automatically via cookie,
        // and the new access/refresh cookies are set by the response.
        await axios.post(
          `${import.meta.env.VITE_API_URL}/api/v1/auth/refresh`,
          undefined,
          { withCredentials: true },
        );
        notifyRefreshSubscribers(true);
        return api(originalRequest);
      } catch (refreshError) {
        notifyRefreshSubscribers(false);
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  },
);

export default api;
