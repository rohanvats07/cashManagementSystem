import axios from "axios";

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api",
    headers: {
        "Content-Type": "application/json",
    },
    timeout: 20000,
});

api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem("accessToken");
        if (token) {
            config.headers = config.headers || {};
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

api.interceptors.response.use(
    (response) => response,
    (error) => {
        const url = error.config?.url || "";
        const isLoginRequest = url.includes("/auth/token/");
        if (error.response?.status === 401 && !isLoginRequest) {
            localStorage.removeItem("accessToken");
            localStorage.removeItem("refreshToken");
            if (window.location.pathname !== "/login") {
                window.location.assign("/login");
            }
        }
        return Promise.reject(error);
    }
);

export function getApiError(error) {
    const data = error?.response?.data;

    if (typeof data?.detail === "string") {
        return data.detail;
    }

    if (typeof data?.message === "string") {
        return data.message;
    }

    if (data && typeof data === "object") {
        return Object.entries(data)
            .map(([field, value]) => {
                const message = Array.isArray(value)
                    ? value.map((item) => typeof item === "string" ? item : JSON.stringify(item)).join(", ")
                    : typeof value === "string"
                        ? value
                        : JSON.stringify(value);
                return `${field}: ${message}`;
            })
            .join(" | ");
    }

    if (error?.code === "ECONNABORTED") {
        return "The request timed out. Please try again.";
    }

    if (!error?.response) {
        return "Unable to reach the backend. Check that Django is running on port 8000.";
    }

    return error?.message || "Something went wrong. Please try again.";
}

export default api;
