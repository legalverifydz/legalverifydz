"""
scoring.py -- LegalVerifyDZ
================================================================
Risk-scoring logic, pulled out of the original monolithic analyse()
function (sections 19-20): how confident the extraction was, and how
risky the contract is, given the findings rules.py raised.

Deliberately knows nothing about wording/templates/language -- it
only works with plain data (counts, presence/absence), which is what
makes the score reproducible and easy to unit-test in isolation.
================================================================
"""


def compute_score(ctx, findings):
    """
    ctx:      the dict returned by extractors.extract_all().
    findings: the list returned by rules.build_findings().

    Returns (risk, lvl, cls, confidence).
    """

    contract_type = ctx["contract_type"]
    parties = ctx["parties"]
    amounts = ctx["amounts"]
    durations = ctx["durations"]
    clauses = ctx["clauses"]

    # =========================================================
    # 19. EXTRACTED INFORMATION QUALITY
    # =========================================================

    extraction_items = 0
    extraction_success = 0

    # Contract type
    extraction_items += 1
    if contract_type != "Unknown":
        extraction_success += 1

    # Parties
    extraction_items += 1
    if len(parties) >= 2:
        extraction_success += 1

    # Amount
    extraction_items += 1
    if amounts:
        extraction_success += 1

    # Duration
    extraction_items += 1
    if durations:
        extraction_success += 1

    # Clause structure
    extraction_items += 1
    if clauses:
        extraction_success += 1

    confidence = round(
        (extraction_success / extraction_items) * 100
    )

    # =========================================================
    # 20. RISK SCORE
    # =========================================================

    high_count = sum(
        1
        for finding in findings
        if finding.get("severity") == "High"
    )

    moderate_count = sum(
        1
        for finding in findings
        if finding.get("severity") == "Moderate"
    )

    low_count = sum(
        1
        for finding in findings
        if finding.get("severity") == "Low"
    )

    # Base score
    risk = (
        high_count * 40
        + moderate_count * 15
        + low_count * 5
    )

    # A High finding means the contract should not be
    # classified as Low or Moderate solely because the
    # numerical sum is below the threshold.
    if high_count > 0:

        risk = max(
            risk,
            60
        )

    risk = min(
        100,
        int(risk)
    )

    if risk < 30:

        lvl = "Low"
        cls = "low"

    elif risk < 60:

        lvl = "Moderate"
        cls = "med"

    else:

        lvl = "High"
        cls = "high"

    return risk, lvl, cls, confidence


if __name__ == "__main__":
    import extractors
    import rules

    demo = """This service contract is made between Company Alpha and Company Beta.
The contract value is 15000 USD. The duration is 12 months.
The parties agree to termination conditions, liability provisions and a penalty clause."""

    ctx = extractors.extract_all(demo)

    def _stub_finding(name):
        return {
            "title": name, "issue": name, "explanation": name,
            "recommendation": name, "replacement": name,
            "clause_status": "stub", "original_text": name,
        }

    fx_stub = {
        key: _stub_finding(key)
        for key in [
            "TERMINATION_HIGH", "TERMINATION_MISSING",
            "PENALTY_EXCLUDED", "PENALTY_MISSING",
            "PAYMENT_MISSING", "PAYMENT_VAGUE",
            "DISPUTE_MISSING", "LIABILITY_MISSING", "PARTIES_MISSING",
        ]
    }
    ox_stub = {
        key: key for key in
        ["termination", "liability", "dispute", "payment", "obligation", "parties"]
    }

    findings, obs, recommendations = rules.build_findings(ctx, fx_stub, ox_stub)
    risk, lvl, cls, confidence = compute_score(ctx, findings)

    assert lvl in ("Low", "Moderate", "High")
    assert cls in ("low", "med", "high")
    assert 0 <= risk <= 100
    assert 0 <= confidence <= 100
    print("scoring self-test OK: risk=%s lvl=%s cls=%s confidence=%s" % (risk, lvl, cls, confidence))
