import { Navigate, useLocation } from "react-router-dom";
import { isAuthenticated } from "../api/auth";

export default function ProtectedRoute({ children }) {
    const location = useLocation();

    if (!isAuthenticated()) {
        const from = `${location.pathname}${location.search}${location.hash}`;
        return <Navigate to="/login" replace state={{ from }} />;
    }

    return children;
}
