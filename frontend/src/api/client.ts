import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 12000,
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("bbp_admin_token");
      if (!window.location.pathname.endsWith("/login")) {
        window.location.href = `${import.meta.env.VITE_BASE_PATH ?? "/"}login`;
      }
    }
    return Promise.reject(error);
  },
);

export function setAuthToken(token: string | null) {
  if (!token) {
    delete apiClient.defaults.headers.common.Authorization;
    return;
  }
  apiClient.defaults.headers.common.Authorization = `Bearer ${token}`;
}
