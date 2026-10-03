"""
rules.py -- LegalVerifyDZ
================================================================
Finding-construction logic, pulled out of the original monolithic
analyse() function (sections 10-18, 21-22): decides, clause by
clause, whether a finding should be raised, using the extracted
context from extractors.extract_all() and the localized finding
templates (fx/ox) from app.py's TR dict for the report language the
user chose.

This module owns the six clause analyses (termination, penalty,
payment, dispute, liability, parties) plus the informational
observations and the recommendation list derived from findings.
Risk scoring itself lives in scoring.py, not here.
================================================================
"""

import re


def build_findings(ctx, fx, ox):
    """
    ctx: the dict returned by extractors.extract_all().
    fx:  TR[report_lang]["findings"] -- localized finding templates.
    ox:  TR[report_lang]["observations"] -- localized observation templates.

    Returns (findings, obs, recommendations).
    """

    find_clause = ctx["find_clause"]
    clean_text = ctx["clean_text"]
    unique_keep_order = ctx["unique_keep_order"]
    parties = ctx["parties"]

    # =========================================================
    # 10. FINDINGS STORAGE
    # =========================================================

    findings = []

    def add_finding(
        title,
        severity,
        original_clause,
        issue,
        explanation,
        recommendation,
        replacement,
        finding_type,
        clause_status="Present"
    ):

        findings.append(
            {
                "title": title,
                "severity": severity,
                "original_text": clean_text(original_clause),
                "issue": clean_text(issue),
                "explanation": clean_text(explanation),
                "recommendation": clean_text(recommendation),
                "replacement": clean_text(replacement),
                "finding_type": finding_type,
                "clause_status": clause_status
            }
        )

    # =========================================================
    # 11. KEYWORD GROUPS
    # =========================================================

    termination_groups = [
        [
            "résiliation",
            "termination",
            "résilier",
            "termination of",
            "فسخ",
            "إنهاء العقد",
            "إنهاء"
        ]
    ]

    penalty_groups = [
        [
            "pénalité",
            "pénalités",
            "penalty",
            "penalties",
            "late fee",
            "retard",
            "غرامة",
            "غرامات",
            "التأخير"
        ]
    ]

    payment_groups = [
        [
            "paiement",
            "prix",
            "facturation",
            "règlement",
            "payment",
            "price",
            "invoice",
            "invoicing",
            "الدفع",
            "السداد",
            "الثمن",
            "الفاتورة"
        ]
    ]

    liability_groups = [
        [
            "responsabilité",
            "responsable",
            "liability",
            "responsible",
            "المسؤولية",
            "مسؤول",
            "المسؤول"
        ]
    ]

    dispute_groups = [
        [
            "litige",
            "tribunal",
            "juridiction",
            "arbitrage",
            "dispute",
            "court",
            "jurisdiction",
            "arbitration",
            "نزاع",
            "المحكمة",
            "الاختصاص",
            "التحكيم"
        ]
    ]

    obligation_groups = [
        [
            "obligation",
            "obligations",
            "engagement",
            "engagements",
            "obligations of",
            "obligation de",
            "obligations de",
            "التزام",
            "التزامات"
        ]
    ]

    # =========================================================
    # 12. TERMINATION ANALYSIS
    # =========================================================

    termination_clause = find_clause(
        termination_groups
    )

    if termination_clause:

        low = termination_clause.lower()

        unrestricted_patterns = [
            "à tout moment",
            "sans motif",
            "sans justification",
            "sans préavis",
            "sans aucune condition",
            "librement",
            "at any time",
            "without cause",
            "without notice",
            "without justification",
            "freely",
            "في أي وقت",
            "دون سبب",
            "دون مبرر",
            "دون إشعار",
            "دون أي شرط",
            "بشكل منفرد"
        ]

        is_unrestricted = any(
            pattern in low
            for pattern in unrestricted_patterns
        )

        if is_unrestricted:

            _f = fx["TERMINATION_HIGH"]
            add_finding(
                title=_f["title"],
                severity="High",
                original_clause=termination_clause,
                issue=_f["issue"],
                explanation=_f["explanation"],
                recommendation=_f["recommendation"],
                replacement=_f["replacement"],
                finding_type="Termination",
                clause_status=_f["clause_status"]
            )

        else:

            # A termination clause exists and does not contain obvious
            # unrestricted wording. Do not automatically create a risk.
            pass

    else:

        # Missing termination clause is informational/moderate,
        # not automatically High.
        _f = fx["TERMINATION_MISSING"]
        add_finding(
            title=_f["title"],
            severity="Moderate",
            original_clause=_f["original_text"],
            issue=_f["issue"],
            explanation=_f["explanation"],
            recommendation=_f["recommendation"],
            replacement=_f["replacement"],
            finding_type="Termination",
            clause_status=_f["clause_status"]
        )

    # =========================================================
    # 13. PENALTY ANALYSIS
    # =========================================================

    penalty_clause = find_clause(
        penalty_groups
    )

    if penalty_clause:

        low = penalty_clause.lower()

        no_penalty_patterns = [
            "aucune pénalité",
            "aucune penalite",
            "aucune pénalité de retard",
            "no penalty",
            "no penalties",
            "no late fee",
            "aucune indemnité",
            "لا توجد غرامة",
            "لا تفرض غرامة",
            "لا توجد غرامات",
            "دون غرامة"
        ]

        no_penalty = any(
            pattern in low
            for pattern in no_penalty_patterns
        )

        if no_penalty:

            _f = fx["PENALTY_EXCLUDED"]
            add_finding(
                title=_f["title"],
                severity="Moderate",
                original_clause=penalty_clause,
                issue=_f["issue"],
                explanation=_f["explanation"],
                recommendation=_f["recommendation"],
                replacement=_f["replacement"],
                finding_type="Penalty",
                clause_status=_f["clause_status"]
            )

    else:

        _f = fx["PENALTY_MISSING"]
        add_finding(
            title=_f["title"],
            severity="Moderate",
            original_clause=_f["original_text"],
            issue=_f["issue"],
            explanation=_f["explanation"],
            recommendation=_f["recommendation"],
            replacement=_f["replacement"],
            finding_type="Penalty",
            clause_status=_f["clause_status"]
        )

    # =========================================================
    # 14. PAYMENT ANALYSIS
    # =========================================================

    payment_clause = find_clause(
        payment_groups
    )

    if not payment_clause:

        _f = fx["PAYMENT_MISSING"]
        add_finding(
            title=_f["title"],
            severity="Moderate",
            original_clause=_f["original_text"],
            issue=_f["issue"],
            explanation=_f["explanation"],
            recommendation=_f["recommendation"],
            replacement=_f["replacement"],
            finding_type="Payment",
            clause_status=_f["clause_status"]
        )

    # If payment clause exists, do NOT create a risk automatically.
    # We only inspect whether it is obviously incomplete.
    else:

        low = payment_clause.lower()

        vague_payment = (
            (
                "paiement" in low
                or "règlement" in low
                or "payment" in low
                or "الدفع" in low
            )
            and not re.search(
                r"\b\d+\s*(?:jours?|days?|j|يوم|أيام)\b",
                low,
                re.I
            )
            and not any(
                x in low
                for x in [
                    "à la réception",
                    "après réception",
                    "à échéance",
                    "within",
                    "upon receipt",
                    "selon facture",
                    "facture",
                    "invoice",
                    "وفق الفاتورة",
                    "عند الاستلام"
                ]
            )
        )

        if vague_payment:

            _f = fx["PAYMENT_VAGUE"]
            add_finding(
                title=_f["title"],
                severity="Moderate",
                original_clause=payment_clause,
                issue=_f["issue"],
                explanation=_f["explanation"],
                recommendation=_f["recommendation"],
                replacement=_f["replacement"],
                finding_type="Payment",
                clause_status=_f["clause_status"]
            )

    # =========================================================
    # 15. DISPUTE / JURISDICTION ANALYSIS
    # =========================================================

    dispute_clause = find_clause(
        dispute_groups
    )

    # IMPORTANT:
    # If a court/jurisdiction/arbitration clause exists, it is NOT missing.
    # We only flag its absence.
    if not dispute_clause:

        _f = fx["DISPUTE_MISSING"]
        add_finding(
            title=_f["title"],
            severity="Moderate",
            original_clause=_f["original_text"],
            issue=_f["issue"],
            explanation=_f["explanation"],
            recommendation=_f["recommendation"],
            replacement=_f["replacement"],
            finding_type="Dispute",
            clause_status=_f["clause_status"]
        )

    # =========================================================
    # 16. LIABILITY ANALYSIS
    # =========================================================

    liability_clause = find_clause(
        liability_groups
    )

    if not liability_clause:

        # Absence of liability wording is less severe than an
        # explicitly abusive liability clause.
        _f = fx["LIABILITY_MISSING"]
        add_finding(
            title=_f["title"],
            severity="Moderate",
            original_clause=_f["original_text"],
            issue=_f["issue"],
            explanation=_f["explanation"],
            recommendation=_f["recommendation"],
            replacement=_f["replacement"],
            finding_type="Liability",
            clause_status=_f["clause_status"]
        )

    # =========================================================
    # 17. PARTIES ANALYSIS
    # =========================================================

    if not parties:

        _f = fx["PARTIES_MISSING"]
        add_finding(
            title=_f["title"],
            severity="Moderate",
            original_clause=_f["original_text"],
            issue=_f["issue"],
            explanation=_f["explanation"],
            recommendation=_f["recommendation"],
            replacement=_f["replacement"],
            finding_type="Parties",
            clause_status=_f["clause_status"]
        )

    # =========================================================
    # 18. OBLIGATIONS
    # =========================================================

    obligation_clause = find_clause(
        obligation_groups
    )

    # Informational only when present.
    # We do not create an automatic risk simply because wording exists.

    # =========================================================
    # 21. OBSERVATIONS
    #    Informational observations only.
    #    Findings remain the source of truth.
    # =========================================================

    obs = []

    if termination_clause:
        obs.append(ox["termination"])

    if liability_clause:
        obs.append(ox["liability"])

    if dispute_clause:
        obs.append(ox["dispute"])

    if payment_clause:
        obs.append(ox["payment"])

    if obligation_clause:
        obs.append(ox["obligation"])

    if parties:
        obs.append(ox["parties"])

    # =========================================================
    # 22. RECOMMENDATIONS
    #
    # Keep recommendations in findings.
    # The report renderer can avoid duplicating them.
    # =========================================================

    recommendations = []

    for finding in findings:

        recommendation = finding.get(
            "recommendation",
            ""
        )

        if recommendation:
            recommendations.append(
                recommendation
            )

    recommendations = unique_keep_order(
        recommendations
    )


    return findings, obs, recommendations


if __name__ == "__main__":
    import extractors

    demo = """This service contract is made between Company Alpha and Company Beta.
The contract value is 15000 USD. The duration is 12 months.
The parties agree to termination conditions, liability provisions and a penalty clause."""

    ctx = extractors.extract_all(demo)

    # Minimal fake templates, just enough to exercise every branch
    # without needing the real TR dict from app.py.
    def _stub_finding(name):
        return {
            "title": name, "issue": name + " issue",
            "explanation": name + " explanation",
            "recommendation": name + " recommendation",
            "replacement": name + " replacement",
            "clause_status": "stub", "original_text": name + " original",
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

    findings, obs, recommendations = build_findings(ctx, fx_stub, ox_stub)
    assert isinstance(findings, list) and len(findings) >= 1
    assert isinstance(obs, list)
    assert isinstance(recommendations, list)
    print("rules self-test OK:", len(findings), "findings,", len(obs), "observations,", len(recommendations), "recommendations")
    for f in findings:
        print(" -", f["finding_type"], "|", f["severity"], "|", f["title"])
