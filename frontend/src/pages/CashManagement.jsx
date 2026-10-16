import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
    AlertCircle, ArrowDownToLine, ArrowLeftRight, Banknote, Check, CheckCircle2,
    ChevronRight, CircleDollarSign, ClipboardCheck, Clock3, FileCheck2, Plus,
    RefreshCw, ShieldCheck, Wallet, X
} from "lucide-react";

import { getApiError } from "../api/client";
import {
    createBankDeposit, createCashSubmission, createCollection, getBankDeposits,
    getCollections, getCurrentUser, getLoans, getSubmissions, markBankDeposit,
    reconcileBankDeposit, reviewCashSubmission
} from "../api/cmrsApi";
import "./CashManagement.css";

const money = (value) => {
    const amount = Number(value ?? 0);
    if (!Number.isFinite(amount)) return "₹0.00";
    return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 2 }).format(amount);
};

const valueOf = (item, ...keys) => {
    for (const key of keys) {
        const value = item?.[key];
        if (value !== undefined && value !== null && value !== "") return value;
    }
    return "—";
};

const itemId = (item) => String(item?.id ?? item?.pk ?? item?.loan_id ?? "");
const loanLabel = (loan) => {
    const customer = loan?.customer;
    const customerLabel = typeof customer === "object" && customer !== null
        ? [customer.full_name, customer.name, customer.first_name, customer.last_name].filter(Boolean).join(" ")
        : (loan?.customer_name || customer || "");
    const number = loan?.loan_number || loan?.account_number || loan?.loan_account_number || `Loan ${itemId(loan)}`;
    const amount = loan?.principal_amount ?? loan?.loan_amount ?? loan?.amount;
    const parts = [number, customerLabel, amount !== undefined && amount !== null ? `₹${amount}` : ""].filter(Boolean);
    return parts.join(" · ");
};
const itemAmount = (item) => Number(valueOf(item, "amount", "expected_amount", "deposited_amount", "credited_amount") || 0);
const displayDate = (value) => {
    if (!value || value === "—") return "—";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
};
const statusClass = (status) => {
    const normalized = String(status || "unknown").toLowerCase();
    if (["accepted", "matched", "reconciled", "deposited", "success"].includes(normalized)) return "success";
    if (["rejected", "discrepancy", "short", "failed"].includes(normalized)) return "danger";
    if (["submitted", "prepared", "excess", "pending"].includes(normalized)) return "warning";
    return "neutral";
};
const parseIds = (value) => value.split(",").map((id) => id.trim()).filter(Boolean);

function StatusBadge({ status }) {
    return <span className={`cm-status ${statusClass(status)}`}>{String(status || "Unknown").replaceAll("_", " ")}</span>;
}

function Alert({ kind = "error", children, onClose }) {
    if (!children) return null;
    return (
        <div className={`cm-alert ${kind}`} role={kind === "error" ? "alert" : "status"}>
            {kind === "error" ? <AlertCircle size={17} /> : <CheckCircle2 size={17} />}
            <span>{children}</span>
            {onClose && <button type="button" onClick={onClose} aria-label="Dismiss message"><X size={15} /></button>}
        </div>
    );
}

function Field({ label, children, hint }) {
    return <div className="cm-field"><label>{label}</label>{children}{hint && <small>{hint}</small>}</div>;
}

function SectionTitle({ icon: Icon, eyebrow, title, description, action }) {
    return (
        <div className="cm-section-title">
            <div className="cm-section-title-main">
                <div className="cm-section-icon"><Icon size={19} /></div>
                <div><span className="cm-eyebrow">{eyebrow}</span><h2>{title}</h2><p>{description}</p></div>
            </div>
            {action}
        </div>
    );
}

function EmptyState({ title, detail }) {
    return <div className="cm-empty"><div><FileCheck2 size={23} /></div><strong>{title}</strong><p>{detail}</p></div>;
}

