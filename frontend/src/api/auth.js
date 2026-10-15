import api from "./client";

export async function loginUser(username, password) {
    const response = await api.post("/auth/token/", {
        username,
        password,
    });

    const access = response.data?.access;
    const refresh = response.data?.refresh;

    if (!access) {
        throw new Error("Login succeeded but the API did not return an access token.");
    }

    localStorage.setItem("accessToken", access);
    if (refresh) {
        localStorage.setItem("refreshToken", refresh);
    } else {
        localStorage.removeItem("refreshToken");
    }

    return access;
}

export function logoutUser() {
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
}

export function isAuthenticated() {
    return Boolean(localStorage.getItem("accessToken"));
}
