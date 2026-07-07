import os

# An optimized mock dictionary simulating an enterprise banking policy directory.
# In a full production deployment, this would query an external vector database (like ChromaDB or Milvus).
ENTERPRISE_POLICY_KNOWLEDGE_BASE = {
    "dormant_risk": (
        "Policy Section 4.2 (Dormant Accounts): Accounts with zero user-initiated transaction activity "
        "for 180 consecutive days must be flagged as DORMANT. High-risk profiles include accounts with balances "
        "exceeding $50,000 that suddenly exhibit inactivity. Reactivation requires physical verification."
    ),
    "withdrawal_limits": (
        "SOP Section 1.9 (Limits): Standard daily ATM withdrawal limits for basic checking accounts are "
        "capped at $1,000 USD. Limit overrides up to $5,000 require a Tier 2 branch manager signature."
    ),
    "loan_compliance": (
        "Compliance Rule 7.1 (Mortgages): Debt-to-Income (DTI) ratios for residential mortgage assessments "
        "must maintain a strict ceiling of 43%, unless backed by additional verifiable cash collateral assets."
    ),
    "fraud_velocity": (
        "Security Protocol 9.0 (Velocity Anti-Fraud): Automated immediate account suspension must trigger "
        "if transaction velocity data points exceed 5 unique geolocation sweeps within a 60-minute window."
    )
}

def perform_rag_search(query: str) -> str:
    """
    Scans through unstructured enterprise banking policies, compliance guidelines, 
    and SOP documents to return relevant textual contextual snippets.
    """
    normalized_query = query.lower()
    matched_snippets = []

    # Fast text interface scoring logic matching query intents against knowledge tokens
    for topic, text_content in ENTERPRISE_POLICY_KNOWLEDGE_BASE.items():
        # Split tokens to check for overlapping intent words
        keywords = topic.split("_")
        if any(word in normalized_query for word in keywords) or topic in normalized_query:
            matched_snippets.append(text_content)

    if not matched_snippets:
        return (
            f"Search Context for '{query}': No specific internal banking policy or compliance "
            f"SOP documents matched this request in the knowledge base."
        )

    return "\n\n".join(matched_snippets)