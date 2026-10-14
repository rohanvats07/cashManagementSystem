import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

function App() {
    const [apiStatus, setApiStatus] = useState("checking");

    useEffect(() => {
        let isMounted = true;

        axios
            .get(`${API_BASE_URL}/health/`)
            .then((response) => {
                if (isMounted) {
                    setApiStatus(
                        response.data.database === "connected"
                            ? "connected"
                            : "unavailable"
                    );
                }
            })
            .catch(() => {
                if (isMounted) {
                    setApiStatus("unavailable");
                }
            });

        return () => {
            isMounted = false;
        };
    }, []);

    return (
        <div className="app-shell">
            <aside className="sidebar">
                <div className="brand">
                    <div className="brand-mark">C</div>
                    <div>
                        <h1>CMRS</h1>
                        <p>Cash Management</p>
                    </div>
                </div>

                <p className="nav-heading">WORKSPACE</p>

                <nav className="navigation">
                    <a className="nav-item active" href="#overview">
                        <span>▦</span> Overview
                    </a>
                    <a className="nav-item" href="#collections">
                        <span>₹</span> Collections
                    </a>
                    <a className="nav-item" href="#reconciliation">
                        <span>⇄</span> Reconciliation
                    </a>
                    <a className="nav-item" href="#deposits">
                        <span>▤</span> Bank Deposits
                    </a>
                    <a className="nav-item" href="#digital-payments">
                        <span>◈</span> Digital Payments
                        <span className="nav-badge">Soon</span>
                    </a>
                </nav>

                <div className="sidebar-footer">
                    <span className="status-dot" />
                    Development environment
                </div>
            </aside>

            <main className="main-content" id="overview">
                <header className="topbar">
                    <div>
                        <p className="eyebrow">WORKSPACE / OVERVIEW</p>
                        <h2>Cash management</h2>
                    </div>

                    <div className="api-indicator">
                        <span
                            className={`status-dot ${
                                apiStatus === "connected" ? "" : "status-warning"
                            }`}
                        />
                        API:{" "}
                        {apiStatus === "connected"
                            ? "Connected"
                            : apiStatus === "checking"
                              ? "Checking..."
                              : "Unavailable"}
                    </div>
                </header>

                <section className="welcome-panel">
                    <div>
                        <p className="eyebrow light-eyebrow">
                            CASH MANAGEMENT & RECONCILIATION
                        </p>
                        <h1>Visibility at every step.</h1>
                        <p>
                            Track collections, reconcile branch cash, and
                            monitor bank settlements in one place.
                        </p>
                    </div>
                    <div className="welcome-symbol" aria-hidden="true">
                        ₹
                    </div>
                </section>

                <section className="section-heading">
                    <div>
                        <h3>Operational overview</h3>
                        <p>Live business metrics will appear here.</p>
                    </div>
                    <span className="demo-label">DEVELOPMENT PREVIEW</span>
                </section>

                <section className="metrics-grid">
                    {[
                        {
                            label: "Expected collections",
                            value: "—",
                            note: "Awaiting collection APIs",
                        },
                        {
                            label: "Cash collected",
                            value: "—",
                            note: "Awaiting collection APIs",
                        },
                        {
                            label: "Cash at branches",
                            value: "—",
                            note: "Awaiting reconciliation APIs",
                        },
                        {
                            label: "Settled amount",
                            value: "—",
                            note: "Awaiting settlement APIs",
                        },
                    ].map((metric) => (
                        <article className="metric-card" key={metric.label}>
                            <p>{metric.label}</p>
                            <h3>{metric.value}</h3>
                            <span>{metric.note}</span>
                        </article>
                    ))}
                </section>

                <section className="payment-panel" id="digital-payments">
                    <div className="payment-icon">◈</div>
                    <div className="payment-copy">
                        <div className="payment-title">
                            <h3>Digital payments</h3>
                            <span className="coming-soon">COMING SOON</span>
                        </div>

                        <p>
                            Digital and UPI repayment support is planned for a
                            future release. Once implemented, eligible
                            transactions will be incorporated into the same
                            reconciliation workflow.
                        </p>

                        <div className="planned-features">
                            <span>UPI payments</span>
                            <span>Transaction references</span>
                            <span>Settlement reconciliation</span>
                        </div>
                    </div>
                </section>

                <footer className="app-footer">
                    CMRS · Development preview · No real payments are processed
                </footer>
            </main>
        </div>
    );
}

export default App;