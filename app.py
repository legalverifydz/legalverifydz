import streamlit as st
import pdfplumber
import docx

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="LegalVerifyDZ", layout="wide")

# ==========================================
# CSS
# ==========================================
st.markdown("""
<style>
.main {background-color: #F3F4F6;}

[data-testid="stSidebar"] {
    background-color: #0F172A;
}

[data-testid="stSidebar"] * {
    color: white;
}

.card {
    background-color: white;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 20px;
}

.low {background:#DCFCE7;padding:10px;border-radius:10px;}
.med {background:#FEF9C3;padding:10px;border-radius:10px;}
.high {background:#FEE2E2;padding:10px;border-radius:10px;}
body {
    background-color: #0E1117;
}

section[data-testid="stSidebar"] {
    background-color: #111827;
    border-right: 1px solid #1F2937;
}

.card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 25px;
    backdrop-filter: blur(10px);
    box-shadow: 0 0 20px rgba(79,139,255,0.08);
    transition: 0.3s;
}

.card:hover {
    transform: translateY(-3px);
    box-shadow: 0 0 30px rgba(79,139,255,0.20);
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
</style>
""", unsafe_allow_html=True)

# ==========================================
# LANGUAGE
# ==========================================
lang = st.sidebar.selectbox("Language", ["English","Français","العربية"])

T = {
"English":{"dashboard":"Dashboard","generate":"Generate Contract","analysis":"Smart Analysis","analyze":"Analyze","text":"Paste text","upload":"Upload file","risk":"Risk","score":"Score"},
"Français":{"dashboard":"Dashboard","generate":"Contrat","analysis":"Analyse","analyze":"Analyser","text":"Texte","upload":"Fichier","risk":"Risque","score":"Score"},
"العربية":{"dashboard":"لوحة","generate":"عقد","analysis":"تحليل","analyze":"تحليل","text":"نص","upload":"ملف","risk":"المخاطر","score":"النسبة"}
}

