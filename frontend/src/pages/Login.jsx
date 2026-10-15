import { useState } from "react";
import { ArrowRight, Eye, EyeOff, ShieldCheck, Wallet } from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { loginUser } from "../api/auth";
import { getApiError } from "../api/client";
import "./Login.css";

export default function Login() {
    const navigate = useNavigate();
    const location = useLocation();
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    async function handleSubmit(event) {
        event.preventDefault();
        if (loading) return;
        setError("");
        setLoading(true);
        try {
            await loginUser(username.trim(), password);
            const destination = location.state?.from || "/cash-management";
            navigate(destination, { replace: true });
        } catch (err) {
            setError(getApiError(err));
        } finally {
            setLoading(false);
        }
    }

    return (
        <main className="login-screen">
            <section className="login-brand-panel">
                <Link to="/" className="login-brand">
                    <span className="login-brand-mark">C<span>.</span></span>
                    <span><strong>CMRS</strong><small>Cash operations platform</small></span>
                </Link>
                <div className="login-brand-message">
                    <span className="login-overline">CASH MANAGEMENT &amp; RECONCILIATION</span>
                    <h1>Every rupee.<br />Every step.<br /><em>Accounted for.</em></h1>
                    <p>One workspace to follow cash collections, branch handovers, bank deposits, and settlement reconciliation.</p>
                    <div className="login-trust-list">
                        <div><ShieldCheck size={17} /><span>Role-based access control</span></div>
                        <div><ArrowRight size={17} /><span>End-to-end cash visibility</span></div>
                    </div>
                </div>
                <div className="login-brand-footer">BUILT FOR ACCOUNTABLE CASH OPERATIONS</div>
                <div className="login-decoration login-decoration-one" />
                <div className="login-decoration login-decoration-two" />
            </section>

            <section className="login-form-panel">
                <div className="login-form-wrap">
                    <div className="login-mobile-brand">
                        <span className="login-brand-mark">C<span>.</span></span>
                        <span><strong>CMRS</strong><small>Cash operations</small></span>
                    </div>
                    <div className="login-form-heading">
                        <div className="login-heading-icon"><Wallet size={20} /></div>
                        <span className="login-overline">SECURE WORKSPACE</span>
                        <h2>Welcome back</h2>
                        <p>Sign in with your assigned CMRS account to continue.</p>
                    </div>

                    {error && <div className="login-alert" role="alert"><strong>Unable to sign in</strong><span>{error}</span></div>}

                    <form className="login-form" onSubmit={handleSubmit}>
                        <label htmlFor="username">Username</label>
                        <input
                            id="username"
                            name="username"
                            type="text"
                            autoComplete="username"
                            placeholder="Enter your username"
                            value={username}
                            onChange={(event) => setUsername(event.target.value)}
                            disabled={loading}
                            required
                            autoFocus
                        />

                        <div className="login-password-label">
                            <label htmlFor="password">Password</label>
                        </div>
                        <div className="password-input-wrap">
                            <input
                                id="password"
                                name="password"
                                type={showPassword ? "text" : "password"}
                                autoComplete="current-password"
                                placeholder="Enter your password"
                                value={password}
                                onChange={(event) => setPassword(event.target.value)}
                                disabled={loading}
                                required
                            />
                            <button type="button" className="password-toggle" aria-label={showPassword ? "Hide password" : "Show password"} onClick={() => setShowPassword((value) => !value)}>
                                {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
                            </button>
                        </div>

                        <button className="login-submit" type="submit" disabled={loading}>
                            <span>{loading ? "Signing in..." : "Sign in to CMRS"}</span>
                            {!loading && <ArrowRight size={17} />}
                            {loading && <span className="login-spinner" />}
                        </button>
                    </form>

                    <div className="login-security-note"><ShieldCheck size={16} /><span>Your session is authenticated by the CMRS backend.</span></div>
                    <div className="login-bottom-links"><Link to="/">Back to overview</Link><span>Digital payments · Coming soon</span></div>
                </div>
            </section>
        </main>
    );
}
