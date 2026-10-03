import streamlit as st
import pdfplumber
import docx
import re
import hashlib
import base64
import extractors
import rules
import scoring
import ocr
from datetime import datetime
from pathlib import Path
# openpyxl is no longer needed for the user database (moved to SQLite),
# kept only if you still export findings to Excel elsewhere.

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="LegalVerifyDZ", layout="wide")

# NOTE: the user database moved from an Excel file (users.xlsx) to
# SQLite (see DB_FILE = legalverify.db below, near hash_password()).
# USERS_FILE is kept only so nothing external that still references it
# breaks; it is no longer read or written by this app.
USERS_FILE = Path("users.xlsx")

# ==========================================
# CSS
# ==========================================
st.markdown("""
<style>
.main {background-color: #F3F4F6;}

body {
    background-color: #0E1117;
}

section[data-testid="stSidebar"] {
    background-color: #111827;
    border-right: 1px solid #1F2937;
}

[data-testid="stSidebar"] * {
    color: white;
}

.card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 25px;
    margin-bottom: 20px;
    backdrop-filter: blur(10px);
    box-shadow: 0 0 20px rgba(79,139,255,0.08);
    transition: 0.3s;
}

.card:hover {
    transform: translateY(-3px);
    box-shadow: 0 0 30px rgba(79,139,255,0.20);
}

.low {
    background:#DCFCE7;
    padding:10px;
    border-radius:10px;
    color:#166534;
}

.med {
    background:#FEF9C3;
    padding:10px;
    border-radius:10px;
    color:#854D0E;
}

.high {
    background:#FEE2E2;
    padding:10px;
    border-radius:10px;
    color:#991B1B;
}

.stButton>button {
    border-radius: 12px;
    background: linear-gradient(90deg, #2563EB, #4F8BFF);
    color: white;
    border: none;
    padding: 12px 18px;
    font-weight: 600;
}

.stButton>button:hover {
    opacity: 0.92;
}

.auth-box {
    max-width: 700px;
    margin: 30px auto;
    padding: 30px;
    border-radius: 20px;
    background: white;
    box-shadow: 0 5px 25px rgba(0,0,0,0.08);
}

.disclaimer-box {
    margin-top: 24px;
    padding: 16px 20px;
    border: 2px solid #B45309;
    border-radius: 12px;
    background: #FFFBEB;
    color: #78350F;
    font-weight: 700;
    font-size: 15px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)


# ==========================================
# BRAND LOGO
# ==========================================
# A shield (trust/protection) wrapped around a contract document with a
# verification checkmark -- replaces the generic ⚖️ emoji with a mark
# specific to what the platform actually does (verify contracts).
_LOGO_SVG = """
<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"
     width="{size}" height="{size}">
  <defs>
    <linearGradient id="lvzShield" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#2563EB"/>
      <stop offset="100%" stop-color="#4F8BFF"/>
    </linearGradient>
  </defs>
  <path d="M50 4 L88 18 L88 46 Q88 78 50 96 Q12 78 12 46 L12 18 Z"
        fill="url(#lvzShield)"/>
  <rect x="31" y="28" width="38" height="46" rx="4" fill="#FFFFFF"/>
  <rect x="37" y="37" width="26" height="4" rx="2" fill="#CBD5E1"/>
  <rect x="37" y="46" width="26" height="4" rx="2" fill="#CBD5E1"/>
  <rect x="37" y="55" width="16" height="4" rx="2" fill="#CBD5E1"/>
  <circle cx="66" cy="68" r="17" fill="#16A34A" stroke="#FFFFFF" stroke-width="3"/>
  <path d="M58 68 L64 74 L75 61" fill="none" stroke="#FFFFFF"
        stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""


def logo_html(size=80):
    """
    Inline brand mark at the given pixel size, as a single-line base64
    <img> tag.

    Why not embed the raw multi-line <svg>...</svg> directly? Because a
    nested, multi-line SVG block placed inside a larger HTML string
    passed to st.markdown(..., unsafe_allow_html=True) can confuse
    Streamlit's Markdown-to-HTML parser partway through -- it can stop
    treating the rest of the string as HTML and print it as literal
    text instead (exactly the "raw tags visible on screen" symptom).
    A single-line base64 data-URI <img> tag has no nested tags for the
    parser to get confused by, so it embeds reliably no matter what
    HTML it's placed inside.
    """
    svg = _LOGO_SVG.format(size=size)
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return (
        '<img src="data:image/svg+xml;base64,{b64}" '
        'width="{size}" height="{size}" '
        'style="display:block;margin:0 auto;" />'
    ).format(b64=encoded, size=size)


# ==========================================
# SESSION STATE
# ==========================================
defaults = {
    "authenticated": False,
    "user": None,
    "guest_used": False,
    "auth_screen": False,
    "analysis_text": None,
    "analysis_filename": None,
    "last_analysis": None,
    "history_open_id": None,
    "last_analysis_id": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ==========================================
# LANGUAGE
# ==========================================
lang = st.sidebar.selectbox(
    "Language",
    ["English", "Français", "العربية"]
)

T = {
    "English": {
        "dashboard": "Dashboard",
        "generate": "Generate Contract",
        "analysis": "Smart Analysis",
        "analyze": "Analyze",
        "risk": "Risk",
        "score": "Score",
        "login": "Login",
        "signup": "Create Account",
        "guest": "Continue as Guest",
        "logout": "Logout",
        "history": "History",
    },
    "Français": {
        "dashboard": "Dashboard",
        "generate": "Contrat",
        "analysis": "Analyse",
        "analyze": "Analyser",
        "risk": "Risque",
        "score": "Score",
        "login": "Connexion",
        "signup": "Créer un compte",
        "guest": "Continuer comme invité",
        "logout": "Déconnexion",
        "history": "Historique",
    },
    "العربية": {
        "dashboard": "لوحة التحكم",
        "generate": "إنشاء عقد",
        "analysis": "التحليل الذكي",
        "analyze": "تحليل",
        "risk": "المخاطر",
        "score": "النسبة",
        "login": "تسجيل الدخول",
        "signup": "إنشاء حساب",
        "guest": "الدخول كزائر",
        "logout": "تسجيل الخروج",
        "history": "السجلّ",
    },
}

t = T[lang]


# ==========================================
# ANALYSIS CONTENT TRANSLATIONS
# ==========================================
# T (above) translates the interface CHROME (buttons, tabs, labels).
# TR translates the ANALYSIS CONTENT itself: finding titles/issues/
# explanations/recommendations/replacements, observations, and the
# executive-summary sentence templates that analyse() builds.
#
# These are two different things on purpose:
#   - detected_language (set inside analyse()) is the language OF THE
#     CONTRACT, used only to pick the right extraction regex. It must
#     NOT change based on what the user selects here.
#   - report_lang (passed into analyse()) is the language the USER
#     chose in the sidebar. It decides which TR[...] templates are
#     used to phrase the output, regardless of the contract's own
#     language.
#
# Actual contract text extracted verbatim (original clauses, party
# names, amounts, durations) is never translated -- only the fixed
# sentences the app itself writes around that extracted text.
# ==========================================

TR = {
    "English": {
        "levels": {"Low": "Low", "Moderate": "Moderate", "High": "High"},
        "contract_types": {
            "Service / Maintenance Contract": "Service / Maintenance Contract",
            "Sale / Purchase Contract": "Sale / Purchase Contract",
            "Lease / Rental Contract": "Lease / Rental Contract",
            "Unknown": "Unspecified",
        },
        "observations": {
            "termination": "A termination clause was identified and reviewed for contractual safeguards.",
            "liability": "A liability / responsibility clause was identified.",
            "dispute": "A dispute resolution / jurisdiction provision was identified.",
            "payment": "Payment-related provisions were identified.",
            "obligation": "Contractual obligations were identified.",
            "parties": "Contracting parties were identified from the contract text.",
        },
        "summary": {
            "type_known": "The contract was classified as {type}.",
            "type_unknown": "The contract type could not be confidently determined.",
            "parties_known": "The identified contracting parties are {parties}.",
            "parties_unknown": "The contracting parties could not be confidently identified.",
            "amounts": "A contract amount of {amounts} was identified.",
            "durations": "The identified duration is {durations}.",
            "risk_low": "The analysis indicates a relatively low level of identified contractual risk based on the clauses and information that could be extracted.",
            "risk_moderate": "The analysis identified several contractual points that may require clarification or stronger safeguards.",
            "risk_high": "The analysis identified significant contractual risks that should be reviewed before relying on the agreement.",
        },
        "findings": {
            "TERMINATION_HIGH": {
                "title": "Termination",
                "issue": "The termination clause allows termination without sufficiently defined conditions or safeguards.",
                "explanation": "An unrestricted termination mechanism may create uncertainty regarding notice, legitimate grounds, and the contractual consequences of termination.",
                "recommendation": "Define the grounds for termination, notice period, formal notice requirements and consequences of termination.",
                "replacement": "Either party may terminate the contract for a defined contractual cause by written notice, subject to a reasonable notice period and settlement of obligations arising before the effective termination date.",
                "clause_status": "Present but insufficiently safeguarded",
            },
            "TERMINATION_MISSING": {
                "title": "Termination",
                "original_text": "Clause under analysis: Absence of a clearly identified termination mechanism.",
                "issue": "No clearly identified contractual termination mechanism was found.",
                "explanation": "The contract does not clearly define how the contractual relationship may be terminated and under which conditions.",
                "recommendation": "Define the grounds, procedure, notice period and consequences of termination.",
                "replacement": "Either party may terminate the contract in the cases specified herein by written notice and subject to the applicable notice period.",
                "clause_status": "Missing or not clearly identified",
            },
            "PENALTY_EXCLUDED": {
                "title": "Contractual Penalty",
                "issue": "No contractual penalty or compensation mechanism is provided for delay or non-performance.",
                "explanation": "The clause expressly excludes or does not establish a financial mechanism addressing delay or certain forms of non-performance.",
                "recommendation": "Define objective conditions, a calculation method, applicable limits and the circumstances triggering contractual penalties or compensation.",
                "replacement": "In the event of unjustified delay attributable to the defaulting party, a contractual penalty shall apply according to a predefined calculation method and within the limits agreed by the parties.",
                "clause_status": "Present but excludes penalty mechanism",
            },
            "PENALTY_MISSING": {
                "title": "Contractual Penalty",
                "original_text": "Clause under analysis: Absence of a clear penalty or compensation mechanism.",
                "issue": "No clear contractual penalty or compensation mechanism was identified.",
                "explanation": "The contract does not clearly establish financial consequences for delay or defined forms of non-performance.",
                "recommendation": "Consider defining objective conditions, calculation method and applicable limits for contractual penalties or compensation.",
                "replacement": "In the event of unjustified delay attributable to the defaulting party, a contractual penalty may apply according to a predefined calculation method.",
                "clause_status": "Missing or not clearly identified",
            },
            "PAYMENT_MISSING": {
                "title": "Payment Terms",
                "original_text": "Clause under analysis: Absence of clearly identified payment terms.",
                "issue": "No clearly identified payment terms were found.",
                "explanation": "The contract should establish the payment mechanism, timing and conditions applicable to the contractual price.",
                "recommendation": "Specify payment deadlines, invoicing conditions, payment method and consequences of late payment.",
                "replacement": "Invoices shall be paid within the agreed payment period from the date of receipt, subject to the contractual conditions set out herein.",
                "clause_status": "Missing or not clearly identified",
            },
            "PAYMENT_VAGUE": {
                "title": "Payment Terms",
                "issue": "The payment provision does not clearly define the applicable payment timing or conditions.",
                "explanation": "An insufficiently precise payment provision may create disagreement regarding when and how payment becomes due.",
                "recommendation": "Specify the payment deadline, invoicing conditions and payment method.",
                "replacement": "Payment shall be made within the agreed period following receipt of the corresponding invoice, in accordance with the payment method specified in this contract.",
                "clause_status": "Present but insufficiently precise",
            },
            "DISPUTE_MISSING": {
                "title": "Dispute Resolution / Jurisdiction",
                "original_text": "Clause under analysis: Absence of a clearly identified dispute resolution or jurisdiction provision.",
                "issue": "No clearly identified dispute resolution or jurisdiction provision was found.",
                "explanation": "The contract does not clearly indicate how disputes should be resolved or which competent authority should have jurisdiction.",
                "recommendation": "Specify the applicable dispute resolution mechanism and competent jurisdiction.",
                "replacement": "Any dispute arising from the interpretation or performance of this contract shall be submitted to the competent jurisdiction agreed by the parties, subject to the applicable law.",
                "clause_status": "Missing or not clearly identified",
            },
            "LIABILITY_MISSING": {
                "title": "Liability",
                "original_text": "Clause under analysis: Absence of a clearly identified liability provision.",
                "issue": "No clearly identified contractual liability provision was found.",
                "explanation": "The contract does not clearly allocate contractual responsibility for damage, breach or non-performance.",
                "recommendation": "Clarify the responsibilities of each party and the conditions governing contractual liability.",
                "replacement": "Each party shall be responsible for damage directly resulting from its proven breach of the contractual obligations expressly assigned to it.",
                "clause_status": "Missing or not clearly identified",
            },
            "PARTIES_MISSING": {
                "title": "Contracting Parties",
                "original_text": "Clause under analysis: Contracting parties could not be confidently identified from the available text.",
                "issue": "The contracting parties could not be confidently identified.",
                "explanation": "The available text does not provide sufficiently clear identification of the legal entities or persons entering into the contract.",
                "recommendation": "Clearly identify each contracting party using its legal name, legal form and relevant identification details.",
                "replacement": "Between [Full legal name of Party 1], duly identified and represented by its authorized representative, and [Full legal name of Party 2], duly identified and represented by its authorized representative.",
                "clause_status": "Missing or not clearly identified",
            },
        },
        "report_ui": {
            "report_title": "LegalVerifyDZ - Contract Analysis Report",
            "generated": "Generated",
            "contract": "Contract",
            "type": "Type",
            "risk_level": "Risk level",
            "confidence": "Confidence",
            "compliance_score": "Compliance score",
            "findings_count": "Findings",
            "high": "high", "moderate": "moderate", "low": "low",
            "executive_summary": "EXECUTIVE SUMMARY",
            "parties": "PARTIES",
            "amounts": "AMOUNTS",
            "durations": "DURATIONS",
            "observations": "OBSERVATIONS",
            "recommendations": "RECOMMENDATIONS",
            "detailed_findings": "DETAILED RISK FINDINGS",
            "none": "None",
            "not_identified": "Not identified",
            "no_finding": "No specific finding was recorded for this contract.",
            "finding_label": "Finding",
            "clause_status": "Clause status",
            "na": "n/a",
            "original_clause": "Original clause:",
            "clause_not_located": "(clause not located in the document)",
            "problem": "Problem:",
            "not_specified": "(not specified)",
            "why_it_matters": "Why it matters:",
            "recommendation_label": "Recommendation:",
            "suggested_wording": "Suggested safer wording:",
            "not_provided": "(not provided)",
            "disclaimer": "DISCLAIMER: automated analysis. It does not replace the review of a qualified lawyer and carries no legal liability.",
            "csv_headers": ["#", "Title", "Severity", "Clause status", "Original text", "Issue", "Explanation", "Recommendation", "Suggested wording"],
            "tab_summary": "🧠 Summary", "tab_findings": "⚠️ Findings", "tab_data": "📑 Extracted data", "tab_export": "📥 Export",
            "compliance_metric": "Compliance score", "risk_metric": "Risk", "confidence_metric": "Confidence", "findings_metric": "Findings",
            "no_high_risk": "no high risk", "n_high": "{n} high",
            "health_progress": "Contract health · {score}%",
            "high_risk_warning": "{n} high-risk finding(s). Review them before signing.",
            "moderate_warning": "{n} moderate finding(s) needing clarification.",
            "no_risk_success": "No high or moderate finding was detected.",
            "priority_actions": "✅ Priority actions",
            "no_finding_info": "No detailed finding was produced for this contract.",
            "severity_filter": "Severity",
            "search_findings": "Search in findings",
            "shown_of_total": "{shown} of {total} finding(s) displayed.",
            "clause_not_located_caption": "Clause not located in the document.",
            "problem_label": "Problem",
            "why_it_matters_label": "Why it matters",
            "recommendation_bold": "Recommendation",
            "suggested_wording_bold": "Suggested safer wording",
            "parties_header": "👥 Parties", "amounts_header": "💰 Amounts", "durations_header": "⏱️ Durations",
            "observations_header": "🔍 Observations",
            "no_observation": "No observation recorded.",
            "text_report_btn": "📄 Text report", "csv_btn": "📊 Findings (CSV)", "json_btn": "🧩 JSON (API)",
            "preview_report": "Preview the text report",
            "footer_disclaimer": "⚖️ Automated analysis — it does not replace the review of a qualified lawyer.",
            "shape_warning": "The analysis result does not have the expected 11-value shape; some sections may be incomplete.",
            "guest_title": "📌 Guest Analysis",
            "guest_info": "This is a limited guest analysis. Create an account to unlock the complete report, analysis history and advanced features.",
            "contract_type_header": "📄 Contract Type",
            "risk_level_header": "⚠️ Risk Level",
            "confidence_header": "📊 Confidence Score",
            "summary_header": "🧠 Summary",
            "key_findings_header": "🔎 Key Findings",
            "parties_detected": "👥 Contracting parties detected.",
            "parties_not_detected": "👥 Parties could not be confidently extracted.",
            "amount_detected": "💰 Contract value detected.",
            "amount_not_detected": "💰 Contract value not confidently detected.",
            "duration_detected": "⏳ Contract duration detected.",
            "duration_not_detected": "⏳ Contract duration not confidently detected.",
            "guest_warning": "🔐 Guest mode provides only a limited result. Create an account to access the full analysis report.",
            "history_title": "🗂️ Analysis History",
            "history_empty": "No saved analyses yet. Analyses you run while logged in will appear here.",
            "history_date": "Date", "history_view": "View report", "history_delete": "Delete",
            "history_deleted": "Analysis deleted.",
            "history_back": "⬅️ Back to history",
            "lawyer_section_title": "🤝 Next step",
            "lawyer_question": "This report is an automated analysis. How would you like to proceed?",
            "lawyer_option_ai_only": "✅ I'll rely on this analysis",
            "lawyer_option_request": "⚖️ Request a lawyer review",
            "lawyer_ai_only_ack": "Noted. Remember this remains an automated analysis, not legal advice.",
            "lawyer_request_success": "Your request has been recorded. We'll reach out once a partner lawyer is available.",
            "lawyer_no_partners_yet": "Note: the platform has not yet contracted with any partner lawyer. This request is queued and you will be contacted as soon as one is available.",
            "ocr_used_note": "📷 This document appears to be a scanned file. Text was extracted using OCR (optical character recognition) -- please review the extracted text below, as OCR can occasionally misread characters.",
        },
    },
    "Français": {
        "levels": {"Low": "Faible", "Moderate": "Modéré", "High": "Élevé"},
        "contract_types": {
            "Service / Maintenance Contract": "Contrat de service / maintenance",
            "Sale / Purchase Contract": "Contrat de vente / achat",
            "Lease / Rental Contract": "Contrat de bail / location",
            "Unknown": "Non déterminé",
        },
        "observations": {
            "termination": "Une clause de résiliation a été identifiée et examinée quant à ses garanties contractuelles.",
            "liability": "Une clause de responsabilité a été identifiée.",
            "dispute": "Une clause de règlement des différends / juridiction a été identifiée.",
            "payment": "Des dispositions relatives au paiement ont été identifiées.",
            "obligation": "Des obligations contractuelles ont été identifiées.",
            "parties": "Les parties contractantes ont été identifiées dans le texte du contrat.",
        },
        "summary": {
            "type_known": "Le contrat a été classé comme {type}.",
            "type_unknown": "Le type de contrat n'a pas pu être déterminé avec certitude.",
            "parties_known": "Les parties contractantes identifiées sont {parties}.",
            "parties_unknown": "Les parties contractantes n'ont pas pu être identifiées avec certitude.",
            "amounts": "Un montant contractuel de {amounts} a été identifié.",
            "durations": "La durée identifiée est {durations}.",
            "risk_low": "L'analyse indique un niveau de risque contractuel relativement faible, sur la base des clauses et informations qui ont pu être extraites.",
            "risk_moderate": "L'analyse a identifié plusieurs points contractuels qui pourraient nécessiter des clarifications ou des garanties renforcées.",
            "risk_high": "L'analyse a identifié des risques contractuels importants qui devraient être examinés avant de se fier à cet accord.",
        },
        "findings": {
            "TERMINATION_HIGH": {
                "title": "Résiliation",
                "issue": "La clause de résiliation permet une résiliation sans conditions ni garanties suffisamment définies.",
                "explanation": "Un mécanisme de résiliation non encadré peut créer une incertitude quant au préavis, aux motifs légitimes et aux conséquences contractuelles de la résiliation.",
                "recommendation": "Définir les motifs de résiliation, le délai de préavis, les modalités formelles de notification et les conséquences de la résiliation.",
                "replacement": "Chaque partie peut résilier le contrat pour une cause contractuelle définie, par notification écrite, sous réserve d'un délai de préavis raisonnable et du règlement des obligations nées avant la date effective de résiliation.",
                "clause_status": "Présente mais insuffisamment encadrée",
            },
            "TERMINATION_MISSING": {
                "title": "Résiliation",
                "original_text": "Clause analysée : absence de mécanisme de résiliation clairement identifié.",
                "issue": "Aucun mécanisme contractuel de résiliation clairement identifié n'a été trouvé.",
                "explanation": "Le contrat ne définit pas clairement comment la relation contractuelle peut être résiliée ni dans quelles conditions.",
                "recommendation": "Définir les motifs, la procédure, le délai de préavis et les conséquences de la résiliation.",
                "replacement": "Chaque partie peut résilier le contrat dans les cas prévus aux présentes, par notification écrite et sous réserve du délai de préavis applicable.",
                "clause_status": "Absente ou non clairement identifiée",
            },
            "PENALTY_EXCLUDED": {
                "title": "Pénalité contractuelle",
                "issue": "Aucun mécanisme de pénalité ou d'indemnisation contractuelle n'est prévu en cas de retard ou d'inexécution.",
                "explanation": "La clause exclut expressément ou n'établit pas de mécanisme financier en cas de retard ou de certaines formes d'inexécution.",
                "recommendation": "Définir des conditions objectives, une méthode de calcul, des limites applicables et les circonstances déclenchant des pénalités ou indemnités contractuelles.",
                "replacement": "En cas de retard injustifié imputable à la partie défaillante, une pénalité contractuelle s'applique selon une méthode de calcul prédéfinie et dans les limites convenues par les parties.",
                "clause_status": "Présente mais exclut le mécanisme de pénalité",
            },
            "PENALTY_MISSING": {
                "title": "Pénalité contractuelle",
                "original_text": "Clause analysée : absence de mécanisme clair de pénalité ou d'indemnisation.",
                "issue": "Aucun mécanisme contractuel clair de pénalité ou d'indemnisation n'a été identifié.",
                "explanation": "Le contrat n'établit pas clairement les conséquences financières en cas de retard ou de certaines formes d'inexécution.",
                "recommendation": "Envisager de définir des conditions objectives, une méthode de calcul et des limites applicables aux pénalités ou indemnités contractuelles.",
                "replacement": "En cas de retard injustifié imputable à la partie défaillante, une pénalité contractuelle peut s'appliquer selon une méthode de calcul prédéfinie.",
                "clause_status": "Absente ou non clairement identifiée",
            },
            "PAYMENT_MISSING": {
                "title": "Modalités de paiement",
                "original_text": "Clause analysée : absence de modalités de paiement clairement identifiées.",
                "issue": "Aucune modalité de paiement clairement identifiée n'a été trouvée.",
                "explanation": "Le contrat devrait établir le mécanisme, les délais et les conditions de paiement applicables au prix contractuel.",
                "recommendation": "Préciser les délais de paiement, les conditions de facturation, le mode de paiement et les conséquences d'un retard de paiement.",
                "replacement": "Les factures seront payées dans le délai convenu à compter de la date de réception, conformément aux conditions contractuelles prévues aux présentes.",
                "clause_status": "Absente ou non clairement identifiée",
            },
            "PAYMENT_VAGUE": {
                "title": "Modalités de paiement",
                "issue": "La clause de paiement ne définit pas clairement les délais ou conditions de paiement applicables.",
                "explanation": "Une clause de paiement insuffisamment précise peut créer un désaccord sur le moment et les modalités d'exigibilité du paiement.",
                "recommendation": "Préciser le délai de paiement, les conditions de facturation et le mode de paiement.",
                "replacement": "Le paiement sera effectué dans le délai convenu suivant réception de la facture correspondante, conformément au mode de paiement précisé dans le présent contrat.",
                "clause_status": "Présente mais insuffisamment précise",
            },
            "DISPUTE_MISSING": {
                "title": "Règlement des différends / Juridiction",
                "original_text": "Clause analysée : absence de disposition clairement identifiée relative au règlement des différends ou à la juridiction compétente.",
                "issue": "Aucune disposition clairement identifiée relative au règlement des différends ou à la juridiction compétente n'a été trouvée.",
                "explanation": "Le contrat n'indique pas clairement comment les différends doivent être résolus ni quelle autorité est compétente.",
                "recommendation": "Préciser le mécanisme de règlement des différends applicable et la juridiction compétente.",
                "replacement": "Tout différend résultant de l'interprétation ou de l'exécution du présent contrat sera soumis à la juridiction compétente convenue par les parties, sous réserve du droit applicable.",
                "clause_status": "Absente ou non clairement identifiée",
            },
            "LIABILITY_MISSING": {
                "title": "Responsabilité",
                "original_text": "Clause analysée : absence de disposition clairement identifiée relative à la responsabilité.",
                "issue": "Aucune disposition contractuelle claire relative à la responsabilité n'a été identifiée.",
                "explanation": "Le contrat n'attribue pas clairement la responsabilité contractuelle en cas de dommage, de manquement ou d'inexécution.",
                "recommendation": "Clarifier les responsabilités de chaque partie et les conditions régissant la responsabilité contractuelle.",
                "replacement": "Chaque partie est responsable des dommages résultant directement de son manquement avéré aux obligations contractuelles qui lui sont expressément assignées.",
                "clause_status": "Absente ou non clairement identifiée",
            },
            "PARTIES_MISSING": {
                "title": "Parties contractantes",
                "original_text": "Clause analysée : les parties contractantes n'ont pas pu être identifiées avec certitude à partir du texte disponible.",
                "issue": "Les parties contractantes n'ont pas pu être identifiées avec certitude.",
                "explanation": "Le texte disponible ne permet pas d'identifier de manière suffisamment claire les entités ou personnes signataires du contrat.",
                "recommendation": "Identifier clairement chaque partie contractante par sa dénomination sociale, sa forme juridique et les éléments d'identification pertinents.",
                "replacement": "Entre [Dénomination sociale complète de la Partie 1], dûment identifiée et représentée par son représentant habilité, et [Dénomination sociale complète de la Partie 2], dûment identifiée et représentée par son représentant habilité.",
                "clause_status": "Absentes ou non clairement identifiées",
            },
        },
        "report_ui": {
            "report_title": "LegalVerifyDZ - Rapport d'analyse de contrat",
            "generated": "Généré le",
            "contract": "Contrat",
            "type": "Type",
            "risk_level": "Niveau de risque",
            "confidence": "Confiance",
            "compliance_score": "Score de conformité",
            "findings_count": "Constats",
            "high": "élevé", "moderate": "modéré", "low": "faible",
            "executive_summary": "RÉSUMÉ EXÉCUTIF",
            "parties": "PARTIES",
            "amounts": "MONTANTS",
            "durations": "DURÉES",
            "observations": "OBSERVATIONS",
            "recommendations": "RECOMMANDATIONS",
            "detailed_findings": "CONSTATS DE RISQUE DÉTAILLÉS",
            "none": "Aucun",
            "not_identified": "Non identifié",
            "no_finding": "Aucun constat spécifique n'a été relevé pour ce contrat.",
            "finding_label": "Constat",
            "clause_status": "État de la clause",
            "na": "n/a",
            "original_clause": "Clause originale :",
            "clause_not_located": "(clause non localisée dans le document)",
            "problem": "Problème :",
            "not_specified": "(non précisé)",
            "why_it_matters": "Pourquoi c'est important :",
            "recommendation_label": "Recommandation :",
            "suggested_wording": "Formulation plus sûre suggérée :",
            "not_provided": "(non fournie)",
            "disclaimer": "AVERTISSEMENT : analyse automatisée. Elle ne remplace pas l'examen d'un avocat qualifié et n'engage aucune responsabilité juridique.",
            "csv_headers": ["#", "Titre", "Gravité", "État de la clause", "Texte original", "Problème", "Explication", "Recommandation", "Formulation suggérée"],
            "tab_summary": "🧠 Résumé", "tab_findings": "⚠️ Constats", "tab_data": "📑 Données extraites", "tab_export": "📥 Export",
            "compliance_metric": "Score de conformité", "risk_metric": "Risque", "confidence_metric": "Confiance", "findings_metric": "Constats",
            "no_high_risk": "aucun risque élevé", "n_high": "{n} élevé(s)",
            "health_progress": "Santé du contrat · {score}%",
            "high_risk_warning": "{n} constat(s) à risque élevé. À examiner avant signature.",
            "moderate_warning": "{n} constat(s) modéré(s) nécessitant une clarification.",
            "no_risk_success": "Aucun constat élevé ou modéré n'a été détecté.",
            "priority_actions": "✅ Actions prioritaires",
            "no_finding_info": "Aucun constat détaillé n'a été produit pour ce contrat.",
            "severity_filter": "Gravité",
            "search_findings": "Rechercher dans les constats",
            "shown_of_total": "{shown} sur {total} constat(s) affiché(s).",
            "clause_not_located_caption": "Clause non localisée dans le document.",
            "problem_label": "Problème",
            "why_it_matters_label": "Pourquoi c'est important",
            "recommendation_bold": "Recommandation",
            "suggested_wording_bold": "Formulation plus sûre suggérée",
            "parties_header": "👥 Parties", "amounts_header": "💰 Montants", "durations_header": "⏱️ Durées",
            "observations_header": "🔍 Observations",
            "no_observation": "Aucune observation enregistrée.",
            "text_report_btn": "📄 Rapport texte", "csv_btn": "📊 Constats (CSV)", "json_btn": "🧩 JSON (API)",
            "preview_report": "Aperçu du rapport texte",
            "footer_disclaimer": "⚖️ Analyse automatisée — elle ne remplace pas l'examen d'un avocat qualifié.",
            "shape_warning": "Le résultat de l'analyse n'a pas la forme attendue à 11 valeurs ; certaines sections peuvent être incomplètes.",
            "guest_title": "📌 Analyse invité",
            "guest_info": "Ceci est une analyse invité limitée. Créez un compte pour débloquer le rapport complet, l'historique des analyses et les fonctionnalités avancées.",
            "contract_type_header": "📄 Type de contrat",
            "risk_level_header": "⚠️ Niveau de risque",
            "confidence_header": "📊 Score de confiance",
            "summary_header": "🧠 Résumé",
            "key_findings_header": "🔎 Constats clés",
            "parties_detected": "👥 Parties contractantes détectées.",
            "parties_not_detected": "👥 Les parties n'ont pas pu être extraites avec certitude.",
            "amount_detected": "💰 Montant du contrat détecté.",
            "amount_not_detected": "💰 Montant du contrat non détecté avec certitude.",
            "duration_detected": "⏳ Durée du contrat détectée.",
            "duration_not_detected": "⏳ Durée du contrat non détectée avec certitude.",
            "guest_warning": "🔐 Le mode invité ne fournit qu'un résultat limité. Créez un compte pour accéder au rapport d'analyse complet.",
            "history_title": "🗂️ Historique des analyses",
            "history_empty": "Aucune analyse enregistrée pour le moment. Les analyses effectuées en étant connecté apparaîtront ici.",
            "history_date": "Date", "history_view": "Voir le rapport", "history_delete": "Supprimer",
            "history_deleted": "Analyse supprimée.",
            "history_back": "⬅️ Retour à l'historique",
            "lawyer_section_title": "🤝 Étape suivante",
            "lawyer_question": "Ce rapport est une analyse automatisée. Comment souhaitez-vous procéder ?",
            "lawyer_option_ai_only": "✅ Je me contente de cette analyse",
            "lawyer_option_request": "⚖️ Demander l'avis d'un avocat",
            "lawyer_ai_only_ack": "Noté. Rappel : ceci reste une analyse automatisée, pas un avis juridique.",
            "lawyer_request_success": "Votre demande a été enregistrée. Nous vous contacterons dès qu'un avocat partenaire sera disponible.",
            "lawyer_no_partners_yet": "Remarque : la plateforme n'a pas encore contractualisé avec un avocat partenaire. Votre demande est mise en file d'attente et vous serez contacté dès que possible.",
            "ocr_used_note": "📷 Ce document semble être un fichier scanné. Le texte a été extrait par OCR (reconnaissance optique de caractères) -- merci de vérifier le texte extrait ci-dessous, l'OCR pouvant parfois mal lire certains caractères.",
        },
    },
    "العربية": {
        "levels": {"Low": "منخفض", "Moderate": "متوسط", "High": "مرتفع"},
        "contract_types": {
            "Service / Maintenance Contract": "عقد خدمة / صيانة",
            "Sale / Purchase Contract": "عقد بيع / شراء",
            "Lease / Rental Contract": "عقد إيجار / كراء",
            "Unknown": "غير محدَّد",
        },
        "observations": {
            "termination": "تم تحديد بند إنهاء ومراجعته من حيث الضمانات التعاقدية.",
            "liability": "تم تحديد بند يتعلق بالمسؤولية.",
            "dispute": "تم تحديد بند يتعلق بتسوية النزاعات / الاختصاص القضائي.",
            "payment": "تم تحديد بنود متعلقة بالدفع.",
            "obligation": "تم تحديد التزامات تعاقدية.",
            "parties": "تم تحديد أطراف العقد من نص العقد.",
        },
        "summary": {
            "type_known": "تم تصنيف العقد على أنه {type}.",
            "type_unknown": "تعذّر تحديد نوع العقد بثقة كافية.",
            "parties_known": "أطراف العقد المحدَّدة هي {parties}.",
            "parties_unknown": "تعذّر تحديد أطراف العقد بثقة كافية.",
            "amounts": "تم تحديد مبلغ تعاقدي قدره {amounts}.",
            "durations": "المدة المحدَّدة هي {durations}.",
            "risk_low": "يشير التحليل إلى مستوى منخفض نسبيًا من المخاطر التعاقدية المحدَّدة، استنادًا إلى البنود والمعلومات التي أمكن استخراجها.",
            "risk_moderate": "حدّد التحليل عدة نقاط تعاقدية قد تحتاج إلى توضيح أو ضمانات أقوى.",
            "risk_high": "حدّد التحليل مخاطر تعاقدية مهمة ينبغي مراجعتها قبل الاعتماد على هذا الاتفاق.",
        },
        "findings": {
            "TERMINATION_HIGH": {
                "title": "الإنهاء",
                "issue": "يسمح بند الإنهاء بالإنهاء دون شروط أو ضمانات محدَّدة بشكل كافٍ.",
                "explanation": "قد تؤدي آلية الإنهاء غير المقيَّدة إلى غموض بشأن مهلة الإشعار والأسباب المشروعة والنتائج التعاقدية للإنهاء.",
                "recommendation": "تحديد أسباب الإنهاء ومهلة الإشعار ومتطلبات الإخطار الرسمي ونتائج الإنهاء.",
                "replacement": "يجوز لأي طرف إنهاء العقد لسبب تعاقدي محدَّد بإشعار كتابي، مع مراعاة مهلة إشعار معقولة وتسوية الالتزامات الناشئة قبل تاريخ نفاذ الإنهاء.",
                "clause_status": "موجود لكن غير مضمون بشكل كافٍ",
            },
            "TERMINATION_MISSING": {
                "title": "الإنهاء",
                "original_text": "البند قيد التحليل: غياب آلية إنهاء محدَّدة بوضوح.",
                "issue": "لم يتم العثور على آلية تعاقدية واضحة لإنهاء العقد.",
                "explanation": "لا يحدّد العقد بوضوح كيفية إنهاء العلاقة التعاقدية ولا الشروط التي يتم بموجبها ذلك.",
                "recommendation": "تحديد الأسباب والإجراء ومهلة الإشعار ونتائج الإنهاء.",
                "replacement": "يجوز لأي طرف إنهاء العقد في الحالات المنصوص عليها فيه بإشعار كتابي ومع مراعاة مهلة الإشعار المعمول بها.",
                "clause_status": "غائب أو غير محدَّد بوضوح",
            },
            "PENALTY_EXCLUDED": {
                "title": "الغرامة التعاقدية",
                "issue": "لا يوجد بند يقرّ آلية غرامة أو تعويض في حالة التأخير أو عدم التنفيذ.",
                "explanation": "يستبعد البند صراحةً أو لا ينشئ آلية مالية تعالج التأخير أو بعض أشكال عدم التنفيذ.",
                "recommendation": "تحديد شروط موضوعية وطريقة حساب وحدود قابلة للتطبيق والظروف التي تستوجب الغرامات أو التعويضات التعاقدية.",
                "replacement": "في حالة التأخير غير المبرَّر المنسوب إلى الطرف المخل، تُطبَّق غرامة تعاقدية وفق طريقة حساب محدَّدة مسبقًا وفي حدود ما يتفق عليه الطرفان.",
                "clause_status": "موجود لكنه يستبعد آلية الغرامة",
            },
            "PENALTY_MISSING": {
                "title": "الغرامة التعاقدية",
                "original_text": "البند قيد التحليل: غياب آلية واضحة للغرامة أو التعويض.",
                "issue": "لم يتم تحديد آلية تعاقدية واضحة للغرامة أو التعويض.",
                "explanation": "لا يحدّد العقد بوضوح النتائج المالية للتأخير أو لأشكال معينة من عدم التنفيذ.",
                "recommendation": "النظر في تحديد شروط موضوعية وطريقة حساب وحدود قابلة للتطبيق للغرامات أو التعويضات التعاقدية.",
                "replacement": "في حالة التأخير غير المبرَّر المنسوب إلى الطرف المخل، يجوز تطبيق غرامة تعاقدية وفق طريقة حساب محدَّدة مسبقًا.",
                "clause_status": "غائب أو غير محدَّد بوضوح",
            },
            "PAYMENT_MISSING": {
                "title": "شروط الدفع",
                "original_text": "البند قيد التحليل: غياب شروط دفع محدَّدة بوضوح.",
                "issue": "لم يتم العثور على شروط دفع محدَّدة بوضوح.",
                "explanation": "ينبغي أن يحدّد العقد آلية الدفع وتوقيته والشروط المطبَّقة على الثمن التعاقدي.",
                "recommendation": "تحديد آجال الدفع وشروط الفوترة وطريقة الدفع ونتائج التأخر في الدفع.",
                "replacement": "تُدفَع الفواتير خلال المدة المتفق عليها ابتداءً من تاريخ الاستلام، مع مراعاة الشروط التعاقدية المنصوص عليها في هذا العقد.",
                "clause_status": "غائبة أو غير محدَّدة بوضوح",
            },
            "PAYMENT_VAGUE": {
                "title": "شروط الدفع",
                "issue": "لا يحدّد بند الدفع بوضوح التوقيت أو الشروط المطبَّقة على الدفع.",
                "explanation": "قد يؤدي بند الدفع غير الدقيق بشكل كافٍ إلى خلاف بشأن موعد وكيفية استحقاق الدفع.",
                "recommendation": "تحديد أجل الدفع وشروط الفوترة وطريقة الدفع.",
                "replacement": "يتم الدفع خلال المدة المتفق عليها بعد استلام الفاتورة المعنية، وفقًا لطريقة الدفع المحدَّدة في هذا العقد.",
                "clause_status": "موجود لكن غير دقيق بشكل كافٍ",
            },
            "DISPUTE_MISSING": {
                "title": "تسوية النزاعات / الاختصاص القضائي",
                "original_text": "البند قيد التحليل: غياب بند محدَّد بوضوح لتسوية النزاعات أو الاختصاص القضائي.",
                "issue": "لم يتم العثور على بند محدَّد بوضوح لتسوية النزاعات أو الاختصاص القضائي.",
                "explanation": "لا يبيّن العقد بوضوح كيفية تسوية النزاعات ولا الجهة المختصة بالنظر فيها.",
                "recommendation": "تحديد آلية تسوية النزاعات المعمول بها والجهة القضائية المختصة.",
                "replacement": "يُعرَض أي نزاع ناشئ عن تفسير هذا العقد أو تنفيذه على الجهة القضائية المختصة المتفق عليها بين الطرفين، مع مراعاة القانون المعمول به.",
                "clause_status": "غائب أو غير محدَّد بوضوح",
            },
            "LIABILITY_MISSING": {
                "title": "المسؤولية",
                "original_text": "البند قيد التحليل: غياب بند محدَّد بوضوح يتعلق بالمسؤولية.",
                "issue": "لم يتم تحديد بند تعاقدي واضح يتعلق بالمسؤولية.",
                "explanation": "لا يحدّد العقد بوضوح توزيع المسؤولية التعاقدية عن الضرر أو الإخلال أو عدم التنفيذ.",
                "recommendation": "توضيح مسؤوليات كل طرف والشروط التي تحكم المسؤولية التعاقدية.",
                "replacement": "يتحمّل كل طرف المسؤولية عن الضرر الناتج مباشرة عن إخلاله الثابت بالالتزامات التعاقدية المسندة إليه صراحةً.",
                "clause_status": "غائب أو غير محدَّد بوضوح",
            },
            "PARTIES_MISSING": {
                "title": "أطراف العقد",
                "original_text": "البند قيد التحليل: تعذّر تحديد أطراف العقد بثقة كافية من النص المتاح.",
                "issue": "تعذّر تحديد أطراف العقد بثقة كافية.",
                "explanation": "لا يوفّر النص المتاح تحديدًا واضحًا بشكل كافٍ للكيانات أو الأشخاص الذين يبرمون العقد.",
                "recommendation": "تحديد كل طرف من أطراف العقد بوضوح باسمه القانوني وشكله القانوني وبياناته التعريفية ذات الصلة.",
                "replacement": "بين [الاسم القانوني الكامل للطرف الأول]، المحدَّد والمُمثَّل حسب الأصول بواسطة ممثله المفوَّض، و[الاسم القانوني الكامل للطرف الثاني]، المحدَّد والمُمثَّل حسب الأصول بواسطة ممثله المفوَّض.",
                "clause_status": "غائبة أو غير محدَّدة بوضوح",
            },
        },
        "report_ui": {
            "report_title": "LegalVerifyDZ - تقرير تحليل العقد",
            "generated": "تاريخ الإنشاء",
            "contract": "العقد",
            "type": "النوع",
            "risk_level": "مستوى المخاطر",
            "confidence": "الثقة",
            "compliance_score": "مؤشر الامتثال",
            "findings_count": "البنود",
            "high": "مرتفع", "moderate": "متوسط", "low": "منخفض",
            "executive_summary": "الملخّص التنفيذي",
            "parties": "الأطراف",
            "amounts": "المبالغ",
            "durations": "المدد",
            "observations": "الملاحظات",
            "recommendations": "التوصيات",
            "detailed_findings": "بنود المخاطر التفصيلية",
            "none": "لا يوجد",
            "not_identified": "غير محدَّد",
            "no_finding": "لم يُسجَّل أي بند خاص بهذا العقد.",
            "finding_label": "بند",
            "clause_status": "حالة البند",
            "na": "غير متاح",
            "original_clause": "البند الأصلي:",
            "clause_not_located": "(لم يتم تحديد موقع البند في المستند)",
            "problem": "المشكلة:",
            "not_specified": "(غير محدَّد)",
            "why_it_matters": "لماذا يهم:",
            "recommendation_label": "التوصية:",
            "suggested_wording": "الصياغة الأكثر أمانًا المقترحة:",
            "not_provided": "(غير متوفرة)",
            "disclaimer": "تنويه: تحليل آلي. لا يغني عن مراجعة محامٍ مختص ولا يترتب عنه أي مسؤولية قانونية.",
            "csv_headers": ["#", "العنوان", "الخطورة", "حالة البند", "النص الأصلي", "المشكلة", "الشرح", "التوصية", "الصياغة المقترحة"],
            "tab_summary": "🧠 الملخّص", "tab_findings": "⚠️ البنود", "tab_data": "📑 البيانات المستخرجة", "tab_export": "📥 التصدير",
            "compliance_metric": "مؤشر الامتثال", "risk_metric": "المخاطر", "confidence_metric": "الثقة", "findings_metric": "البنود",
            "no_high_risk": "لا مخاطر مرتفعة", "n_high": "{n} مرتفعة",
            "health_progress": "صحة العقد · {score}%",
            "high_risk_warning": "{n} بند(ود) عالي الخطورة. راجعها قبل التوقيع.",
            "moderate_warning": "{n} بند(ود) متوسط الخطورة يحتاج إلى توضيح.",
            "no_risk_success": "لم يُكتشف أي بند مرتفع أو متوسط الخطورة.",
            "priority_actions": "✅ إجراءات ذات أولوية",
            "no_finding_info": "لم يُنتج أي بند تفصيلي لهذا العقد.",
            "severity_filter": "الخطورة",
            "search_findings": "بحث في البنود",
            "shown_of_total": "{shown} من أصل {total} بند(ود) معروض.",
            "clause_not_located_caption": "لم يتم تحديد موقع البند في المستند.",
            "problem_label": "المشكلة",
            "why_it_matters_label": "لماذا يهم",
            "recommendation_bold": "التوصية",
            "suggested_wording_bold": "الصياغة الأكثر أمانًا المقترحة",
            "parties_header": "👥 الأطراف", "amounts_header": "💰 المبالغ", "durations_header": "⏱️ المدد",
            "observations_header": "🔍 الملاحظات",
            "no_observation": "لا توجد ملاحظات مسجَّلة.",
            "text_report_btn": "📄 تقرير نصي", "csv_btn": "📊 البنود (CSV)", "json_btn": "🧩 JSON (واجهة برمجية)",
            "preview_report": "معاينة التقرير النصي",
            "footer_disclaimer": "⚖️ تحليل آلي — لا يغني عن مراجعة محامٍ مختص.",
            "shape_warning": "نتيجة التحليل لا تطابق الشكل المتوقَّع من 11 قيمة؛ قد تكون بعض الأقسام ناقصة.",
            "guest_title": "📌 تحليل الزائر",
            "guest_info": "هذا تحليل محدود لوضع الزائر. أنشئ حسابًا لفتح التقرير الكامل وسجلّ التحليلات والميزات المتقدمة.",
            "contract_type_header": "📄 نوع العقد",
            "risk_level_header": "⚠️ مستوى المخاطر",
            "confidence_header": "📊 درجة الثقة",
            "summary_header": "🧠 الملخّص",
            "key_findings_header": "🔎 أبرز النتائج",
            "parties_detected": "👥 تم تحديد أطراف العقد.",
            "parties_not_detected": "👥 تعذّر استخراج الأطراف بثقة كافية.",
            "amount_detected": "💰 تم تحديد قيمة العقد.",
            "amount_not_detected": "💰 تعذّر تحديد قيمة العقد بثقة كافية.",
            "duration_detected": "⏳ تم تحديد مدة العقد.",
            "duration_not_detected": "⏳ تعذّر تحديد مدة العقد بثقة كافية.",
            "guest_warning": "🔐 يوفّر وضع الزائر نتيجة محدودة فقط. أنشئ حسابًا للوصول إلى تقرير التحليل الكامل.",
            "history_title": "🗂️ سجلّ التحليلات",
            "history_empty": "لا توجد تحليلات محفوظة بعد. ستظهر هنا التحليلات التي تجريها وأنت مسجَّل الدخول.",
            "history_date": "التاريخ", "history_view": "عرض التقرير", "history_delete": "حذف",
            "history_deleted": "تم حذف التحليل.",
            "history_back": "⬅️ العودة إلى السجلّ",
            "lawyer_section_title": "🤝 الخطوة التالية",
            "lawyer_question": "هذا التقرير تحليل آلي. كيف تودّ المتابعة؟",
            "lawyer_option_ai_only": "✅ سأكتفي بهذا التحليل",
            "lawyer_option_request": "⚖️ طلب مراجعة محامٍ",
            "lawyer_ai_only_ack": "تم التسجيل. تذكّر أن هذا يبقى تحليلًا آليًا وليس استشارة قانونية.",
            "lawyer_request_success": "تم تسجيل طلبك. سنتواصل معك بمجرد توفّر محامٍ شريك.",
            "lawyer_no_partners_yet": "ملاحظة: لم تتعاقد المنصة بعد مع أي محامٍ شريك. طلبك مُدرَج في قائمة الانتظار وسيتم التواصل معك حالما يتوفر محامٍ.",
            "ocr_used_note": "📷 يبدو أن هذا المستند ملف ممسوح ضوئيًا. تم استخراج النص باستخدام التعرف الضوئي على الحروف (OCR) — يُرجى مراجعة النص المستخرج أدناه، فقد يخطئ التعرف الضوئي أحيانًا في قراءة بعض الأحرف.",
        },
    },
}


def _tr(lang_key):
    """Safe lookup: unknown/None language falls back to English."""
    return TR.get(lang_key, TR["English"])




# ==========================================
# USER DATABASE - SQLite  (replaces the Excel-based store)
# ==========================================
# Why this changed:
#   - users.xlsx is a single file with no locking: two users signing up
#     or logging in at the same moment can corrupt it or silently lose
#     one of the writes (openpyxl loads the whole file, then overwrites
#     it wholesale on save).
#   - SQLite (Python's stdlib `sqlite3`, no extra install) handles
#     concurrent access safely and scales far better as the user base
#     grows, while keeping the exact same fields the rest of the app
#     already expects (User ID, Name, Email, Company, Plan, Status...).
#
# Password hashing changed from plain SHA-256 (fast, brute-forceable,
# no salt -> identical passwords produce identical hashes) to bcrypt
# (salted automatically, deliberately slow, industry standard for
# login systems). Existing SHA-256 hashes are NOT abandoned: they are
# transparently upgraded to bcrypt the next time each user logs in
# successfully, so no one is locked out.
#
# Requires: pip install bcrypt --break-system-packages
# ==========================================

import sqlite3

try:
    import bcrypt
    _BCRYPT_AVAILABLE = True
except ImportError:
    _BCRYPT_AVAILABLE = False

DB_FILE = Path("legalverify.db")


def hash_password(password):
    """New hashes: bcrypt, salted, ~250ms to compute (by design)."""

    if not _BCRYPT_AVAILABLE:
        # Fallback so the app still runs if bcrypt isn't installed yet;
        # a clear warning is better than a silent security downgrade.
        st.warning(
            "⚠️ bcrypt is not installed — run `pip install bcrypt`. "
            "Falling back to a weaker hash for now."
        )
        return "sha256$" + hashlib.sha256(password.encode("utf-8")).hexdigest()

    salt = bcrypt.gensalt()
    return "bcrypt$" + bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def _verify_password(password, stored_hash):
    """
    Returns True/False. Understands both the new bcrypt$ format and the
    legacy plain SHA-256 hashes written by earlier versions of the app.
    """

    stored_hash = str(stored_hash or "")

    if stored_hash.startswith("bcrypt$"):
        if not _BCRYPT_AVAILABLE:
            return False
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"),
                stored_hash[len("bcrypt$"):].encode("utf-8")
            )
        except ValueError:
            return False

    if stored_hash.startswith("sha256$"):
        legacy = stored_hash[len("sha256$"):]
    else:
        # Hashes created before this change had no prefix at all.
        legacy = stored_hash

    return hashlib.sha256(password.encode("utf-8")).hexdigest() == legacy


def ensure_users_file():
    connection = sqlite3.connect(DB_FILE)

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id        TEXT PRIMARY KEY,
            name           TEXT NOT NULL,
            email          TEXT NOT NULL UNIQUE,
            company        TEXT,
            password_hash  TEXT NOT NULL,
            plan           TEXT DEFAULT 'Free',
            status         TEXT DEFAULT 'Active',
            created_at     TEXT,
            last_login     TEXT
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS analyses (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         TEXT NOT NULL,
            filename        TEXT,
            contract_type   TEXT,
            risk_level      TEXT,
            risk_score      INTEGER,
            confidence      INTEGER,
            compliance_score INTEGER,
            summary         TEXT,
            report_json     TEXT NOT NULL,
            created_at      TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        """
    )

    # Lead-capture table: no lawyer is under contract with the platform
    # yet (see request_lawyer_review()), so this simply records who
    # asked for a human review, on which contract, so the platform can
    # follow up once partner lawyers are onboarded.
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS lawyer_requests (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         TEXT NOT NULL,
            analysis_id     INTEGER,
            filename        TEXT,
            contract_type   TEXT,
            risk_level      TEXT,
            status          TEXT DEFAULT 'pending',
            created_at      TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        """
    )

    connection.commit()
    connection.close()


def request_lawyer_review(user_id, analysis_id, filename, contract_type, risk_level):
    """
    Record that a user asked for a human lawyer to review their
    contract. No partner lawyer is under contract with the platform
    yet, so this does not route to anyone in real time -- it queues a
    lead that becomes actionable the moment partner lawyers are
    onboarded (see get_pending_lawyer_requests()).
    """

    ensure_users_file()

    connection = sqlite3.connect(DB_FILE)

    connection.execute(
        """
        INSERT INTO lawyer_requests (
            user_id, analysis_id, filename, contract_type, risk_level,
            status, created_at
        ) VALUES (?, ?, ?, ?, ?, 'pending', ?)
        """,
        (
            user_id,
            analysis_id,
            str(filename),
            contract_type,
            risk_level,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
    )
    connection.commit()
    connection.close()


def has_pending_lawyer_request(user_id, analysis_id):
    """Avoid logging the same request twice if the user reopens the
    same report and clicks the button again."""

    if analysis_id is None:
        return False

    ensure_users_file()

    connection = sqlite3.connect(DB_FILE)

    row = connection.execute(
        "SELECT 1 FROM lawyer_requests WHERE user_id = ? AND analysis_id = ?",
        (user_id, analysis_id)
    ).fetchone()

    connection.close()

    return row is not None


def get_pending_lawyer_requests(limit=100):
    """For future admin/ops use: the queue of users waiting for a
    lawyer, to hand to partner lawyers once the platform contracts
    with any."""

    ensure_users_file()

    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row

    rows = connection.execute(
        "SELECT * FROM lawyer_requests WHERE status = 'pending' "
        "ORDER BY id DESC LIMIT ?",
        (limit,)
    ).fetchall()

    connection.close()

    return [dict(row) for row in rows]


def save_analysis(user_id, filename, result, findings):
    """
    Store one completed analysis for a registered user so it shows up
    in their History page later. `report_json` keeps the full result +
    findings so the report can be fully reconstructed and re-displayed,
    not just summarized.
    """

    ensure_users_file()

    data = unpack_result(result)
    counts = severity_counts(findings)
    score = compliance_score(data["risk"], data["confidence"], counts)

    payload = _json.dumps(
        {"result": list(result), "findings": normalize_findings(findings)},
        ensure_ascii=False
    )

    connection = sqlite3.connect(DB_FILE)

    connection.execute(
        """
        INSERT INTO analyses (
            user_id, filename, contract_type, risk_level, risk_score,
            confidence, compliance_score, summary, report_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            str(filename),
            data["contract_type"],
            data["lvl"],
            data["risk"],
            data["confidence"],
            score,
            data["summary"],
            payload,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
    )
    new_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    connection.commit()
    connection.close()

    return new_id


def get_user_analyses(user_id, limit=50):
    ensure_users_file()

    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row

    rows = connection.execute(
        """
        SELECT id, filename, contract_type, risk_level, risk_score,
               confidence, compliance_score, summary, report_json, created_at
        FROM analyses
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (user_id, limit)
    ).fetchall()

    connection.close()

    return [dict(row) for row in rows]


def delete_analysis(analysis_id, user_id):
    """Delete one history row, scoped to its owner so a user can only
    delete their own analyses (never someone else's by guessing an id)."""

    connection = sqlite3.connect(DB_FILE)

    connection.execute(
        "DELETE FROM analyses WHERE id = ? AND user_id = ?",
        (analysis_id, user_id)
    )
    connection.commit()
    connection.close()


def get_users():
    ensure_users_file()

    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row

    rows = connection.execute(
        "SELECT * FROM users ORDER BY created_at"
    ).fetchall()

    connection.close()

    # Same key names the rest of the app already relies on.
    return [
        {
            "User ID": row["user_id"],
            "Name": row["name"],
            "Email": row["email"],
            "Company": row["company"],
            "Password Hash": row["password_hash"],
            "Plan": row["plan"],
            "Status": row["status"],
            "Created At": row["created_at"],
            "Last Login": row["last_login"],
        }
        for row in rows
    ]


def email_exists(email):
    email = email.strip().lower()

    ensure_users_file()

    connection = sqlite3.connect(DB_FILE)

    row = connection.execute(
        "SELECT 1 FROM users WHERE lower(email) = ?",
        (email,)
    ).fetchone()

    connection.close()

    return row is not None


def create_user(name, email, company, password):
    ensure_users_file()

    if email_exists(email):
        return False, "This email is already registered."

    connection = sqlite3.connect(DB_FILE)

    user_count = connection.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    user_id = "LV-{:04d}".format(user_count + 1)

    try:
        connection.execute(
            """
            INSERT INTO users (
                user_id, name, email, company, password_hash,
                plan, status, created_at, last_login
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                name.strip(),
                email.strip().lower(),
                company.strip(),
                hash_password(password),
                "Free",
                "Active",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "",
            )
        )
        connection.commit()
    except sqlite3.IntegrityError:
        # Two signups for the same email arrived at the same instant.
        connection.close()
        return False, "This email is already registered."

    connection.close()

    return True, "Account created successfully."


def authenticate_user(email, password):
    email = email.strip().lower()

    ensure_users_file()

    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row

    row = connection.execute(
        "SELECT * FROM users WHERE lower(email) = ?",
        (email,)
    ).fetchone()

    if row is None:
        connection.close()
        return None

    if str(row["status"]) != "Active":
        connection.close()
        return None

    if not _verify_password(password, row["password_hash"]):
        connection.close()
        return None

    # Transparent upgrade: a legacy SHA-256 hash becomes bcrypt now that
    # we know the plaintext password was correct.
    new_hash = row["password_hash"]

    if not str(row["password_hash"]).startswith("bcrypt$") and _BCRYPT_AVAILABLE:
        new_hash = hash_password(password)

    connection.execute(
        "UPDATE users SET last_login = ?, password_hash = ? WHERE user_id = ?",
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            new_hash,
            row["user_id"],
        )
    )
    connection.commit()
    connection.close()

    return {
        "User ID": row["user_id"],
        "Name": row["name"],
        "Email": row["email"],
        "Company": row["company"],
        "Plan": row["plan"] or "Free",
        "Status": row["status"] or "Active",
    }

# ==========================================
# AUTHENTICATION SCREEN
# ==========================================
def show_auth_screen():
    st.markdown(
        """
    <div style='text-align:center; padding:35px 10px 10px;'>
        {logo}
        <h1 style='color:#4F8BFF; margin-top:8px;'>LegalVerifyDZ</h1>
        <h3>AI-Powered Contract Intelligence Platform</h3>
        <p style='color:#888;'>
        Create an account or continue as a guest.
        </p>
    </div>
    """.format(logo=logo_html(72)),
        unsafe_allow_html=True
    )

    tab_login, tab_signup, tab_guest = st.tabs([
        "🔐 Login",
        "📝 Create Account",
        "👤 Guest"
    ])

    with tab_login:
        st.markdown("### 🔐 Login")

        email = st.text_input(
            "Email",
            key="auth_login_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="auth_login_password"
        )

        if st.button(
            "Login",
            key="login_button",
            use_container_width=True
        ):
            if not email or not password:
                st.warning("Please enter your email and password.")
            else:
                user = authenticate_user(email, password)

                if user:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.session_state.auth_screen = False
                    st.success("Login successful.")
                    st.rerun()
                else:
                    st.error(
                        "Invalid email, password, or inactive account."
                    )

    with tab_signup:
        st.markdown("### 📝 Create Account")

        name = st.text_input(
            "Full Name",
            key="auth_signup_name"
        )

        email = st.text_input(
            "Email",
            key="auth_signup_email"
        )

        company = st.text_input(
            "Company",
            key="auth_signup_company"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="auth_signup_password"
        )

        password2 = st.text_input(
            "Confirm Password",
            type="password",
            key="auth_signup_password2"
        )

        if st.button(
            "Create Account",
            key="signup_button",
            use_container_width=True
        ):
            if not name or not email or not password:
                st.warning(
                    "Name, email and password are required."
                )
            elif password != password2:
                st.error("Passwords do not match.")
            elif len(password) < 6:
                st.error(
                    "Password must contain at least 6 characters."
                )
            elif email_exists(email):
                st.error(
                    "This email is already registered."
                )
            else:
                ok, message = create_user(
                    name,
                    email,
                    company,
                    password
                )

                if ok:
                    st.success(message)
                    st.info(
                        "Your account has been created. "
                        "Please use the Login tab."
                    )
                else:
                    st.error(message)

    with tab_guest:
        st.markdown("### 👤 Continue as Guest")

        st.info("""
You can test LegalVerifyDZ without creating an account.

Guest access:
- One contract analysis only
- Limited analysis results
- No analysis history
- No saved contracts
- No advanced report
""")

        if st.session_state.guest_used:
            st.warning(
                "Your guest analysis has already been used."
            )
        else:
            if st.button(
                "Continue as Guest",
                key="guest_button",
                use_container_width=True
            ):
                st.session_state.authenticated = False
                st.session_state.user = None
                st.session_state.auth_screen = False
                st.rerun()


# ==========================================
# FILE EXTRACTION
# ==========================================
def extract_pdf(f):
    text = ""

    try:
        f.seek(0)

        with pdfplumber.open(f) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()

                if page_text:
                    text += page_text + "\n"

        if text.strip():
            return text, None, False

        # No text layer found -- likely a scanned/image-only PDF.
        # Fall back to OCR (see ocr.py) before giving up entirely.
        ocr_text, ocr_error = ocr.ocr_pdf(f)

        if ocr_text:
            return ocr_text, None, True

        return None, ocr_error or "Empty or scanned PDF (no readable text).", False

    except Exception:
        return None, "Invalid or corrupted PDF.", False


def extract_docx(f):
    try:
        f.seek(0)

        d = docx.Document(f)

        text = "\n".join(
            paragraph.text
            for paragraph in d.paragraphs
        )

        if not text.strip():
            return None, "Empty Word file.", False

        return text, None, False

    except Exception:
        return None, "Invalid Word file.", False


# ==========================================
# CONTRACT ANALYSIS - MULTILINGUAL ENGINE
# ==========================================
def analyse(text, report_lang=None):

    import re

    # Templates for the CONTENT this function writes (finding text,
    # observations, summary sentences), in the language the user chose
    # in the sidebar -- independent of the contract's own language,
    # which is detected further below as `detected_language`.
    _rl = _tr(report_lang)
    fx = _rl["findings"]
    ox = _rl["observations"]
    sx = _rl["summary"]

    # ---------------------------------------------------------------
    # Sections 1-22 of the original monolithic analyse() now live in
    # extractors.py (text extraction), rules.py (finding construction)
    # and scoring.py (risk/confidence scoring) -- see those files for
    # the actual logic. This keeps analyse() itself as a short, readable
    # orchestrator instead of a ~1500-line function.
    # ---------------------------------------------------------------

    ctx = extractors.extract_all(text, report_lang)

    findings, obs, recommendations = rules.build_findings(ctx, fx, ox)

    risk, lvl, cls, confidence = scoring.compute_score(ctx, findings)

    contract_type = ctx["contract_type"]
    parties = ctx["parties"]
    amounts = ctx["amounts"]
    durations = ctx["durations"]
    detected_language = ctx["detected_language"]

    # =========================================================
    # 23. EXECUTIVE SUMMARY
    #    Canonical English internal text.
    #    The renderer should translate it according to report_lang.
    # =========================================================

    # Localized display name for the contract type. `contract_type`
    # itself stays canonical/English above (it drove the `!= "Unknown"`
    # checks in this function) -- only the text shown to the user changes.
    contract_type_display = _rl["contract_types"].get(
        contract_type, contract_type
    )

    summary_parts = []

    if contract_type != "Unknown":

        summary_parts.append(
            sx["type_known"].format(type=contract_type_display)
        )
    else:

        summary_parts.append(sx["type_unknown"])

    if parties:

        summary_parts.append(
            sx["parties_known"].format(
                parties=" / ".join(parties[:2])
            )
        )

    else:

        summary_parts.append(sx["parties_unknown"])

    if amounts:

        summary_parts.append(
            sx["amounts"].format(amounts=", ".join(amounts))
        )

    if durations:

        summary_parts.append(
            sx["durations"].format(durations=", ".join(durations))
        )

    if risk < 30:
        summary_parts.append(sx["risk_low"])
    elif risk < 60:
        summary_parts.append(sx["risk_moderate"])
    else:
        summary_parts.append(sx["risk_high"])

    summary = " ".join(
        summary_parts
    )

    # =========================================================
    # 24. SAVE ANALYSIS DATA IN SESSION
    # =========================================================

    try:

        st.session_state["risk_findings"] = findings
        st.session_state["detected_language"] = detected_language
        st.session_state["analysis_confidence"] = confidence

    except Exception:
        pass

    # =========================================================
    # 25. FINAL RETURN
    #
    # IMPORTANT:
    # Keep exactly the 11-value structure used by the application.
    # =========================================================

    return (
        _rl["levels"].get(lvl, lvl),
        risk,
        obs,
        cls,
        amounts,
        durations,
        recommendations,
        parties,
        contract_type_display,
        summary,
        confidence
    )
# ==========================================
# FULL REGISTERED REPORT  (rewritten - clean version)
# ==========================================
# Fixes applied here:
#   1. The whole body is correctly indented inside the function
#      (the old version leaked to module level after the tuple unpacking).
#   2. report_text / risk_findings are no longer trapped inside an `else`.
#   3. Findings keys are normalized: analyse() writes
#      title / severity / original_text / replacement, while the old UI
#      read clause_type / risk_level / suggested_replacement.
#   4. The duplicated "AI Insights" block is gone.
#   5. HTML injection is blocked with html.escape().
# ==========================================

import csv as _csv
import io as _io
import json as _json
import html as _html

SEVERITY_ORDER = {"High": 0, "Moderate": 1, "Low": 2}
SEVERITY_ICON = {"High": "🔴", "Moderate": "🟠", "Low": "🟢"}

RESULT_FIELDS = (
    "lvl", "risk", "obs", "cls", "amounts", "durations",
    "recs", "parties", "contract_type", "summary", "confidence",
)

# Accepted spellings for every canonical finding key.
KEY_ALIASES = {
    "title": ("title", "clause_type"),
    "severity": ("severity", "risk_level"),
    "original_text": ("original_text", "clause", "original_clause"),
    "issue": ("issue",),
    "explanation": ("explanation",),
    "recommendation": ("recommendation",),
    "replacement": ("replacement", "suggested_replacement"),
    "finding_type": ("finding_type",),
    "clause_status": ("clause_status",),
}


# ------------------------------------------------------------------
# Pure helpers (no Streamlit call inside -> easy to test)
# ------------------------------------------------------------------

def get_finding_severity(finding):
    """Return 'High' | 'Moderate' | 'Low' whatever the key or casing."""

    if not isinstance(finding, dict):
        return "Moderate"

    raw = ""

    for key in KEY_ALIASES["severity"]:
        if finding.get(key):
            raw = str(finding[key])
            break

    low = raw.strip().lower()

    if low.startswith("high") or low in {"élevé", "eleve", "مرتفع", "عالي"}:
        return "High"

    if low.startswith("low") or low in {"faible", "منخفض"}:
        return "Low"

    return "Moderate"


def normalize_finding(finding):
    """Map any accepted key spelling onto one canonical schema."""

    out = {}

    for canonical, aliases in KEY_ALIASES.items():
        value = ""

        for alias in aliases:
            if isinstance(finding, dict) and finding.get(alias):
                value = str(finding[alias]).strip()
                break

        out[canonical] = value

    out["severity"] = get_finding_severity(finding)
    out["title"] = out["title"] or "Contractual Clause"

    return out


def normalize_findings(findings):
    """Normalize then sort by severity (High first). Never raises."""

    if not findings:
        return []

    clean = [
        normalize_finding(f)
        for f in findings
        if isinstance(f, dict)
    ]

    return sorted(
        clean,
        key=lambda f: SEVERITY_ORDER.get(f["severity"], 1)
    )


def _as_int(value, default=0):
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return default


def _as_list(value):
    if value is None:
        return []

    if isinstance(value, (list, tuple, set)):
        return [str(v).strip() for v in value if str(v).strip()]

    text = str(value).strip()

    return [text] if text else []


def unpack_result(result):
    """
    Defensive unpacking of the 11-value tuple returned by analyse().

    A plain tuple assignment crashes the whole page if the shape ever
    changes; here the report degrades instead of breaking.
    """

    values = list(result) if isinstance(result, (list, tuple)) else []

    data = {name: None for name in RESULT_FIELDS}

    for name, value in zip(RESULT_FIELDS, values):
        data[name] = value

    data["risk"] = _as_int(data["risk"], 0)
    data["confidence"] = _as_int(data["confidence"], 0)
    data["lvl"] = data["lvl"] or "Unknown"
    data["cls"] = data["cls"] or "med"
    data["contract_type"] = data["contract_type"] or "Unspecified"
    data["summary"] = data["summary"] or "No summary available."

    for field in ("amounts", "durations", "parties", "obs", "recs"):
        data[field] = _as_list(data[field])

    data["_shape_ok"] = len(values) == len(RESULT_FIELDS)

    return data


def severity_counts(findings):
    counts = {"High": 0, "Moderate": 0, "Low": 0}

    for finding in normalize_findings(findings):
        counts[finding["severity"]] += 1

    return counts


def compliance_score(risk, confidence, counts):
    """Single 0-100 contract-health figure."""

    base = 100 - _as_int(risk, 0)
    base -= counts.get("High", 0) * 8
    base -= counts.get("Moderate", 0) * 3
    base -= counts.get("Low", 0) * 1

    confidence = max(0, min(100, _as_int(confidence, 0)))
    adjusted = base * (0.7 + 0.3 * confidence / 100.0)

    return max(0, min(100, int(round(adjusted))))


# ------------------------------------------------------------------
# Export builders
# ------------------------------------------------------------------

def build_report_text(data, findings, filename="Contract"):
    """Plain-text report (same input -> same output)."""

    ru = TR.get(lang, TR["English"])["report_ui"]
    lv = TR.get(lang, TR["English"])["levels"]

    clean = normalize_findings(findings)
    counts = severity_counts(clean)

    lines = [
        ru["report_title"],
        "=" * 55,
        ru["generated"] + " : " + datetime.now().strftime("%Y-%m-%d %H:%M"),
        ru["contract"] + "  : " + str(filename),
        ru["type"] + "      : " + str(data["contract_type"]),
        "",
        "{}       : {} ({}%)".format(ru["risk_level"], data["lvl"], data["risk"]),
        "{}       : {}%".format(ru["confidence"], data["confidence"]),
        "{} : {}/100".format(
            ru["compliance_score"],
            compliance_score(data["risk"], data["confidence"], counts)
        ),
        "{}         : {} {} / {} {} / {} {}".format(
            ru["findings_count"],
            counts["High"], ru["high"],
            counts["Moderate"], ru["moderate"],
            counts["Low"], ru["low"],
        ),
        "",
        ru["executive_summary"],
        "-" * 55,
        str(data["summary"]),
        "",
        ru["parties"] + "      : " + (", ".join(data["parties"]) or ru["not_identified"]),
        ru["amounts"] + "      : " + (", ".join(data["amounts"]) or ru["not_identified"]),
        ru["durations"] + "    : " + (", ".join(data["durations"]) or ru["not_identified"]),
        "",
        ru["observations"],
        "-" * 55,
    ]

    lines += ["- " + str(o) for o in data["obs"]] or ["- " + ru["none"]]
    lines += ["", ru["recommendations"], "-" * 55]
    lines += ["- " + str(r) for r in data["recs"]] or ["- " + ru["none"]]
    lines += ["", "=" * 55, ru["detailed_findings"], "=" * 55]

    if not clean:
        lines.append(ru["no_finding"])
    else:
        for index, finding in enumerate(clean, start=1):
            lines += [
                "",
                "{} #{} - {} [{}]".format(
                    ru["finding_label"], index, finding["title"],
                    lv.get(finding["severity"], finding["severity"])
                ),
                "-" * 55,
                ru["clause_status"] + " : " + (finding["clause_status"] or ru["na"]),
                "",
                ru["original_clause"],
                finding["original_text"] or ru["clause_not_located"],
                "",
                ru["problem"],
                finding["issue"] or ru["not_specified"],
                "",
                ru["why_it_matters"],
                finding["explanation"] or ru["not_specified"],
                "",
                ru["recommendation_label"],
                finding["recommendation"] or ru["not_specified"],
                "",
                ru["suggested_wording"],
                finding["replacement"] or ru["not_provided"],
                "",
                "-" * 55,
            ]

    lines += [
        "",
        "!" * 55,
        ru["disclaimer"],
        "!" * 55,
    ]

    return "\n".join(lines)


def build_findings_csv(findings):
    """CSV export (a UTF-8 BOM is added at download time for Excel)."""

    ru = TR.get(lang, TR["English"])["report_ui"]
    lv = TR.get(lang, TR["English"])["levels"]

    buffer = _io.StringIO()
    writer = _csv.writer(buffer)

    writer.writerow(ru["csv_headers"])

    for index, finding in enumerate(normalize_findings(findings), start=1):
        writer.writerow([
            index,
            finding["title"],
            lv.get(finding["severity"], finding["severity"]),
            finding["clause_status"],
            finding["original_text"],
            finding["issue"],
            finding["explanation"],
            finding["recommendation"],
            finding["replacement"],
        ])

    return buffer.getvalue()


def build_report_json(data, findings, filename="Contract"):
    """Machine-readable export - the hook for a future REST API."""

    counts = severity_counts(findings)

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "document": str(filename),
        "contract_type": data["contract_type"],
        "risk": {"level": data["lvl"], "score": data["risk"]},
        "confidence": data["confidence"],
        "compliance_score": compliance_score(
            data["risk"], data["confidence"], counts
        ),
        "severity_counts": counts,
        "summary": data["summary"],
        "parties": data["parties"],
        "amounts": data["amounts"],
        "durations": data["durations"],
        "observations": data["obs"],
        "recommendations": data["recs"],
        "findings": normalize_findings(findings),
    }

    return _json.dumps(payload, ensure_ascii=False, indent=2)


# ------------------------------------------------------------------
# Renderer
# ------------------------------------------------------------------

def display_full_report(result, filename="Contract", findings=None, analysis_id=None):
    """Full report for a registered user."""

    ru = TR.get(lang, TR["English"])["report_ui"]
    lv = TR.get(lang, TR["English"])["levels"]

    data = unpack_result(result)

    if not data["_shape_ok"]:
        st.warning(ru["shape_warning"])

    if findings is None:
        findings = st.session_state.get("risk_findings", [])

    clean = normalize_findings(findings)
    counts = severity_counts(clean)
    score = compliance_score(data["risk"], data["confidence"], counts)

    if lang == "العربية":
        st.markdown(
            "<style>.block-container{direction:rtl;text-align:right;}</style>",
            unsafe_allow_html=True
        )

    # ---------------- header ----------------
    st.markdown(
        '<div class="{}">⚠️ {}: {} | {}: {}%</div>'.format(
            _html.escape(str(data["cls"])),
            _html.escape(str(t.get("risk", "Risk"))),
            _html.escape(str(data["lvl"])),
            _html.escape(str(t.get("score", "Score"))),
            data["risk"],
        ),
        unsafe_allow_html=True
    )

    st.markdown("## 📌 " + str(filename))

    # ---------------- KPI row ----------------
    k1, k2, k3, k4 = st.columns(4)

    k1.metric(ru["compliance_metric"], "{}/100".format(score))
    k2.metric(ru["risk_metric"], "{}%".format(data["risk"]), data["lvl"])
    k3.metric(ru["confidence_metric"], "{}%".format(data["confidence"]))
    k4.metric(
        ru["findings_metric"],
        len(clean),
        ru["n_high"].format(n=counts["High"]) if counts["High"] else ru["no_high_risk"],
        delta_color="inverse" if counts["High"] else "normal"
    )

    try:
        st.progress(
            score / 100.0,
            text=ru["health_progress"].format(score=score)
        )
    except TypeError:
        # Older Streamlit versions have no `text` argument.
        st.progress(score / 100.0)

    # ---------------- tabs ----------------
    tab_summary, tab_findings, tab_data, tab_export = st.tabs([
        ru["tab_summary"],
        "{} ({})".format(ru["tab_findings"], len(clean)),
        ru["tab_data"],
        ru["tab_export"],
    ])

    # ----- summary -----
    with tab_summary:

        st.write(data["summary"])

        if counts["High"]:
            st.error(ru["high_risk_warning"].format(n=counts["High"]))
        elif counts["Moderate"]:
            st.warning(ru["moderate_warning"].format(n=counts["Moderate"]))
        else:
            st.success(ru["no_risk_success"])

        if any(counts.values()):
            st.bar_chart(
                {
                    ru["high"]: [counts["High"]],
                    ru["moderate"]: [counts["Moderate"]],
                    ru["low"]: [counts["Low"]],
                }
            )

        if data["recs"]:
            st.markdown("#### " + ru["priority_actions"])

            for recommendation in data["recs"][:5]:
                st.markdown("- " + str(recommendation))

    # ----- findings -----
    with tab_findings:

        if not clean:
            st.info(ru["no_finding_info"])
        else:
            col_filter, col_search = st.columns([1, 2])

            chosen = col_filter.multiselect(
                ru["severity_filter"],
                ["High", "Moderate", "Low"],
                default=["High", "Moderate", "Low"],
                format_func=lambda s: lv.get(s, s),
                key="rv_severity_filter"
            )

            query = col_search.text_input(
                ru["search_findings"],
                key="rv_search"
            ).strip().lower()

            shown = [
                f for f in clean
                if f["severity"] in chosen
                and (
                    not query
                    or query in _json.dumps(f, ensure_ascii=False).lower()
                )
            ]

            st.caption(
                ru["shown_of_total"].format(shown=len(shown), total=len(clean))
            )

            for index, finding in enumerate(shown, start=1):

                with st.expander(
                    "{} {}. {} — {}".format(
                        SEVERITY_ICON[finding["severity"]],
                        index,
                        finding["title"],
                        lv.get(finding["severity"], finding["severity"]),
                    ),
                    expanded=(finding["severity"] == "High" and index <= 2)
                ):

                    if finding["original_text"]:
                        st.markdown("**" + ru["original_clause"].rstrip(":") + "**")
                        st.code(finding["original_text"], language=None)
                    else:
                        st.caption(ru["clause_not_located_caption"])

                    if finding["issue"]:
                        st.markdown("**" + ru["problem_label"] + "** — " + finding["issue"])

                    if finding["explanation"]:
                        st.markdown(
                            "**" + ru["why_it_matters_label"] + "** — " + finding["explanation"]
                        )

                    if finding["recommendation"]:
                        st.info(
                            "**" + ru["recommendation_bold"] + "** — " + finding["recommendation"]
                        )

                    if finding["replacement"]:
                        st.markdown("**" + ru["suggested_wording_bold"] + "**")
                        st.success(finding["replacement"])

    # ----- extracted data -----
    with tab_data:

        c1, c2, c3 = st.columns(3)

        c1.markdown("#### " + ru["parties_header"])
        c1.write(data["parties"] or ru["not_identified"])

        c2.markdown("#### " + ru["amounts_header"])
        c2.write(data["amounts"] or ru["not_identified"])

        c3.markdown("#### " + ru["durations_header"])
        c3.write(data["durations"] or ru["not_identified"])

        st.markdown("#### " + ru["observations_header"])

        if data["obs"]:
            for observation in data["obs"]:
                st.markdown("- " + str(observation))
        else:
            st.caption(ru["no_observation"])

    # ----- export -----
    with tab_export:

        report_text = build_report_text(data, clean, filename)
        stamp = datetime.now().strftime("%Y%m%d_%H%M")

        safe_name = "".join(
            ch for ch in str(filename)
            if ch.isalnum() or ch in (" ", "-", "_")
        ).strip().replace(" ", "_") or "contract"

        e1, e2 = st.columns(2)

        e1.download_button(
            ru["text_report_btn"],
            report_text,
            file_name="LegalVerify_{}_{}.txt".format(safe_name, stamp),
            mime="text/plain",
            use_container_width=True
        )

        e2.download_button(
            ru["csv_btn"],
            "\ufeff" + build_findings_csv(clean),
            file_name="LegalVerify_{}_{}.csv".format(safe_name, stamp),
            mime="text/csv",
            use_container_width=True
        )

        with st.expander(ru["preview_report"]):
            st.text(report_text)

    # ---------------- next step: AI-only or request a lawyer ----------------
    st.markdown("---")
    st.markdown("#### " + ru["lawyer_section_title"])
    st.write(ru["lawyer_question"])

    choice_key = str(analysis_id) if analysis_id is not None else str(filename)
    ack_key = "lawyer_choice_made_" + choice_key

    lc1, lc2 = st.columns(2)

    if lc1.button(
        ru["lawyer_option_ai_only"],
        key="lawyer_ai_only_" + choice_key,
        use_container_width=True
    ):
        st.session_state[ack_key] = "ai_only"

    if lc2.button(
        ru["lawyer_option_request"],
        key="lawyer_request_" + choice_key,
        use_container_width=True
    ):
        current_user = st.session_state.get("user")
        if current_user and not has_pending_lawyer_request(current_user["User ID"], analysis_id):
            try:
                request_lawyer_review(
                    current_user["User ID"],
                    analysis_id,
                    filename,
                    data["contract_type"],
                    data["lvl"]
                )
            except Exception:
                pass
        st.session_state[ack_key] = "requested"

    made_choice = st.session_state.get(ack_key)

    if made_choice == "ai_only":
        st.success(ru["lawyer_ai_only_ack"])
    elif made_choice == "requested":
        st.info(ru["lawyer_request_success"])
        st.caption(ru["lawyer_no_partners_yet"])

    st.markdown(
        '<div class="disclaimer-box">' + _html.escape(ru["footer_disclaimer"]) + '</div>',
        unsafe_allow_html=True
    )
# ==========================================
# LIMITED GUEST REPORT
# ==========================================
def display_guest_report(result):
    (
        lvl,
        risk,
        obs,
        cls,
        amounts,
        durations,
        recs,
        parties,
        contract_type,
        summary,
        confidence
    ) = result

    ru = TR.get(lang, TR["English"])["report_ui"]

    if lang == "العربية":
        st.markdown(
            "<style>.block-container{direction:rtl;text-align:right;}</style>",
            unsafe_allow_html=True
        )

    st.markdown(
        f'<div class="{cls}">⚠️ {t["risk"]}: '
        f'{lvl} | {t["score"]}: {risk}%</div>',
        unsafe_allow_html=True
    )

    st.markdown("## " + ru["guest_title"])

    st.info(ru["guest_info"])

    st.markdown("### " + ru["contract_type_header"])
    st.write(contract_type)

    st.markdown("### " + ru["risk_level_header"])
    st.write(f"{lvl} ({risk}%)")

    st.markdown("### " + ru["confidence_header"])
    st.write(f"{confidence}%")

    st.markdown("### " + ru["summary_header"])
    st.write(summary)

    st.markdown("### " + ru["key_findings_header"])

    if parties:
        st.write(ru["parties_detected"])
    else:
        st.write(ru["parties_not_detected"])

    if amounts:
        st.write(ru["amount_detected"])
    else:
        st.write(ru["amount_not_detected"])

    if durations:
        st.write(ru["duration_detected"])
    else:
        st.write(ru["duration_not_detected"])

    st.warning(ru["guest_warning"])

    st.markdown(
        '<div class="disclaimer-box">' + _html.escape(ru["footer_disclaimer"]) + '</div>',
        unsafe_allow_html=True
    )


# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:

    st.markdown(
        """
    <div style='text-align:center; padding:10px;'>
        {logo}
        <h2 style='margin-bottom:0; margin-top:8px;'>LegalVerifyDZ</h2>
        <p style='color:gray; font-size:14px;'>
        AI Legal Platform
        </p>
    </div>
    """.format(logo=logo_html(56)),
        unsafe_allow_html=True
    )

    st.markdown("---")

    if st.session_state.authenticated:

        user = st.session_state.user

        st.success(
            f"👤 {user['Name']}\n\n"
            f"Plan: {user['Plan']}"
        )

        if st.button(
            t["logout"],
            use_container_width=True,
            key="logout_button"
        ):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.analysis_text = None
            st.session_state.analysis_filename = None
            st.session_state.last_analysis = None
            st.rerun()

    else:

        if st.session_state.guest_used:
            st.warning(
                "👤 Guest mode\n\n"
                "Guest analysis already used."
            )
        else:
            st.info(
                "👤 Guest mode\n\n"
                "1 limited analysis available."
            )

        if st.button(
            "🔐 Login / Create Account",
            use_container_width=True,
            key="open_auth"
        ):
            st.session_state.auth_screen = True
            st.rerun()

    st.markdown("---")

    nav_options = [t["dashboard"], t["generate"], t["analysis"]]

    if st.session_state.authenticated:
        nav_options.append(t["history"])

    page = st.radio(
        "Navigation",
        nav_options
    )

    st.markdown("---")
    st.caption("LegalVerifyDZ © 2026")


# ==========================================
# AUTH SCREEN
# ==========================================
if st.session_state.auth_screen:
    show_auth_screen()
    st.stop()


# ==========================================
# DASHBOARD
# ==========================================
if page == t["dashboard"]:

    st.markdown(
        """
        <div style="text-align:center; padding:40px 20px;">
            {logo}
            <h1 style="font-size:48px; color:#4F8BFF; margin-top:12px;">
                LegalVerifyDZ
            </h1>
            <h3 style="color:#BBBBBB;">
                AI-Powered Contract Intelligence Platform
            </h3>
            <p style="font-size:18px; color:#999999; max-width:800px; margin:auto;">
                Analyze contracts instantly, detect legal risks, extract
                critical clauses, and generate professional agreements
                with AI assistance.
            </p>
        </div>
        """.format(logo=logo_html(100)),
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class='card' style='text-align:center;'>
        <h2>120+</h2>
        <p>Contracts Analyzed</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class='card' style='text-align:center;'>
        <h2>85%</h2>
        <p>Detection Accuracy</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class='card' style='text-align:center;'>
        <h2>3</h2>
        <p>Supported Languages</p>
        </div>
        """, unsafe_allow_html=True)

    if st.session_state.authenticated:
        st.success(
            f"Welcome, {st.session_state.user['Name']}. "
            "You are connected as a registered user."
        )
    elif st.session_state.guest_used:
        st.warning(
            "Your guest analysis has already been used. "
            "Create an account to continue."
        )
    else:
        st.info(
            "You are using LegalVerifyDZ as a guest. "
            "One limited contract analysis is available."
        )

    st.markdown("## 🚀 Platform Features")

    f1, f2 = st.columns(2)

    with f1:
        st.markdown("""
        <div class='card'>
        <h3>📄 Smart Contract Analysis</h3>
        <p>
        Upload PDF or Word contracts and receive legal risk
        analysis, clause detection, summaries and recommendations.
        </p>
        </div>
        """, unsafe_allow_html=True)

    with f2:
        st.markdown("""
        <div class='card'>
        <h3>✍️ AI Contract Generation</h3>
        <p>
        Generate professional legal agreements using simplified
        intelligent forms.
        </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style='text-align:center; color:gray; padding:20px;'>
    LegalVerifyDZ © 2026 — AI-powered legal technology
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# GENERATE CONTRACT
# ==========================================
elif page == t["generate"]:

    st.title(t["generate"])

    p1 = st.text_input("First Party")
    p2 = st.text_input("Second Party")

    if st.button("Generate"):
        if not p1 or not p2:
            st.warning("Please enter both parties.")
        else:
            st.markdown(
                f'<div class="card">'
                f'Contract between {p1} and {p2}'
                f'</div>',
                unsafe_allow_html=True
            )


# ==========================================
# SMART ANALYSIS
# ==========================================
elif page == t["analysis"]:

    st.title(t["analysis"])

    # ---------------------------------
    # Guest restriction
    # ---------------------------------
    if (
        not st.session_state.authenticated
        and st.session_state.guest_used
    ):
        st.error(
            "🔒 Your one guest analysis has already been used."
        )

        st.info(
            "Create an account or log in to continue using "
            "Smart Analysis."
        )

        if st.button(
            "🔐 Login / Create Account",
            key="analysis_auth_button"
        ):
            st.session_state.auth_screen = True
            st.rerun()

        st.stop()

    # ---------------------------------
    # Demo
    # ---------------------------------
    if st.button("🎯 Run Demo"):

        demo_text = """
        This service contract is made between Company Alpha
        and Company Beta.

        The contract value is 15000 USD.

        The duration is 12 months.

        The service includes maintenance and technical support.

        The parties agree to termination conditions,
        liability provisions and a penalty clause.
        """

        with st.spinner(
            "🤖 AI is analyzing the contract..."
        ):
            import time
            time.sleep(1)

        result = analyse(demo_text, report_lang=lang)

        st.session_state.last_analysis = result
        st.session_state.analysis_text = demo_text
        st.session_state.analysis_filename = "Demo Contract"

        if not st.session_state.authenticated:
            st.session_state.guest_used = True
            display_guest_report(result)
        else:
            st.success("Demo loaded successfully.")
            display_full_report(
                result,
                "Demo Contract"
            )

        st.stop()

    # ---------------------------------
    # Upload
    # ---------------------------------
    st.markdown("### 📄 Upload Contract")

    file = st.file_uploader(
        "PDF / Word",
        type=["pdf", "docx"],
        key="contract_uploader"
    )

    pasted_text = st.text_area(
        "Or paste contract text",
        height=180,
        placeholder="Paste the contract text here...",
        key="contract_text_input"
    )

    current_text = None
    current_filename = "Pasted Contract"

    if file:

        current_filename = file.name

        if file.type == "application/pdf":
            current_text, error, used_ocr = extract_pdf(file)
        else:
            current_text, error, used_ocr = extract_docx(file)

        if error:
            st.error(error)
        else:
            st.success("File loaded successfully.")

            if used_ocr:
                ru = TR.get(lang, TR["English"])["report_ui"]
                st.info(ru["ocr_used_note"])

            st.session_state.analysis_text = current_text
            st.session_state.analysis_filename = file.name

            with st.expander(
                "Preview extracted text"
            ):
                st.text(current_text[:5000])

    elif pasted_text.strip():

        current_text = pasted_text
        st.session_state.analysis_text = pasted_text
        st.session_state.analysis_filename = "Pasted Contract"

    # ---------------------------------
    # Analyze
    # ---------------------------------
    if st.button(
        t["analyze"],
        type="primary",
        use_container_width=True
    ):

        text_to_analyze = (
            current_text
            or st.session_state.analysis_text
        )

        filename = (
            current_filename
            if current_text
            else (
                st.session_state.analysis_filename
                or "Contract"
            )
        )

        if not text_to_analyze or not text_to_analyze.strip():
            st.warning(
                "Please upload a PDF/Word file "
                "or paste contract text."
            )
        else:

            with st.spinner(
                "🤖 AI is analyzing the contract..."
            ):
                import time
                time.sleep(1)

            result = analyse(text_to_analyze, report_lang=lang)

            st.session_state.last_analysis = result
            st.session_state.analysis_text = text_to_analyze
            st.session_state.analysis_filename = filename

            if not st.session_state.authenticated:
                st.session_state.guest_used = True
                display_guest_report(result)
            else:
                findings_for_history = st.session_state.get("risk_findings", [])
                new_analysis_id = None
                try:
                    new_analysis_id = save_analysis(
                        st.session_state.user["User ID"],
                        filename,
                        result,
                        findings_for_history
                    )
                except Exception:
                    # History is a convenience feature; never let a
                    # storage hiccup block the user from seeing their
                    # report.
                    pass

                st.session_state.last_analysis_id = new_analysis_id

                display_full_report(
                    result,
                    filename,
                    analysis_id=new_analysis_id
                )

    # ---------------------------------
    # Previous result
    # ---------------------------------
    elif st.session_state.last_analysis is not None:

        st.markdown("### Previous Analysis")

        if st.session_state.authenticated:
            display_full_report(
                st.session_state.last_analysis,
                st.session_state.analysis_filename
                or "Contract",
                analysis_id=st.session_state.get("last_analysis_id")
            )
        else:
            display_guest_report(
                st.session_state.last_analysis
            )

# ==========================================
# HISTORY  (registered users only)
# ==========================================
elif page == t["history"]:

    ru = TR.get(lang, TR["English"])["report_ui"]

    st.markdown("## " + ru["history_title"])

    if not st.session_state.authenticated or not st.session_state.user:
        st.info(ru["history_empty"])
        st.stop()

    open_id = st.session_state.get("history_open_id")

    if open_id is not None:

        if st.button(ru["history_back"], key="history_back_btn"):
            st.session_state.history_open_id = None
            st.rerun()

        rows = get_user_analyses(st.session_state.user["User ID"])
        row = next((r for r in rows if r["id"] == open_id), None)

        if row is None:
            st.session_state.history_open_id = None
            st.rerun()
        else:
            try:
                payload = _json.loads(row["report_json"])
                display_full_report(
                    tuple(payload["result"]),
                    row["filename"] or "Contract",
                    findings=payload["findings"],
                    analysis_id=row["id"]
                )
            except Exception:
                st.error(ru["shape_warning"])

    else:
        rows = get_user_analyses(st.session_state.user["User ID"])

        if not rows:
            st.info(ru["history_empty"])
        else:
            for row in rows:
                with st.container():
                    st.markdown('<div class="card">', unsafe_allow_html=True)

                    c1, c2, c3 = st.columns([3, 1, 1])

                    c1.markdown(
                        "**{}**  \n{} · {} ({}%)  \n{}: {}".format(
                            row["filename"] or "Contract",
                            row["contract_type"] or "-",
                            row["risk_level"] or "-",
                            row["risk_score"] if row["risk_score"] is not None else "-",
                            ru["history_date"],
                            row["created_at"] or "-",
                        )
                    )

                    if c2.button(ru["history_view"], key="hv_{}".format(row["id"])):
                        st.session_state.history_open_id = row["id"]
                        st.rerun()

                    if c3.button(ru["history_delete"], key="hd_{}".format(row["id"])):
                        delete_analysis(row["id"], st.session_state.user["User ID"])
                        st.success(ru["history_deleted"])
                        st.rerun()

                    st.markdown('</div>', unsafe_allow_html=True)
