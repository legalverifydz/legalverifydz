"""
criminal.py -- LegalVerifyDZ
================================================================
Detects contract features that can move a breach out of purely CIVIL
liability and into potential CRIMINAL liability under Algerian law.

This module only DETECTS (language-independent, no Streamlit). The
wording shown to the user -- and the article numbers -- live in
CRIMINAL_BASIS in app.py, so each citation can be reviewed in one place.

The three alerts (articles checked against Algerian university course
materials before being used):

  ENTRUSTED_PROPERTY -> Code pénal art. 376, abus de confiance
        (property handed over under one of the contracts the article
        lists: deposit, loan for use, mandate, pledge, lease, or to
        perform work with or without pay).
  ADVANCE_PAYMENT    -> Code pénal art. 372, escroquerie
        (only if false name/capacity or fraudulent manoeuvres are used;
        an advance payment alone is a civil matter).
  CHEQUE_PAYMENT     -> Code pénal art. 374-375, cheque without funds.

An alert is SUPPRESSED when the contract already contains the usual
protection (a handover record, a bank guarantee), so a well-drafted
contract is not flagged for something it has already solved.
================================================================
"""

import re

SERVICE_TYPE = "Service / Maintenance Contract"

_EQUIPMENT = (
    r"معدات|تجهيزات|آلات|أجهزة|مركبات?|سيارات?|"
    r"[ée]quipements?|mat[ée]riels?|machines?|v[ée]hicules?|"
    r"equipment|machinery|vehicles?"
)

_TRUST_WORDS = (
    # Arabic
    r"وديعة|عارية|رهن حيازي|عهدة|"
    # French
    r"\bd[ée]p[oô]t\b|\bd[ée]pos[ée]e?s?\b|\bgage\b|\bnantissement\b|"
    r"\bpr[eê]t [àa] usage\b|\bconfi[ée]e?s?\b|\bremet(?:tra)?\b|"
    r"\bremis(?:e|es)? (?:au|à|a)\b|"
    # English
    r"\bbailment\b|\bentrust(?:ed)?\b|\bin custody\b|\bcustody of\b|"
    r"\bpledged?\b|\bloan for use\b|\bhanded over to\b"
)

_HANDOVER_RECORD = (
    r"محضر\s+(?:تسليم|استلام|معاينة)|"
    r"proc[èe]s[- ]verbal\s+de\s+(?:remise|r[ée]ception|livraison|constat)|"
    r"(?:handover|delivery|acceptance|inspection)\s+(?:report|protocol|record|certificate)"
)

_ADVANCE = (
    r"دفعة\s+مقدمة|مقدّم\s+الثمن|عربون|تسبيق|دفع\s+مسبق|الدفع\s+المسبق|"
    r"\bacompte\b|\barrhes\b|\bavance\s+(?:de|sur|forfaitaire)\b|"
    r"\bpaiement\s+(?:anticip[ée]|d['’]avance)\b|\bversement\s+(?:anticip[ée]|initial)\b|"
    r"\badvance\s+payment\b|\bdown\s+payment\b|\bupfront\s+payment\b|"
    r"\bpre-?payment\b|\badvance\s+of\b"
)

_GUARANTEE = (
    r"ضمان\s+بنكي|كفالة\s+بنكية|كفالة|"
    r"garantie\s+bancaire|\bcaution\b|"
    r"bank\s+guarantee|performance\s+bond|advance\s+payment\s+guarantee"
)

_CHEQUE = (
    r"شيك|شيكات|"
    r"\bch[eè]ques?\b|"
    r"\bcheques?\b|\bbank\s+check\b|\bby\s+check\b|\bpayment\s+by\s+check\b"
)


def _excerpt(text, match, radius=90):
    """A short, single-line quote around the match, to show WHY an alert
    was raised."""
    start = max(0, match.start() - radius)
    end = min(len(text), match.end() + radius)
    snippet = re.sub(r"\s+", " ", text[start:end]).strip()
    return ("…" if start > 0 else "") + snippet + ("…" if end < len(text) else "")


def detect(text, contract_type=None):
    """
    Returns a list of (code, excerpt) for every criminal-law alert that
    applies, in a fixed order. `excerpt` is the contract passage that
    triggered it.
    """
    text = text or ""
    alerts = []

    # --- 1. property entrusted to the other party (abus de confiance) ---
    trigger = re.search(_TRUST_WORDS, text, re.I)

    if trigger is None and contract_type == SERVICE_TYPE:
        # A maintenance/service contract implicitly hands the client's
        # equipment to the provider to perform work on it.
        trigger = re.search(_EQUIPMENT, text, re.I)

    if trigger is not None and not re.search(_HANDOVER_RECORD, text, re.I):
        alerts.append(("ENTRUSTED_PROPERTY", _excerpt(text, trigger)))

    # --- 2. advance payment (escroquerie exposure) ---
    advance = re.search(_ADVANCE, text, re.I)
    if advance is not None and not re.search(_GUARANTEE, text, re.I):
        alerts.append(("ADVANCE_PAYMENT", _excerpt(text, advance)))

    # --- 3. payment by cheque ---
    cheque = re.search(_CHEQUE, text, re.I)
    if cheque is not None:
        alerts.append(("CHEQUE_PAYMENT", _excerpt(text, cheque)))

    return alerts


if __name__ == "__main__":
    samples = {
        "maintenance, equipment, no handover record": (
            "Contrat de maintenance des équipements industriels du Client.", SERVICE_TYPE),
        "same, WITH a handover record": (
            "Maintenance des équipements du Client. Un procès-verbal de remise est établi.", SERVICE_TYPE),
        "advance by cheque, no guarantee": (
            "Le Client verse un acompte de 50% par chèque.", None),
        "advance with bank guarantee": (
            "Le Client verse un acompte contre garantie bancaire.", None),
        "arabic: عربون + شيك": ("دفع المشتري عربونا قدره 100000 دينار والباقي بشيك.", None),
        "clean": ("The price is paid by bank transfer within 30 days.", None),
    }
    for label, (text, ctype) in samples.items():
        print("%-40s ->" % label, [code for code, _ in detect(text, ctype)])