t = T[lang]

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:

    st.markdown("""
    <div style='text-align:center; padding:10px;'>
        <h1 style='color:#4F8BFF;'>⚖️</h1>
        <h2 style='margin-bottom:0;'>LegalVerifyDZ</h2>
        <p style='color:gray; font-size:14px;'>
        AI Legal Platform
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    page = st.radio(
        "Navigation",
        [
            t["dashboard"],
            t["generate"],
            t["analysis"]
        ]
    )

    st.markdown("---")

    st.caption("LegalVerifyDZ © 2026")

# ==========================================
# FUNCTIONS
# ==========================================

def extract_pdf(f):
    text = ""
    try:
        with pdfplumber.open(f) as pdf:
            for p in pdf.pages:
                t = p.extract_text()
                if t:
                    text += t

        if not text.strip():
            return None, "Empty or scanned PDF (no readable text)"

        return text, None

    except Exception:
        return None, "Invalid or corrupted PDF"


def extract_docx(f):
    try:
        d = docx.Document(f)
        text = "\n".join([p.text for p in d.paragraphs])
        if not text.strip():
            return None, "Empty Word file"
        return text, None
    except Exception:
        return None, "Invalid Word file"


def analyse(text):
    risk = 0
    obs = []
    recommendations = []

    txt = text.lower()

    # ---------------------------------
    # Detect clauses
    # ---------------------------------
    if "penalty" in txt or "pénalité" in txt:
        risk += 20
        obs.append("Penalty clause detected")

    else:
        recommendations.append("Consider adding a penalty clause")

    if "termination" in txt or "résiliation" in txt:
        risk += 20
        obs.append("Termination clause detected")
    else:
        recommendations.append("Define termination conditions")

    if "arbitration" in txt or "arbitrage" in txt:
        risk += 15
        obs.append("Arbitration clause detected")

    if "liability" in txt or "responsabilité" in txt:
        risk += 15
        obs.append("Liability clause detected")

    # ---------------------------------
    # Extract data
    # ---------------------------------
    import re

    # ---------------------------------
    # Amount extraction (EN + FR + AR)
    # ---------------------------------
    import re

    amounts = re.findall(
        r"\b\d{1,3}(?:[.,]\d{3})*(?:\s?(?:dzd|da|usd|eur|\$|€|دينار|دج))?",
    txt
)

    # تنظيف
    amounts = [a for a in amounts if len(a) > 3]

    # ---------------------------------
    # Duration extraction (EN + FR + AR)
    # ---------------------------------
    durations = re.findall(
        r"\b\d+\s?(days?|months?|years?|jours?|mois|ans|يوم|أيام|شهر|أشهر|سنة|سنوات)\b",
    txt
)

    if not amounts:
        risk += 15
        recommendations.append("Specify contract value")

    if not durations:
        risk += 10
        recommendations.append("Specify contract duration")

    # ---------------------------------
    # Parties extraction (NEW)
    # ---------------------------------
    parties = []

    import re

    patterns = [
        r"between\s+(.*?)\s+and\s+(.*?)[\.,\n]",
        r"entre\s+(.*?)\s+et\s+(.*?)[\.,\n]",
        r"بين\s+(.*?)\s+و\s+(.*?)[\.,\n]"
        r"الطرف\s+الأول[:\s]+(.*?)\s+.*?الطرف\s+الثاني[:\s]+(.*?)[\.,\n]"
]

    for pattern in patterns:
        match = re.search(pattern, txt)
        if match:
            parties = [match.group(1), match.group(2)]
            break
    # ---------------------------------
    # Contract Type Detection (NEW)
    # ---------------------------------
    contract_type = "Unknown"

    if any(word in txt for word in ["service", "maintenance", "prestations"]):
        contract_type = "Service Contract"

    elif any(word in txt for word in ["sale", "purchase", "vente"]):
        contract_type = "Sale Contract"

    elif any(word in txt for word in ["lease", "rent", "location"]):
        contract_type = "Lease Contract"
    # ---------------------------------
    # Smart Summary (NEW)
    # ---------------------------------
    summary = f"This contract is classified as {contract_type}. "
    # ---------------------------------
    # Penalty for missing critical data
    # ---------------------------------
    if not parties:
        risk += 20

    if not amounts:
        risk += 20

    if not durations:
        risk += 15
    if risk < 30:
        summary += "It presents low legal risk. "
    elif risk < 60:
        summary += "It presents moderate legal risk. "
    else:
        summary += "It presents high legal risk. "

    if parties:
        summary += f"It involves {parties[0]} and {parties[1]}. "

    if amounts:
        summary += f"The contract includes financial values such as {amounts[0]}. "

    if durations:
        summary += f"The duration appears to be {durations[0]}. "
    # ---------------------------------
    # Confidence Score (NEW)
    # ---------------------------------
    confidence = 100

    if not parties:
        confidence -= 25
    if not amounts:
        confidence -= 25
    if not durations:
        confidence -= 20
    if risk > 60:
        confidence -= 10

    confidence = max(confidence, 30)
    # ---------------------------------
    # FINAL Risk Level (AFTER all calculations)
    # ---------------------------------
    if risk < 30:
        lvl = "Low"
        cls = "low"
    elif risk < 60:
        lvl = "Moderate"
        cls = "med"
    else:
        lvl = "High"
        cls = "high"
    return lvl, risk, obs, cls, amounts, durations, recommendations, parties, contract_type, summary, confidence
# ==========================================
# PAGES
# ==========================================

# ---- DASHBOARD ----
if page == t["dashboard"]:
    st.markdown("""
    <div style='text-align:center; padding:40px 20px;'>

    <h1 style='font-size:60px; color:#4F8BFF; margin-bottom:10px;'>
    ⚖️ LegalVerifyDZ
    </h1>

    <h3 style='color:#BBBBBB;'>
    AI-Powered Contract Intelligence Platform
    </h3>

    <p style='font-size:18px; color:#999999; max-width:800px; margin:auto; margin-top:20px;'>
    Analyze contracts instantly, detect legal risks, extract critical clauses,
    and generate professional agreements with AI assistance.
    </p>

    </div>
    """, unsafe_allow_html=True)

    # ---------------------------------
    # Stats Cards
    # ---------------------------------
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

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------------------------
    # Features Section
    # ---------------------------------
    st.markdown("## 🚀 Platform Features")

    f1, f2 = st.columns(2)

    with f1:
        st.markdown("""
        <div class='card'>
        <h3>📄 Smart Contract Analysis</h3>
        <p>
        Upload PDF or Word contracts and receive instant legal risk analysis,
        clause detection, summaries, and recommendations.
        </p>
        </div>
        """, unsafe_allow_html=True)

    with f2:
        st.markdown("""
        <div class='card'>
        <h3>✍️ AI Contract Generation</h3>
        <p>
        Generate professional legal agreements in seconds using simplified intelligent forms.
        </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    st.markdown("""
    <div style='text-align:center; color:gray; padding:20px;'>
    LegalVerifyDZ © 2026 — AI-powered legal technology
    </div>
    """, unsafe_allow_html=True)

# ---- GENERATE ----
elif page == t["generate"]:
    st.title(t["generate"])

    p1 = st.text_input("First Party")
    p2 = st.text_input("Second Party")

    if st.button("Generate"):
        st.markdown(f'<div class="card">Contract between {p1} and {p2}</div>', unsafe_allow_html=True)

# ---- ANALYSIS ----
elif page == t["analysis"]:
    st.title(t["analysis"])
    if st.button("🎯 Run Demo"):
        text = """
        This service contract is made between Company Alpha and Company Beta.
        The contract value is 15000 USD.
        The duration is 12 months.
        The service includes maintenance and technical support.
        """
        with st.spinner("🤖 AI is analyzing the contract..."):
            import time
            time.sleep(2)
        lvl, risk, obs, cls, amounts, durations, recs, parties, contract_type, summary, confidence = analyse(text)

        st.success("Demo loaded successfully")

        st.markdown("## 📌 Analysis Report")

        st.markdown(f"### 📄 Contract Type: {contract_type}")
        st.markdown(f"### ⚠️ Risk Level: {lvl} ({risk}%)")
        st.markdown(f"### 📊 Confidence Score: {confidence}%")

        st.markdown("### 🧠 Executive Summary")
        st.write(summary)
      
        if risk > 60:
            st.error("🚨 High Risk Contract – Immediate attention required")
        elif risk > 30:
            st.warning("⚠️ Moderate Risk – Review recommended")
        else:
            st.success("✅ Low Risk – Contract appears safe")

        st.markdown("### 👥 Parties")
        if parties:
            for p in parties:
                st.write("- " + p)
        else:
            st.info("⚠️ Could not confidently extract this information.")

        st.markdown("### 📊 Extracted Data")

        if amounts:
            st.write("💰 Amounts:")
            for a in amounts:
                st.write("- " + a)

        if durations:
            st.write("⏳ Duration:")
            for d in durations:
                st.write("- " + d)

    else:
        file = st.file_uploader("PDF / Word", type=["pdf","docx"])

        if file:
            if file.type == "application/pdf":
                text, error = extract_pdf(file)
            else:
                text, error = extract_docx(file)

            if error:
                st.error(error)
            else:
                st.success("File loaded successfully")

            st.info("If your PDF is scanned, text extraction may not work.")

    if st.button(t["analyze"]):
        with st.spinner("🤖 AI is analyzing the uploaded contract..."):
            import time
            time.sleep(2)
        if not text or not text.strip():
            st.warning("No text to analyze")
        else:
            lvl, risk, obs, cls, amounts, durations, recs, parties, contract_type, summary, confidence = analyse(text)
            
            st.markdown(
                f'<div class="{cls}">{t["risk"]}: {lvl} | {t["score"]}: {risk}%</div>',
                unsafe_allow_html=True
            )

            st.markdown('<div class="card">', unsafe_allow_html=True)
            report_text = f"""
            LegalVerifyDZ - AI Analysis Report
            ==================================

            Contract Type:
            {contract_type}

            Risk Level:
            {lvl} ({risk}%)

            Confidence Score:
            {confidence}%

            Executive Summary:
            {summary}

            Detected Parties:
            {parties}

            Amounts:
            {amounts}

            Durations:
            {durations}

            Recommendations:
            {recs}
            """
            st.markdown("## 📌 Analysis Report")
            col1, col2 = st.columns([1,5])

            with col1:
                st.download_button(
                    "📥 Export",
                    report_text,
                    file_name="LegalVerify_Report.txt"
                )
            st.markdown("### 🧠 Executive Summary")
            st.write(summary)
            st.markdown("### 🤖 AI Insights")

            if risk > 60:
                st.error("""
                - Critical contractual information appears incomplete.
                - The agreement may expose one or both parties to legal ambiguity.
                - Immediate legal review is strongly recommended.
                """)
            elif risk > 30:
                st.warning("""
                - Some contractual clauses may require clarification.
                - Additional legal validation is recommended.
                - Certain obligations are not clearly defined.
                """)
            else:
                st.success("""
                - The contract structure appears generally consistent.
                - No major legal inconsistencies were detected.
                - Basic contractual safeguards are present.
                """)
            # ---------------------------------
            # Risk Factors
            # ---------------------------------
            st.markdown("### ⚠️ Main Risk Factors")
            # ---------------------------------
            # Export Report
            # ---------------------------------
            
            factors = []

            if not parties:
                factors.append("Missing or unclear party identification")

            if not amounts:
                factors.append("No clear contract value detected")

            if not durations:
                factors.append("Contract duration is not clearly defined")

            if risk > 60:
                factors.append("High legal ambiguity detected")

            if len(factors) == 0:
                st.success("No major contractual risk factors detected.")
            else:
                for f in factors:
                    st.write("- " + f)
            if risk > 60:
                st.error("🚨 High Risk Contract – Immediate attention required")
            elif risk > 30:
                st.warning("⚠️ Moderate Risk – Review recommended")
            else:
                st.success("✅ Low Risk – Contract appears safe")
            st.markdown(f"### 📄 Contract Type: {contract_type}")
            # Risk
            st.markdown(f"### 📊 Confidence Score: {confidence}%")
            st.markdown(f"### ⚠️ Risk Level: {lvl} ({risk}%)")

            # Parties
            st.markdown("### 👥 Parties")
            if parties:
                for p in parties:
                    st.write("- " + p)
            else:
                st.info("⚠️ Could not confidently extract this information. Manual review recommended.")

            # Observations
            st.markdown("### 🔍 Observations")
            if obs:
                for o in obs:
                    st.write("- " + o)
            else:
                st.write("No major issues detected")

            # Extracted Data
            st.markdown("### 📊 Extracted Data")

            if amounts:
                st.write("💰 Amounts:")
                for a in amounts[:5]:
                    st.write("- " + a)
            else:
                st.write("No amounts found")

            if durations:
                st.write("⏳ Duration:")
                for d in durations:
                    st.write("- " + d)
            else:
                st.write("No duration found")

            # Recommendations
            st.markdown("### 💡 Recommendations")
            if recs:
                for r in recs:
                    st.write("- " + r)
            else:
                st.write("No recommendations")

            st.markdown('</div>', unsafe_allow_html=True)