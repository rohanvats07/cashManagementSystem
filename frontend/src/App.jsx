import { useEffect, useState } from "react";
import { NavLink, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import {
    Activity, ArrowDownLeft, ArrowLeftRight, ArrowUpRight, Banknote,
    Bell, ChevronDown, CircleHelp, ClipboardCheck, CreditCard, LayoutDashboard,
    LogOut, Menu, ShieldCheck, Wallet, X
} from "lucide-react";

import "./App.css";
import Login from "./pages/Login";
import CashManagement from "./pages/CashManagement";
import ProtectedRoute from "./components/ProtectedRoute";
import { isAuthenticated, logoutUser } from "./api/auth";
import { getHealth } from "./api/cmrsApi";

function Dashboard() {
    const [health, setHealth] = useState("checking");

    useEffect(() => {
        let active = true;
        getHealth()
            .then(() => active && setHealth("online"))
            .catch(() => active && setHealth("offline"));
        return () => { active = false; };
    }, []);

    const quickLinks = [
        { icon: Wallet, title: "Cash collections", description: "Record customer repayments and generate receipts.", href: "/cash-management#collections", tone: "blue" },
        { icon: ClipboardCheck, title: "Branch reconciliation", description: "Review submissions and track cash differences.", href: "/cash-management#reconciliation", tone: "green" },
        { icon: Banknote, title: "Bank deposits", description: "Track deposits, references, and account credits.", href: "/cash-management#deposits", tone: "violet" },
    ];

    return (
        <div className="page-content">
            <section className="hero-panel">
                <div className="hero-copy">
                    <span className="eyebrow eyebrow-light">OPERATIONS OVERVIEW</span>
                    <h1>Cash operations,<br />under control.</h1>
                    <p>Follow every repayment from customer collection to branch handover, bank deposit, and company-account reconciliation.</p>
                    <NavLink className="button button-light" to="/cash-management#collections">
                        Open cash management <ArrowUpRight size={16} />
                    </NavLink>
                </div>
                <div className="hero-art" aria-hidden="true">
                    <div className="hero-orbit orbit-one" />
                    <div className="hero-orbit orbit-two" />
                    <div className="hero-money-card">
                        <div className="money-card-top"><span>CMRS WALLET</span><Wallet size={18} /></div>
                        <div className="money-symbol">₹</div>
                        <div className="money-card-bottom"><span>Cash lifecycle</span><span className="money-dot" /></div>
                    </div>
                    <div className="floating-chip chip-top"><ArrowDownLeft size={15} /> Cash collected</div>
                    <div className="floating-chip chip-bottom"><ShieldCheck size={15} /> Reconciliation ready</div>
                </div>
            </section>

            <div className="page-heading">
                <div>
                    <span className="eyebrow">YOUR WORKSPACE</span>
                    <h2>Quick access</h2>
                    <p>Choose an operational area to continue.</p>
                </div>
                <div className={`system-status ${health}`}>
                    <span className="status-dot" />
                    {health === "checking" ? "Checking API" : health === "online" ? "API connected" : "API unavailable"}
                </div>
            </div>

            <section className="quick-link-grid">
                {quickLinks.map((item) => {
                    const Icon = item.icon;
                    return (
                        <NavLink className="quick-link-card" to={item.href} key={item.title}>
                            <div className={`quick-icon ${item.tone}`}><Icon size={21} /></div>
                            <div className="quick-link-text">
                                <h3>{item.title}</h3>
                                <p>{item.description}</p>
                                <span className="text-link">Open workspace <ArrowUpRight size={14} /></span>
                            </div>
                        </NavLink>
                    );
                })}
            </section>

            <section className="lifecycle-panel">
                <div className="lifecycle-heading">
                    <div>
                        <span className="eyebrow">END-TO-END VISIBILITY</span>
                        <h2>Cash lifecycle</h2>
                    </div>
                    <span className="lifecycle-tag"><Activity size={14} /> Process overview</span>
                </div>
                <div className="lifecycle-steps">
                    {[
                        { icon: Wallet, title: "Collected", detail: "Agent records payment" },
                        { icon: ClipboardCheck, title: "Branch received", detail: "Submission reviewed" },
                        { icon: Banknote, title: "Bank deposited", detail: "Deposit recorded" },
                        { icon: ShieldCheck, title: "Reconciled", detail: "Company credit matched" },
                    ].map((step, index) => {
                        const Icon = step.icon;
                        return (
                            <div className="lifecycle-step" key={step.title}>
                                <div className="lifecycle-icon"><Icon size={18} /></div>
                                <div><strong>{step.title}</strong><span>{step.detail}</span></div>
                                {index < 3 && <div className="lifecycle-connector" />}
                            </div>
                        );
                    })}
                </div>
            </section>

            <section className="coming-soon-panel" id="digital-payments">
                <div className="coming-soon-icon"><CreditCard size={22} /></div>
                <div className="coming-soon-copy">
                    <div className="coming-soon-title"><h2>Digital payments</h2><span className="pill pill-warning">Coming soon</span></div>
                    <p>Digital payment processing is not enabled in this release. Cash operations and reconciliation remain available.</p>
                </div>
                <span className="coming-soon-decoration">CMRS / NEXT</span>
            </section>

            <footer className="app-footer">
                <span>CMRS · Cash Management &amp; Reconciliation System</span>
                <span>Secure operations workspace</span>
            </footer>
        </div>
    );
}

function AppShell() {
    const location = useLocation();
    const navigate = useNavigate();
    const [mobileNavOpen, setMobileNavOpen] = useState(false);
    const [signingOut, setSigningOut] = useState(false);
    const authenticated = isAuthenticated();
    const isLogin = location.pathname === "/login";
    const isDashboard = location.pathname === "/";
    const activeLabel = location.hash === "#reconciliation" ? "Reconciliation"
        : location.hash === "#deposits" ? "Bank deposits"
        : location.hash === "#collections" ? "Collections"
        : isDashboard ? "Overview" : "Cash management";

    useEffect(() => {
        setMobileNavOpen(false);
    }, [location.pathname, location.hash]);

    useEffect(() => {
        if (location.pathname !== "/cash-management" || !location.hash) return;
        const id = decodeURIComponent(location.hash.slice(1));
        const frame = window.requestAnimationFrame(() => {
            document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
        });
        return () => window.cancelAnimationFrame(frame);
    }, [location.pathname, location.hash]);

    async function handleLogout() {
        setSigningOut(true);
        try {
            logoutUser();
        } finally {
            setSigningOut(false);
            navigate("/login", { replace: true });
        }
    }

    if (isLogin) {
        return <Routes><Route path="/login" element={<Login />} /><Route path="*" element={<Login />} /></Routes>;
    }

    return (
        <div className="app-shell">
            {mobileNavOpen && <button className="mobile-overlay" aria-label="Close navigation" onClick={() => setMobileNavOpen(false)} />}
            <aside className={`sidebar ${mobileNavOpen ? "sidebar-open" : ""}`}>
                <NavLink to="/" className="brand-lockup">
                    <div className="brand-mark">C<span>.</span></div>
                    <div><strong>CMRS</strong><small>Cash operations</small></div>
                    <button className="mobile-close" aria-label="Close navigation" onClick={(event) => { event.preventDefault(); setMobileNavOpen(false); }}><X size={19} /></button>
                </NavLink>

                <div className="workspace-switcher">
                    <div className="workspace-avatar"><ShieldCheck size={17} /></div>
                    <div className="workspace-label"><strong>Operations</strong><span>Management workspace</span></div>
                    <ChevronDown size={15} className="workspace-chevron" />
                </div>

                <div className="nav-section-label">WORKSPACE</div>
                <nav className="primary-nav" aria-label="Main navigation">
                    <NavLink to="/" end className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
                        <LayoutDashboard size={18} /><span>Overview</span>
                    </NavLink>
                    <NavLink to="/cash-management#collections" className={() => `nav-link ${location.pathname === "/cash-management" && (!location.hash || location.hash === "#collections") ? "active" : ""}`}>
                        <Wallet size={18} /><span>Collections</span>
                    </NavLink>
                    <NavLink to="/cash-management#reconciliation" className={() => `nav-link ${location.pathname === "/cash-management" && location.hash === "#reconciliation" ? "active" : ""}`}>
                        <ArrowLeftRight size={18} /><span>Reconciliation</span>
                    </NavLink>
                    <NavLink to="/cash-management#deposits" className={() => `nav-link ${location.pathname === "/cash-management" && location.hash === "#deposits" ? "active" : ""}`}>
                        <Banknote size={18} /><span>Bank deposits</span>
                    </NavLink>
                </nav>

                <div className="nav-section-label nav-section-spaced">PLATFORM</div>
                <a className="nav-link nav-link-disabled" href="/#digital-payments" onClick={(event) => { event.preventDefault(); navigate("/#digital-payments"); }}>
                    <CreditCard size={18} /><span>Digital payments</span><span className="nav-soon">SOON</span>
                </a>

                <div className="sidebar-bottom">
                    <div className="help-card">
                        <div className="help-icon"><CircleHelp size={17} /></div>
                        <div><strong>Need help?</strong><span>Contact your system administrator.</span></div>
                    </div>
                    {authenticated ? (
                        <button className="nav-link signout-link" onClick={handleLogout} disabled={signingOut}>
                            <LogOut size={18} /><span>{signingOut ? "Signing out..." : "Sign out"}</span>
                        </button>
                    ) : (
                        <NavLink className="nav-link" to="/login"><LogOut size={18} /><span>Sign in</span></NavLink>
                    )}
                    <div className="sidebar-user">
                        <div className="user-avatar">CM</div>
                        <div className="user-meta"><strong>CMRS Workspace</strong><span>{authenticated ? "Authenticated session" : "Guest access"}</span></div>
                        <Bell size={16} className="user-bell" />
                    </div>
                </div>
            </aside>

            <div className="app-main">
                <header className="topbar">
                    <div className="topbar-left">
                        <button className="mobile-menu" aria-label="Open navigation" onClick={() => setMobileNavOpen(true)}><Menu size={21} /></button>
                        <div className="breadcrumbs"><span>Workspace</span><span className="breadcrumb-slash">/</span><strong>{activeLabel}</strong></div>
                    </div>
                    <div className="topbar-right">
                        <span className="environment-chip"><span /> Local environment</span>
                        {authenticated ? (
                            <button className="topbar-signout" onClick={handleLogout}><LogOut size={15} /> Sign out</button>
                        ) : (
                            <NavLink className="topbar-signout" to="/login"><LogOut size={15} /> Sign in</NavLink>
                        )}
                    </div>
                </header>

                <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/login" element={<Login />} />
                    <Route path="/cash-management" element={<ProtectedRoute><CashManagement /></ProtectedRoute>} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
            </div>
        </div>
    );
}

export default function App() {
    return <AppShell />;
}