function DataTable({ columns, rows, rowKey, emptyTitle, emptyDetail }) {
    if (!rows?.length) return <EmptyState title={emptyTitle || "Nothing to show yet"} detail={emptyDetail || "Records will appear here when available."} />;
    return (
        <div className="cm-table-wrap">
            <table className="cm-table">
                <thead><tr>{columns.map((column) => <th key={column.key}>{column.label}</th>)}</tr></thead>
                <tbody>{rows.map((row, index) => (
                    <tr key={rowKey ? rowKey(row) : itemId(row) || index}>
                        {columns.map((column) => <td key={column.key}>{column.render ? column.render(row) : valueOf(row, column.key)}</td>)}
                    </tr>
                ))}</tbody>
            </table>
        </div>
    );
}

export default function CashManagement() {
    const queryClient = useQueryClient();
    const [notice, setNotice] = useState(null);
    const [collectionForm, setCollectionForm] = useState({ loan: "", amount: "", notes: "" });
    const [collectionIds, setCollectionIds] = useState("");
    const [submissionIds, setSubmissionIds] = useState("");
    const [reviewForm, setReviewForm] = useState({ id: "", decision: "accept", review_notes: "" });
    const [depositForm, setDepositForm] = useState({ id: "", bank_name: "", bank_reference: "", deposited_amount: "", deposit_date: new Date().toISOString().slice(0, 10) });
    const [newDepositIds, setNewDepositIds] = useState("");
    const [reconcileForm, setReconcileForm] = useState({ id: "", statement_reference: "", statement_date: new Date().toISOString().slice(0, 10), credited_amount: "", notes: "" });
    const [activeTab, setActiveTab] = useState("collections");

    const currentUser = useQuery({ queryKey: ["cmrs", "me"], queryFn: getCurrentUser });
    const loans = useQuery({ queryKey: ["cmrs", "loans"], queryFn: getLoans });
    const collections = useQuery({ queryKey: ["cmrs", "collections"], queryFn: getCollections });
    const submissions = useQuery({ queryKey: ["cmrs", "submissions"], queryFn: getSubmissions });
    const deposits = useQuery({ queryKey: ["cmrs", "deposits"], queryFn: getBankDeposits });

    const user = currentUser.data || {};
    const role = String(user.role || "").toUpperCase();
    const isAdmin = role === "ADMIN";
    const isManager = role === "BRANCH_MANAGER";
    const isAgent = role === "COLLECTION_AGENT";
    const canReview = isAdmin || isManager;
    const canManageDeposits = isAdmin || isManager;
    const canReconcile = isAdmin;
    const initialLoading = currentUser.isLoading;

    const allCollections = collections.data || [];
    const allSubmissions = submissions.data || [];
    const allDeposits = deposits.data || [];
    const allLoans = loans.data || [];

    const totals = useMemo(() => ({
        collected: allCollections.reduce((sum, row) => sum + Number(row.amount || 0), 0),
        collections: allCollections.length,
        pendingSubmissions: allSubmissions.filter((row) => String(row.status).toUpperCase() === "SUBMITTED").length,
        deposits: allDeposits.length,
        deposited: allDeposits.reduce((sum, row) => sum + Number(row.deposited_amount || row.expected_amount || 0), 0),
    }), [allCollections, allSubmissions, allDeposits]);

    async function refreshAll() {
        await queryClient.invalidateQueries({ queryKey: ["cmrs"] });
    }

    const collectionMutation = useMutation({
        mutationFn: createCollection,
        onSuccess: async () => {
            setCollectionForm({ loan: "", amount: "", notes: "" });
            setNotice({ kind: "success", text: "Cash collection recorded successfully." });
            await refreshAll();
        },
        onError: (error) => setNotice({ kind: "error", text: getApiError(error) }),
    });

    const submissionMutation = useMutation({
        mutationFn: createCashSubmission,
        onSuccess: async () => {
            setCollectionIds("");
            setNotice({ kind: "success", text: "Cash submission created successfully." });
            await refreshAll();
        },
        onError: (error) => setNotice({ kind: "error", text: getApiError(error) }),
    });

    const reviewMutation = useMutation({
        mutationFn: ({ id, decision, review_notes }) => reviewCashSubmission(id, decision, review_notes),
        onSuccess: async () => {
            setReviewForm({ id: "", decision: "accept", review_notes: "" });
            setNotice({ kind: "success", text: "Submission review saved." });
            await refreshAll();
        },
        onError: (error) => setNotice({ kind: "error", text: getApiError(error) }),
    });

    const createDepositMutation = useMutation({
        mutationFn: createBankDeposit,
        onSuccess: async () => {
            setNewDepositIds("");
            setNotice({ kind: "success", text: "Bank deposit prepared successfully." });
            await refreshAll();
        },
        onError: (error) => setNotice({ kind: "error", text: getApiError(error) }),
    });

    const markDepositMutation = useMutation({
        mutationFn: ({ id, payload }) => markBankDeposit(id, payload),
        onSuccess: async () => {
            setDepositForm({ id: "", bank_name: "", bank_reference: "", deposited_amount: "", deposit_date: new Date().toISOString().slice(0, 10) });
            setNotice({ kind: "success", text: "Bank deposit marked as deposited." });
            await refreshAll();
        },
        onError: (error) => setNotice({ kind: "error", text: getApiError(error) }),
    });

    const reconcileMutation = useMutation({
        mutationFn: ({ id, payload }) => reconcileBankDeposit(id, payload),
        onSuccess: async () => {
            setReconcileForm({ id: "", statement_reference: "", statement_date: new Date().toISOString().slice(0, 10), credited_amount: "", notes: "" });
            setNotice({ kind: "success", text: "Company-account reconciliation recorded." });
            await refreshAll();
        },
        onError: (error) => setNotice({ kind: "error", text: getApiError(error) }),
    });

    useEffect(() => {
        if (!window.location.hash) return;
        const id = decodeURIComponent(window.location.hash.slice(1));
        setActiveTab(id);
        const timer = window.setTimeout(() => document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
        return () => window.clearTimeout(timer);
    }, []);

    if (initialLoading) {
        return <div className="cm-page"><div className="cm-loading"><span className="cm-spinner" /><strong>Loading your workspace</strong><p>Verifying your account and permissions...</p></div></div>;
    }

    if (currentUser.isError) {
        return (
            <div className="cm-page">
                <div className="cm-auth-error">
                    <div className="cm-auth-error-icon"><ShieldCheck size={25} /></div>
                    <h1>Unable to load your account</h1>
                    <p>{getApiError(currentUser.error)}</p>
                    <p className="cm-auth-help">Please sign in again. Your account permissions are enforced by the backend.</p>
                    <button className="cm-button primary" onClick={() => currentUser.refetch()}><RefreshCw size={15} /> Retry</button>
                </div>
            </div>
        );
    }

    const refreshError = [loans, collections, submissions, deposits].find((query) => query.isError);
    const isMutating = collectionMutation.isPending || submissionMutation.isPending || reviewMutation.isPending || createDepositMutation.isPending || markDepositMutation.isPending || reconcileMutation.isPending;

    function setTabAndScroll(id) {
        setActiveTab(id);
        document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
        if (window.location.hash !== `#${id}`) window.history.replaceState(null, "", `#${id}`);
    }

    function handleCreateCollection(event) {
        event.preventDefault();
        setNotice(null);
        if (!collectionForm.loan) {
            setNotice({ kind: "error", text: "Select a loan before recording a collection." });
            return;
        }
        if (!collectionForm.amount || Number(collectionForm.amount) <= 0) {
            setNotice({ kind: "error", text: "Enter an amount greater than zero." });
            return;
        }
        collectionMutation.mutate({
            loan: Number(collectionForm.loan),
            amount: collectionForm.amount,
            notes: collectionForm.notes.trim(),
            idempotency_key: window.crypto?.randomUUID?.() || `cmrs-${Date.now()}-${Math.random().toString(36).slice(2)}`,
        });
    }

    function handleCreateSubmission(event) {
        event.preventDefault();
        const ids = parseIds(collectionIds);
        if (!ids.length) {
            setNotice({ kind: "error", text: "Enter one or more collection IDs separated by commas." });
            return;
        }
        submissionMutation.mutate(ids.map((id) => Number(id)));
    }

    function handleReview(event) {
        event.preventDefault();
        if (!reviewForm.id) {
            setNotice({ kind: "error", text: "Select a cash submission to review." });
            return;
        }
        reviewMutation.mutate({ ...reviewForm, id: Number(reviewForm.id) });
    }

    function handleCreateDeposit(event) {
        event.preventDefault();
        const ids = parseIds(newDepositIds);
        if (!ids.length) {
            setNotice({ kind: "error", text: "Enter accepted submission IDs separated by commas." });
            return;
        }
        createDepositMutation.mutate(ids.map((id) => Number(id)));
    }

    function handleMarkDeposit(event) {
        event.preventDefault();
        if (!depositForm.id || !depositForm.bank_name.trim() || !depositForm.bank_reference.trim() || !depositForm.deposited_amount || Number(depositForm.deposited_amount) < 0) {
            setNotice({ kind: "error", text: "Complete the deposit ID, bank, bank reference, and deposited amount." });
            return;
        }
        markDepositMutation.mutate({
            id: Number(depositForm.id),
            payload: {
                bank_name: depositForm.bank_name.trim(),
                bank_reference: depositForm.bank_reference.trim(),
                deposited_amount: depositForm.deposited_amount,
                deposit_date: depositForm.deposit_date,
            },
        });
    }

    function handleReconcile(event) {
        event.preventDefault();
        if (!reconcileForm.id || !reconcileForm.statement_reference.trim() || reconcileForm.credited_amount === "") {
            setNotice({ kind: "error", text: "Complete the deposit, statement reference, and credited amount." });
            return;
        }
        reconcileMutation.mutate({
            id: Number(reconcileForm.id),
            payload: {
                statement_reference: reconcileForm.statement_reference.trim(),
                statement_date: reconcileForm.statement_date,
                credited_amount: reconcileForm.credited_amount,
                notes: reconcileForm.notes.trim(),
            },
        });
    }

    return (
        <div className="cm-page">
            <div className="cm-page-heading">
                <div>
                    <span className="cm-eyebrow">CASH OPERATIONS</span>
                    <h1>Cash management</h1>
                    <p>Record, submit, deposit, and reconcile collected funds.</p>
                </div>
                <button type="button" className="cm-button subtle" onClick={refreshAll} disabled={isMutating}>
                    <RefreshCw size={15} /> Refresh data
                </button>
            </div>

            <div className="cm-user-strip">
                <div className="cm-user-avatar">{String(user.username || user.email || "U").slice(0, 1).toUpperCase()}</div>
                <div className="cm-user-info"><strong>{valueOf(user, "full_name", "username", "email")}</strong><span>{valueOf(user, "role_display", "role")} {user.branch_name ? `· ${user.branch_name}` : ""}</span></div>
                <span className="cm-auth-pill"><span /> Authenticated</span>
            </div>

            {notice && <Alert kind={notice.kind} onClose={() => setNotice(null)}>{notice.text}</Alert>}
            {refreshError && <Alert>Some data could not be loaded: {getApiError(refreshError.error)}</Alert>}

            <div className="cm-stats-grid">
                <article className="cm-stat-card"><div className="cm-stat-icon blue"><Wallet size={18} /></div><span>Total collections</span><strong>{totals.collections}</strong><small>Recorded repayment entries</small></article>
                <article className="cm-stat-card"><div className="cm-stat-icon green"><CircleDollarSign size={18} /></div><span>Amount collected</span><strong>{money(totals.collected)}</strong><small>Based on visible collection records</small></article>
                <article className="cm-stat-card"><div className="cm-stat-icon amber"><Clock3 size={18} /></div><span>Pending submissions</span><strong>{totals.pendingSubmissions}</strong><small>Awaiting branch review</small></article>
                <article className="cm-stat-card"><div className="cm-stat-icon violet"><Banknote size={18} /></div><span>Bank deposits</span><strong>{totals.deposits}</strong><small>{money(totals.deposited)} deposited / expected</small></article>
            </div>

            <div className="cm-tabbar" role="tablist" aria-label="Cash operations sections">
                <button className={activeTab === "collections" ? "active" : ""} onClick={() => setTabAndScroll("collections")}><Wallet size={16} /> Collections</button>
                <button className={activeTab === "reconciliation" ? "active" : ""} onClick={() => setTabAndScroll("reconciliation")}><ArrowLeftRight size={16} /> Reconciliation</button>
                <button className={activeTab === "deposits" ? "active" : ""} onClick={() => setTabAndScroll("deposits")}><Banknote size={16} /> Bank deposits</button>
            </div>

            <section className="cm-section" id="collections">
                <SectionTitle icon={Wallet} eyebrow="01 / COLLECTIONS" title="Cash collections" description="Record a repayment against a loan and review receipt history." />
                {isAgent && (
                    <form className="cm-form-card" onSubmit={handleCreateCollection}>
                        <div className="cm-form-heading"><div><h3>Record a collection</h3><p>Use the loan linked to the customer repayment.</p></div><span className="cm-form-step">NEW ENTRY</span></div>
                        <div className="cm-form-grid">
                            <Field
                                label="Loan *"
                                hint={loans.isLoading
                                    ? "Loading loans assigned to your account…"
                                    : loans.isError
                                        ? "Could not load loans. Use Retry below and check the backend if this continues."
                                        : allLoans.length === 0
                                            ? "No loans are available to this agent. Create a loan and ensure its customer/assignment is linked to this agent."
                                            : `${allLoans.length} loan${allLoans.length === 1 ? "" : "s"} available. Select the loan receiving this repayment.`}
                            >
                                <select
                                    value={collectionForm.loan}
                                    onChange={(event) => setCollectionForm((prev) => ({ ...prev, loan: event.target.value }))}
                                    required
                                    disabled={loans.isLoading || loans.isError || allLoans.length === 0}
                                >
                                    <option value="">
                                        {loans.isLoading ? "Loading loans…" : loans.isError ? "Loans could not be loaded" : allLoans.length === 0 ? "No eligible loans found" : "Select a loan"}
                                    </option>
                                    {allLoans.map((loan, index) => {
                                        const id = itemId(loan);
                                        return id ? <option value={id} key={id}>{loanLabel(loan)}</option> : null;
                                    })}
                                </select>
                                {loans.isError && <button type="button" className="cm-button subtle" onClick={() => loans.refetch()} style={{ marginTop: 8 }}>Retry loading loans</button>}
                            </Field>
                            <Field label="Collection amount (₹) *">
                                <input type="number" min="0.01" step="0.01" inputMode="decimal" placeholder="e.g. 2500.00" value={collectionForm.amount} onChange={(event) => setCollectionForm((prev) => ({ ...prev, amount: event.target.value }))} required />
                            </Field>
                            <Field label="Notes" hint="Optional collection details">
                                <input type="text" maxLength={500} placeholder="Add a note" value={collectionForm.notes} onChange={(event) => setCollectionForm((prev) => ({ ...prev, notes: event.target.value }))} />
                            </Field>
                        </div>
                        <div className="cm-form-actions"><span className="cm-form-note"><ShieldCheck size={14} /> Receipt reference is generated by the backend.</span><button className="cm-button primary" type="submit" disabled={collectionMutation.isPending}><Plus size={15} /> {collectionMutation.isPending ? "Saving..." : "Record collection"}</button></div>
                    </form>
                )}
                {!isAgent && <div className="cm-info-banner"><ShieldCheck size={16} /><span>Your role is <strong>{valueOf(user, "role_display", "role")}</strong>. Collection creation is available to collection agents according to the backend permissions.</span></div>}
                <div className="cm-data-card">
                    <div className="cm-data-card-heading"><div><h3>Collection history</h3><p>{allCollections.length} records available to your account</p></div><span className="cm-count-chip">{allCollections.length} records</span></div>
                    <DataTable
                        rows={allCollections}
                        emptyTitle="No collections found"
                        emptyDetail="Collection records will appear here once they are created."
                        columns={[
                            { key: "receipt_number", label: "Receipt", render: (row) => <span className="cm-primary-cell">{valueOf(row, "receipt_number", "id")}</span> },
                            { key: "collection_id", label: "collection id", render: (row) => <span className="cm-primary-cell">{valueOf(row, "id")}</span> },
                            { key: "customer", label: "Customer / loan", render: (row) => <div className="cm-cell-stack"><strong>{valueOf(row, "customer_name", "customer", "loan_number", "loan")}</strong><span>Loan {valueOf(row, "loan_number", "loan_id", "loan")}</span></div> },
                            { key: "amount", label: "Amount", render: (row) => <strong>{money(row.amount)}</strong> },
                            { key: "collection_date", label: "Date", render: (row) => displayDate(valueOf(row, "collection_date", "created_at")) },
                            { key: "status", label: "Status", render: (row) => <StatusBadge status={valueOf(row, "status", "collection_status") === "—" ? "Recorded" : valueOf(row, "status", "collection_status")} /> },
                        ]}
                    />
                </div>

                {isAgent && (
                    <form className="cm-inline-form" onSubmit={handleCreateSubmission}>
                        <div className="cm-inline-form-copy"><div className="cm-small-icon"><ArrowDownToLine size={18} /></div><div><h3>Submit cash to branch</h3><p>Enter collection IDs that have not already been submitted. Separate multiple IDs with commas.</p></div></div>
                        <div className="cm-inline-fields"><Field label="Collection IDs *"><input value={collectionIds} onChange={(event) => setCollectionIds(event.target.value)} placeholder="e.g. 12, 13, 14" required /></Field><button className="cm-button primary" disabled={submissionMutation.isPending}><Plus size={15} /> {submissionMutation.isPending ? "Submitting..." : "Create submission"}</button></div>
                    </form>
                )}
            </section>

            <section className="cm-section" id="reconciliation">
                <SectionTitle icon={ClipboardCheck} eyebrow="02 / BRANCH HANDOVER" title="Cash submission reconciliation" description="Track submissions from agents and review cash received at the branch." />
                <div className="cm-data-card">
                    <div className="cm-data-card-heading"><div><h3>Cash submissions</h3><p>Submission status and expected amounts</p></div><span className="cm-count-chip">{allSubmissions.length} records</span></div>
                    <DataTable
                        rows={allSubmissions}
                        emptyTitle="No submissions found"
                        emptyDetail="Agent cash submissions will appear here."
                        columns={[
                            { key: "submission_number", label: "Submission", render: (row) => <span className="cm-primary-cell">{valueOf(row, "submission_number", "id")}</span> },
                            { key: "branch", label: "Branch", render: (row) => valueOf(row, "branch_name", "branch_code", "branch") },
                            { key: "submitted_by", label: "Submitted by", render: (row) => valueOf(row, "submitted_by_name", "submitted_by_username", "submitted_by") },
                            { key: "amount", label: "Expected amount", render: (row) => <strong>{money(row.amount)}</strong> },
                            { key: "submission_date", label: "Date", render: (row) => displayDate(valueOf(row, "submission_date", "created_at")) },
                            { key: "status", label: "Status", render: (row) => <StatusBadge status={row.status} /> },
                        ]}
                    />
                </div>

                {canReview && (
                    <form className="cm-form-card" onSubmit={handleReview}>
                        <div className="cm-form-heading"><div><h3>Review a cash submission</h3><p>Approve or reject a submission received by the branch.</p></div><span className="cm-form-step">REVIEW</span></div>
                        <div className="cm-form-grid">
                            <Field label="Submission ID *"><input type="number" min="1" value={reviewForm.id} onChange={(event) => setReviewForm((prev) => ({ ...prev, id: event.target.value }))} placeholder="Submission ID" required /></Field>
                            <Field label="Decision *"><select value={reviewForm.decision} onChange={(event) => setReviewForm((prev) => ({ ...prev, decision: event.target.value }))}><option value="accept">Accept</option><option value="reject">Reject</option></select></Field>
                            <Field label="Review notes"><input value={reviewForm.review_notes} onChange={(event) => setReviewForm((prev) => ({ ...prev, review_notes: event.target.value }))} placeholder="Optional review notes" maxLength={500} /></Field>
                        </div>
                        <div className="cm-form-actions"><span className="cm-form-note"><ShieldCheck size={14} /> The backend validates branch access and status.</span><button className="cm-button primary" disabled={reviewMutation.isPending}><Check size={15} /> {reviewMutation.isPending ? "Saving..." : "Save review"}</button></div>
                    </form>
                )}
            </section>

            <section className="cm-section" id="deposits">
                <SectionTitle icon={Banknote} eyebrow="03 / BANK SETTLEMENT" title="Bank deposits & company reconciliation" description="Prepare deposits from accepted submissions, record bank details, and match credited amounts." />
                {canManageDeposits && (
                    <form className="cm-form-card" onSubmit={handleCreateDeposit}>
                        <div className="cm-form-heading"><div><h3>Prepare a bank deposit</h3><p>Only accepted cash submissions should be selected.</p></div><span className="cm-form-step">NEW DEPOSIT</span></div>
                        <div className="cm-form-grid one-column">
                            <Field label="Accepted submission IDs *" hint="Enter one or more submission IDs separated by commas.">
                                <input value={newDepositIds} onChange={(event) => setNewDepositIds(event.target.value)} placeholder="e.g. 21, 22" required />
                            </Field>
                        </div>
                        <div className="cm-form-actions"><span className="cm-form-note"><ShieldCheck size={14} /> The backend calculates the expected deposit amount.</span><button className="cm-button primary" disabled={createDepositMutation.isPending}><Plus size={15} /> {createDepositMutation.isPending ? "Preparing..." : "Prepare deposit"}</button></div>
                    </form>
                )}

                <div className="cm-data-card">
                    <div className="cm-data-card-heading"><div><h3>Deposit register</h3><p>Deposit amounts and settlement status</p></div><span className="cm-count-chip">{allDeposits.length} records</span></div>
                    <DataTable
                        rows={allDeposits}
                        emptyTitle="No bank deposits found"
                        emptyDetail="Prepared deposits will appear here."
                        columns={[
                            { key: "deposit_number", label: "Deposit", render: (row) => <span className="cm-primary-cell">{valueOf(row, "deposit_number", "id")}</span> },
                            { key: "bank_name", label: "Bank", render: (row) => valueOf(row, "bank_name", "bank_reference") },
                            { key: "expected_amount", label: "Expected", render: (row) => <strong>{money(valueOf(row, "expected_amount", "amount"))}</strong> },
                            { key: "deposited_amount", label: "Deposited", render: (row) => money(valueOf(row, "deposited_amount", "expected_amount")) },
                            { key: "deposit_date", label: "Date", render: (row) => displayDate(valueOf(row, "deposit_date", "created_at")) },
                            { key: "status", label: "Status", render: (row) => <StatusBadge status={row.status} /> },
                            { key: "reconciliation", label: "Company credit", render: (row) => <div className="cm-cell-stack"><StatusBadge status={row.reconciliation?.status || row.reconciliation_status || "Not reconciled"} /><span>{money(row.reconciliation?.credited_amount ?? row.credited_amount ?? 0)}</span></div> },
                        ]}
                    />
                </div>

                {canManageDeposits && (
                    <form className="cm-form-card" onSubmit={handleMarkDeposit}>
                        <div className="cm-form-heading"><div><h3>Record completed bank deposit</h3><p>Save the actual bank transaction details after depositing funds.</p></div><span className="cm-form-step">BANK DETAILS</span></div>
                        <div className="cm-form-grid">
                            <Field label="Deposit ID *"><input type="number" min="1" value={depositForm.id} onChange={(event) => setDepositForm((prev) => ({ ...prev, id: event.target.value }))} placeholder="Deposit ID" required /></Field>
                            <Field label="Bank name *"><input value={depositForm.bank_name} onChange={(event) => setDepositForm((prev) => ({ ...prev, bank_name: event.target.value }))} placeholder="e.g. HDFC Bank" required /></Field>
                            <Field label="Bank reference *"><input value={depositForm.bank_reference} onChange={(event) => setDepositForm((prev) => ({ ...prev, bank_reference: event.target.value }))} placeholder="Transaction reference" required /></Field>
                            <Field label="Actual deposited amount (₹) *"><input type="number" min="0" step="0.01" value={depositForm.deposited_amount} onChange={(event) => setDepositForm((prev) => ({ ...prev, deposited_amount: event.target.value }))} placeholder="0.00" required /></Field>
                            <Field label="Deposit date *"><input type="date" value={depositForm.deposit_date} onChange={(event) => setDepositForm((prev) => ({ ...prev, deposit_date: event.target.value }))} required /></Field>
                        </div>
                        <div className="cm-form-actions"><span className="cm-form-note"><ShieldCheck size={14} /> Bank reference uniqueness is enforced by the backend.</span><button className="cm-button primary" disabled={markDepositMutation.isPending}><Check size={15} /> {markDepositMutation.isPending ? "Saving..." : "Mark as deposited"}</button></div>
                    </form>
                )}

                {canReconcile && (
                    <form className="cm-form-card" onSubmit={handleReconcile}>
                        <div className="cm-form-heading"><div><h3>Reconcile company-account credit</h3><p>Compare the bank statement credit against the expected and deposited amounts.</p></div><span className="cm-form-step">ADMIN ONLY</span></div>
                        <div className="cm-form-grid">
                            <Field label="Deposit ID *"><input type="number" min="1" value={reconcileForm.id} onChange={(event) => setReconcileForm((prev) => ({ ...prev, id: event.target.value }))} placeholder="Deposit ID" required /></Field>
                            <Field label="Statement reference *"><input value={reconcileForm.statement_reference} onChange={(event) => setReconcileForm((prev) => ({ ...prev, statement_reference: event.target.value }))} placeholder="Bank statement reference" required /></Field>
                            <Field label="Statement date *"><input type="date" value={reconcileForm.statement_date} onChange={(event) => setReconcileForm((prev) => ({ ...prev, statement_date: event.target.value }))} required /></Field>
                            <Field label="Credited amount (₹) *"><input type="number" min="0" step="0.01" value={reconcileForm.credited_amount} onChange={(event) => setReconcileForm((prev) => ({ ...prev, credited_amount: event.target.value }))} placeholder="0.00" required /></Field>
                            <Field label="Notes"><input value={reconcileForm.notes} onChange={(event) => setReconcileForm((prev) => ({ ...prev, notes: event.target.value }))} placeholder="Optional reconciliation notes" maxLength={500} /></Field>
                        </div>
                        <div className="cm-form-actions"><span className="cm-form-note"><ShieldCheck size={14} /> Only an administrator can reconcile company-account credit.</span><button className="cm-button primary" disabled={reconcileMutation.isPending}><ArrowLeftRight size={15} /> {reconcileMutation.isPending ? "Reconciling..." : "Reconcile credit"}</button></div>
                    </form>
                )}
            </section>

            <footer className="cm-footer"><span>CMRS · Operational records are scoped by your backend permissions.</span><span><ShieldCheck size={13} /> Secure workflow</span></footer>
        </div>
    );
}
