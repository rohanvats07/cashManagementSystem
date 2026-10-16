import api from "./client";

function listFromResponse(data) {
    // Support standard DRF lists, pagination, and common API response wrappers.
    if (Array.isArray(data)) return data;
    if (!data || typeof data !== "object") return [];

    for (const key of ["results", "data", "items", "loans", "records"]) {
        const value = data[key];
        if (Array.isArray(value)) return value;
        if (value && typeof value === "object") {
            const nested = listFromResponse(value);
            if (nested.length) return nested;
        }
    }

    return [];
}

export async function getCurrentUser() {
    const { data } = await api.get("/me/");
    return data;
}

export async function getHealth() {
    const { data } = await api.get("/health/");
    return data;
}

export async function getLoans() {
    const { data } = await api.get("/loans/");
    return listFromResponse(data);
}

export async function getCollections() {
    const { data } = await api.get("/collections/");
    return listFromResponse(data);
}

export async function createCollection(payload) {
    const { data } = await api.post("/collections/", payload);
    return data;
}

export async function getSubmissions() {
    const { data } = await api.get("/cash-submissions/");
    return listFromResponse(data);
}

export async function createCashSubmission(collectionIds) {
    const { data } = await api.post("/cash-submissions/", {
        collection_ids: collectionIds,
    });
    return data;
}

export async function reviewCashSubmission(id, decision, reviewNotes = "") {
    const normalizedDecision = {
        accept: "ACCEPTED",
        reject: "REJECTED",
    }[decision];

    if (!normalizedDecision) {
        throw new Error(`Invalid review decision: ${decision}`);
    }

    const { data } = await api.post(
        `/cash-submissions/${id}/review/`,
        {
            decision: normalizedDecision,
            review_notes: reviewNotes,
        }
    );

    return data;
}

export async function getBankDeposits() {
    const { data } = await api.get("/bank-deposits/");
    return listFromResponse(data);
}

export async function createBankDeposit(submissionIds) {
    const { data } = await api.post("/bank-deposits/", {
        submission_ids: submissionIds,
    });
    return data;
}

export async function markBankDeposit(id, payload) {
    const { data } = await api.post(`/bank-deposits/${id}/mark-deposited/`, payload);
    return data;
}

export async function reconcileBankDeposit(id, payload) {
    const { data } = await api.post(`/bank-deposits/${id}/reconcile/`, payload);
    return data;
}
