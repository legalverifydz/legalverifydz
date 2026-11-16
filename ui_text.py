# -*- coding: utf-8 -*-
"""
ui_text.py -- LegalVerifyDZ
Interface strings (ar / en / fr) and commercial settings for the
landing page, the user workspace and the plans page.
Merged into the main T dictionary in app.py.
"""

# ------------------------------------------------------------------
# COMMERCIAL SETTINGS -- edit here
# ------------------------------------------------------------------
# Contact address used by the "Request this plan" buttons. While it is
# empty the buttons are hidden and a generic contact note is shown.
CONTACT_EMAIL = ""

# Official packages. Annual price = 12 x monthly (no discount), as in
# the pricing sheet. PLAN_LIMITS is DISPLAY ONLY (dashboard usage bar):
# nothing in the app enforces it, and no payment is processed.
PLANS = [
    {"id": "Starter",      "monthly": 9900,  "yearly": 118800, "analysis_per_year": 6},
    {"id": "Professional", "monthly": 24900, "yearly": 298800, "analysis_per_year": 18},
    {"id": "Business",     "monthly": 49900, "yearly": 598800, "analysis_per_year": None},  # unlimited
]
PLAN_LIMITS = {p["id"]: p["analysis_per_year"] for p in PLANS if p["analysis_per_year"]}

NEW_T = {
    # =============================================================
    "العربية": {
        "language_label": "اللغة / Language",
        "sidebar_tagline": "تحليل العقود بالذكاء الاصطناعي",
        "plan_label": "الخطة",
        "guest_mode": "وضع الزائر",
        "guest_left": "تحليل واحد محدود متاح.",
        "guest_none": "تم استخدام تحليل الزائر.",
        "login_signup": "تسجيل الدخول / إنشاء حساب",
        "plans": "الباقات",
        "run_demo": "تشغيل عرض تجريبي",
        "upload_heading": "رفع عقد",
        "cta_analyze": "حلّل عقدك الآن",
        "cta_demo": "جرّب عرضًا تجريبيًا",
        "cta_plans": "عرض الباقات",
        "currency": "دج",
        "plan_names": {"Free": "مجانية", "Starter": "Starter", "Professional": "Professional", "Business": "Business"},

        # --- hero
        "hero_badge": "للشركات والأقسام القانونية",
        "hero_title": "راجع عقودك قبل التوقيع واكتشف مخاطرها في دقائق",
        "hero_sub": "منصتك الذكية لتحليل العقود واكتشاف المخاطر القانونية وفق البيئة القانونية الجزائرية.",
        "hero_chips": ["مواد من القانون المدني الجزائري", "مسح ضوئي OCR بثلاث لغات", "تقارير بالعربية والفرنسية والإنجليزية"],

        # --- value tiles
        "values": [
            {"i": "landmark", "t": "مرجعية قانونية جزائرية", "d": "ملاحظات مرتبطة بمواد محتملة من القانون المدني وقانون الإجراءات المدنية والإدارية."},
            {"i": "scale", "t": "بنود تُقاس على الممارسة الجزائرية", "d": "الإنهاء والشرط الجزائي والدفع والاختصاص والمسؤولية، مصنّفة حسب الخطورة."},
            {"i": "scan", "t": "عقود ممسوحة ضوئيًا", "d": "استخراج النص بالعربية والفرنسية والإنجليزية، حتى 15 صفحة."},
            {"i": "languages", "t": "ثلاث لغات", "d": "واجهة وتقارير بلغتك، أيًّا كانت لغة العقد."},
        ],

        # --- tabs
        "tab_how": "كيف تعمل",
        "tab_sample": "عيّنة تقرير",
        "tab_who": "لمن المنصة",
        "tab_trust": "الثقة والخصوصية",
        "steps": [
            {"t": "ارفع العقد", "d": "ملف PDF أو Word أو نسخة ممسوحة ضوئيًا، أو الصق النص مباشرة."},
            {"t": "تحليل تلقائي", "d": "تُستخرج الأطراف والمبالغ والمدد والبنود، ثم تُقاس المخاطر."},
            {"t": "استلم التقرير", "d": "ملخّص ودرجة مخاطر وتوصيات وصيغ بديلة للبنود، مع تصدير بصيغ متعددة."},
        ],
        "sample_note": "عيّنة توضيحية لعقد افتراضي، وليست تحليلًا لعقد حقيقي.",
        "sample_type_lbl": "نوع العقد", "sample_type": "عقد خدمات",
        "sample_risk_lbl": "درجة المخاطر", "sample_risk_level": "عالية",
        "sample_conf_lbl": "درجة الثقة",
        "sample_findings": [
            {"s": "high", "sl": "عالية", "t": "لا يوجد بند للإنهاء", "d": "العقد لا يبيّن شروط إنهائه ولا مهلة الإخطار. المرجع المحتمل: المادة 106 من القانون المدني."},
            {"s": "med", "sl": "متوسطة", "t": "شروط الدفع غير محددة", "d": "لا يوجد أجل للدفع ولا أثر للتأخر عنه."},
            {"s": "med", "sl": "متوسطة", "t": "الاختصاص القضائي غير مذكور", "d": "يُستحسن تحديد موطن مختار. المرجع المحتمل: المادة 37 من قانون الإجراءات المدنية والإدارية."},
        ],
        "who": [
            {"i": "building", "t": "الشركات الصغيرة والمتوسطة", "d": "راجع عقود الموردين والعملاء قبل التوقيع دون انتظار موعد مع محامٍ."},
            {"i": "briefcase", "t": "الأقسام القانونية", "d": "فرز أولي سريع للعقود الواردة وتحديد ما يستحق مراجعة معمّقة."},
            {"i": "users", "t": "مسؤولو المشتريات والعقود", "d": "اكتشف البنود الناقصة أو غير المتوازنة قبل أن تصبح نزاعًا."},
            {"i": "scale", "t": "المحامون والمستشارون", "d": "نقطة انطلاق منظَّمة لمراجعة العقد، مع إحالات إلى المواد المحتملة."},
        ],
        "trust": [
            {"i": "lock", "t": "كلمات المرور مشفّرة", "d": "لا تُخزَّن كلمات المرور كنص واضح."},
            {"i": "landmark", "t": "القانون 18-07", "d": "سياسة حماية المعطيات مستندة إلى القانون 18-07، مع حقوق الولوج والتصحيح والمسح."},
            {"i": "shield", "t": "تدريب المحرّك اختياري", "d": "استخدام عقودك لتحسين التحليل بند منفصل، ورفضه لا يؤثر على استخدامك."},
            {"i": "scale", "t": "لا يغني عن محامٍ", "d": "التحليل آلي، ويمكنك طلب مراجعة محامٍ عند الحاجة."},
        ],

        # --- workspace
        "ws_hello": "مرحبًا، {name}",
        "ws_sub": "نظرة سريعة على نشاط عقودك ومخاطرها.",
        "ws_plan": "الخطة: {plan}",
        "ws_usage": "{used} من {limit} عقود هذا العام",
        "ws_usage_free": "{used} تحليلات هذا العام",
        "kpi_total": "إجمالي التحليلات",
        "kpi_total_sub": "هذا الشهر: {n}",
        "kpi_avg": "متوسط الخطورة",
        "kpi_high": "عقود عالية الخطورة",
        "kpi_high_sub": "تستحق مراجعة معمّقة",
        "kpi_lawyer": "طلبات مراجعة محامٍ",
        "kpi_lawyer_sub": "قيد الانتظار",
        "dist_title": "توزيع مستويات الخطورة",
        "risk_low": "منخفض", "risk_med": "متوسط", "risk_high": "مرتفع",
        "recent": "آخر العقود المحلَّلة",
        "no_recent": "لا توجد تحليلات بعد. ارفع أول عقد لتبدأ.",
        "open_btn": "عرض",
        "new_analysis": "تحليل عقد جديد",
        "view_all": "سجلّ التحليلات",

        # --- plans page
        "plans_title": "الباقات",
        "plans_sub": "باقات واضحة تناسب حجم عقودك وفريقك.",
        "per_month": "/ شهريًا",
        "or_yearly": "أو {price} سنويًا",
        "plan_current": "خطتك الحالية",
        "plan_request": "اطلب هذه الباقة",
        "plan_free_note": "حسابك الحالي على الخطة {plan}.",
        "plan_contact": "للاشتراك أو لأي استفسار: {email}",
        "plan_contact_none": "للاشتراك أو للاستفسار عن الباقات تواصل مع فريق المنصة.",
        "cmp_title": "مقارنة تفصيلية",
        "cmp_head": ["الميزة", "Starter", "Professional", "Business"],
        "plan_feats": {
            "Starter": ["6 عقود تُحلَّل سنويًا", "مستخدم واحد", "صياغة 3 عقود سنويًا", "دعم عادي"],
            "Professional": ["18 عقدًا تُحلَّل سنويًا", "3 مستخدمين", "تتبّع العقود وتنبيهات الآجال", "صياغة 6 عقود سنويًا", "دعم ذو أولوية"],
            "Business": ["تحليل غير محدود", "10 مستخدمين أو أكثر", "تدقيق الامتثال / ISO", "صياغة غير محدودة", "دعم مخصّص"],
        },
        "cmp_rows": [
            ["تحليل العقود", "محدود · 6 عقود/سنة", "محدود · 18 عقدًا/سنة", "غير محدود"],
            ["المخاطر والالتزامات", "✓", "✓", "✓"],
            ["التقرير", "✓", "✓", "✓"],
            ["سجلّ التحليلات", "محدود", "✓", "✓"],
            ["تتبّع العقود", "—", "✓", "✓"],
            ["تنبيهات المواعيد والآجال", "—", "✓", "✓"],
            ["صياغة العقود", "محدودة · 3 عقود/سنة", "محدودة · 6 عقود/سنة", "غير محدودة"],
            ["تدقيق الامتثال / ISO", "—", "محدود", "✓"],
            ["عدد المستخدمين", "1", "3", "10+"],
            ["لوحة التحكم", "✓", "✓", "✓"],
            ["الدعم", "عادي", "ذو أولوية", "مخصّص"],
            ["خدمات حسب الطلب", "✓", "✓", "✓"],
        ],
    },

    # =============================================================
    "English": {
        "language_label": "Language / اللغة",
        "sidebar_tagline": "AI contract analysis",
        "plan_label": "Plan",
        "guest_mode": "Guest mode",
        "guest_left": "1 limited analysis available.",
        "guest_none": "Guest analysis already used.",
        "login_signup": "Login / Create Account",
        "plans": "Plans",
        "run_demo": "Run demo",
        "upload_heading": "Upload contract",
        "cta_analyze": "Analyze your contract",
        "cta_demo": "Try a demo",
        "cta_plans": "View plans",
        "currency": "DZD",
        "plan_names": {"Free": "Free", "Starter": "Starter", "Professional": "Professional", "Business": "Business"},

        "hero_badge": "For businesses and legal teams",
        "hero_title": "Review contracts before you sign and spot legal risks in minutes",
        "hero_sub": "Your smart platform for contract analysis and legal risk detection, tailored to the Algerian legal environment.",
        "hero_chips": ["Algerian Civil Code references", "OCR in three languages", "Reports in Arabic, French and English"],

        "values": [
            {"i": "landmark", "t": "Algerian legal references", "d": "Findings linked to potentially applicable Civil Code and Civil Procedure articles."},
            {"i": "scale", "t": "Clauses checked against local practice", "d": "Termination, penalty, payment, jurisdiction and liability, ranked by severity."},
            {"i": "scan", "t": "Scanned contracts", "d": "Text recognized in Arabic, French and English, up to 15 pages."},
            {"i": "languages", "t": "Three languages", "d": "Interface and reports in your language, whatever the contract's language."},
        ],

        "tab_how": "How it works",
        "tab_sample": "Sample report",
        "tab_who": "Who it is for",
        "tab_trust": "Trust and privacy",
        "steps": [
            {"t": "Upload the contract", "d": "A PDF, a Word file or a scanned copy, or paste the text directly."},
            {"t": "Automatic analysis", "d": "Parties, amounts, durations and clauses are extracted, then risk is measured."},
            {"t": "Get the report", "d": "Summary, risk score, recommendations and replacement wording, with several export formats."},
        ],
        "sample_note": "Illustrative sample for a fictional contract, not an analysis of a real one.",
        "sample_type_lbl": "Contract type", "sample_type": "Service contract",
        "sample_risk_lbl": "Risk score", "sample_risk_level": "High",
        "sample_conf_lbl": "Confidence",
        "sample_findings": [
            {"s": "high", "sl": "High", "t": "No termination clause", "d": "The contract does not state how it can be ended or the notice period. Possible reference: Art. 106 of the Civil Code."},
            {"s": "med", "sl": "Moderate", "t": "Payment terms not defined", "d": "No payment deadline and no consequence for late payment."},
            {"s": "med", "sl": "Moderate", "t": "Jurisdiction not stated", "d": "A chosen domicile is advisable. Possible reference: Art. 37 of the Code of Civil and Administrative Procedure."},
        ],
        "who": [
            {"i": "building", "t": "Small and mid-size businesses", "d": "Review supplier and client contracts before signing, without waiting for a lawyer's appointment."},
            {"i": "briefcase", "t": "Legal departments", "d": "Fast first-pass triage of incoming contracts to see which deserve a deeper review."},
            {"i": "users", "t": "Procurement and contract managers", "d": "Spot missing or unbalanced clauses before they become disputes."},
            {"i": "scale", "t": "Lawyers and advisors", "d": "A structured starting point for contract review, with pointers to potentially applicable articles."},
        ],
        "trust": [
            {"i": "lock", "t": "Passwords are hashed", "d": "Passwords are never stored as plain text."},
            {"i": "landmark", "t": "Law n° 18-07", "d": "The data-protection policy is based on Law n° 18-07, with rights of access, correction and erasure."},
            {"i": "shield", "t": "Engine training is optional", "d": "Using your contracts to improve the analysis is a separate clause; declining has no effect on your use."},
            {"i": "scale", "t": "Not a lawyer", "d": "The analysis is automated; you can request a lawyer's review when needed."},
        ],

        "ws_hello": "Welcome, {name}",
        "ws_sub": "A quick look at your contract activity and risks.",
        "ws_plan": "Plan: {plan}",
        "ws_usage": "{used} of {limit} contracts this year",
        "ws_usage_free": "{used} analyses this year",
        "kpi_total": "Total analyses",
        "kpi_total_sub": "This month: {n}",
        "kpi_avg": "Average risk",
        "kpi_high": "High-risk contracts",
        "kpi_high_sub": "Deserve a deeper review",
        "kpi_lawyer": "Lawyer-review requests",
        "kpi_lawyer_sub": "Pending",
        "dist_title": "Risk level distribution",
        "risk_low": "Low", "risk_med": "Moderate", "risk_high": "High",
        "recent": "Recently analyzed contracts",
        "no_recent": "No analyses yet. Upload your first contract to get started.",
        "open_btn": "View",
        "new_analysis": "Analyze a new contract",
        "view_all": "Analysis history",

        "plans_title": "Plans",
        "plans_sub": "Clear plans that fit your contract volume and your team.",
        "per_month": "/ month",
        "or_yearly": "or {price} per year",
        "plan_current": "Your current plan",
        "plan_request": "Request this plan",
        "plan_free_note": "Your account is currently on the {plan} plan.",
        "plan_contact": "To subscribe or ask questions: {email}",
        "plan_contact_none": "To subscribe or ask about plans, get in touch with the platform team.",
        "cmp_title": "Detailed comparison",
        "cmp_head": ["Feature", "Starter", "Professional", "Business"],
        "plan_feats": {
            "Starter": ["6 contracts analyzed per year", "1 user", "3 contracts drafted per year", "Standard support"],
            "Professional": ["18 contracts analyzed per year", "3 users", "Contract tracking and deadline alerts", "6 contracts drafted per year", "Priority support"],
            "Business": ["Unlimited analysis", "10+ users", "Compliance / ISO audit", "Unlimited drafting", "Dedicated support"],
        },
        "cmp_rows": [
            ["Contract analysis", "Limited · 6 contracts/year", "Limited · 18 contracts/year", "Unlimited"],
            ["Risks and obligations", "✓", "✓", "✓"],
            ["Report", "✓", "✓", "✓"],
            ["Analysis history", "Limited", "✓", "✓"],
            ["Contract tracking", "—", "✓", "✓"],
            ["Deadline and due-date alerts", "—", "✓", "✓"],
            ["Contract drafting", "Limited · 3 contracts/year", "Limited · 6 contracts/year", "Unlimited"],
            ["Compliance / ISO audit", "—", "Limited", "✓"],
            ["Users", "1", "3", "10+"],
            ["Dashboard", "✓", "✓", "✓"],
            ["Support", "Standard", "Priority", "Dedicated"],
            ["Services on request", "✓", "✓", "✓"],
        ],
    },

    # =============================================================
    "Français": {
        "language_label": "Langue / اللغة",
        "sidebar_tagline": "Analyse de contrats par IA",
        "plan_label": "Offre",
        "guest_mode": "Mode invité",
        "guest_left": "1 analyse limitée disponible.",
        "guest_none": "Analyse invité déjà utilisée.",
        "login_signup": "Connexion / Créer un compte",
        "plans": "Offres",
        "run_demo": "Lancer la démo",
        "upload_heading": "Téléverser un contrat",
        "cta_analyze": "Analysez votre contrat",
        "cta_demo": "Essayer une démo",
        "cta_plans": "Voir les offres",
        "currency": "DA",
        "plan_names": {"Free": "Gratuite", "Starter": "Starter", "Professional": "Professional", "Business": "Business"},

        "hero_badge": "Pour les entreprises et directions juridiques",
        "hero_title": "Relisez vos contrats avant de signer et repérez les risques juridiques en quelques minutes",
        "hero_sub": "Votre plateforme intelligente pour l'analyse de contrats et la détection des risques juridiques, adaptée à l'environnement juridique algérien.",
        "hero_chips": ["Articles du Code civil algérien", "OCR en trois langues", "Rapports en arabe, français et anglais"],

        "values": [
            {"i": "landmark", "t": "Références juridiques algériennes", "d": "Constats reliés à des articles potentiellement applicables du Code civil et du Code de procédure."},
            {"i": "scale", "t": "Clauses évaluées selon la pratique locale", "d": "Résiliation, clause pénale, paiement, compétence et responsabilité, classées par gravité."},
            {"i": "scan", "t": "Contrats scannés", "d": "Texte reconnu en arabe, français et anglais, jusqu'à 15 pages."},
            {"i": "languages", "t": "Trois langues", "d": "Interface et rapports dans votre langue, quelle que soit celle du contrat."},
        ],

        "tab_how": "Comment ça marche",
        "tab_sample": "Exemple de rapport",
        "tab_who": "À qui s'adresse-t-elle",
        "tab_trust": "Confiance et confidentialité",
        "steps": [
            {"t": "Téléversez le contrat", "d": "PDF, Word ou copie scannée, ou collez directement le texte."},
            {"t": "Analyse automatique", "d": "Parties, montants, durées et clauses sont extraits, puis le risque est mesuré."},
            {"t": "Recevez le rapport", "d": "Résumé, score de risque, recommandations et formulations de remplacement, avec plusieurs formats d'export."},
        ],
        "sample_note": "Exemple illustratif pour un contrat fictif, et non l'analyse d'un contrat réel.",
        "sample_type_lbl": "Type de contrat", "sample_type": "Contrat de services",
        "sample_risk_lbl": "Score de risque", "sample_risk_level": "Élevé",
        "sample_conf_lbl": "Confiance",
        "sample_findings": [
            {"s": "high", "sl": "Élevé", "t": "Aucune clause de résiliation", "d": "Le contrat n'indique ni comment il peut prendre fin ni le préavis. Référence possible : art. 106 du Code civil."},
            {"s": "med", "sl": "Modéré", "t": "Conditions de paiement non définies", "d": "Pas de délai de paiement ni de conséquence en cas de retard."},
            {"s": "med", "sl": "Modéré", "t": "Compétence juridictionnelle non précisée", "d": "Un domicile élu est conseillé. Référence possible : art. 37 du Code de procédure civile et administrative."},
        ],
        "who": [
            {"i": "building", "t": "PME", "d": "Relisez les contrats fournisseurs et clients avant signature, sans attendre un rendez-vous chez l'avocat."},
            {"i": "briefcase", "t": "Directions juridiques", "d": "Un tri préliminaire rapide des contrats reçus pour repérer ceux qui méritent une revue approfondie."},
            {"i": "users", "t": "Responsables achats et contrats", "d": "Repérez les clauses manquantes ou déséquilibrées avant qu'elles ne deviennent un litige."},
            {"i": "scale", "t": "Avocats et conseillers", "d": "Un point de départ structuré pour la revue d'un contrat, avec des renvois aux articles potentiels."},
        ],
        "trust": [
            {"i": "lock", "t": "Mots de passe chiffrés", "d": "Les mots de passe ne sont jamais stockés en clair."},
            {"i": "landmark", "t": "Loi n° 18-07", "d": "La politique de protection des données s'appuie sur la loi n° 18-07, avec droits d'accès, de rectification et d'effacement."},
            {"i": "shield", "t": "Entraînement du moteur facultatif", "d": "L'utilisation de vos contrats pour améliorer l'analyse est une clause distincte ; la refuser n'affecte pas votre usage."},
            {"i": "scale", "t": "Ne remplace pas un avocat", "d": "L'analyse est automatisée ; vous pouvez demander l'avis d'un avocat si nécessaire."},
        ],

        "ws_hello": "Bienvenue, {name}",
        "ws_sub": "Un aperçu rapide de l'activité et des risques de vos contrats.",
        "ws_plan": "Offre : {plan}",
        "ws_usage": "{used} contrats sur {limit} cette année",
        "ws_usage_free": "{used} analyses cette année",
        "kpi_total": "Analyses au total",
        "kpi_total_sub": "Ce mois-ci : {n}",
        "kpi_avg": "Risque moyen",
        "kpi_high": "Contrats à risque élevé",
        "kpi_high_sub": "À examiner en profondeur",
        "kpi_lawyer": "Demandes d'avis d'avocat",
        "kpi_lawyer_sub": "En attente",
        "dist_title": "Répartition des niveaux de risque",
        "risk_low": "Faible", "risk_med": "Modéré", "risk_high": "Élevé",
        "recent": "Derniers contrats analysés",
        "no_recent": "Aucune analyse pour l'instant. Téléversez votre premier contrat.",
        "open_btn": "Voir",
        "new_analysis": "Analyser un nouveau contrat",
        "view_all": "Historique des analyses",

        "plans_title": "Offres",
        "plans_sub": "Des offres claires, adaptées au volume de vos contrats et à votre équipe.",
        "per_month": "/ mois",
        "or_yearly": "ou {price} par an",
        "plan_current": "Votre offre actuelle",
        "plan_request": "Demander cette offre",
        "plan_free_note": "Votre compte est actuellement sur l'offre {plan}.",
        "plan_contact": "Pour souscrire ou poser une question : {email}",
        "plan_contact_none": "Pour souscrire ou vous renseigner sur les offres, contactez l'équipe de la plateforme.",
        "cmp_title": "Comparatif détaillé",
        "cmp_head": ["Élément", "Starter", "Professional", "Business"],
        "plan_feats": {
            "Starter": ["6 contrats analysés par an", "1 utilisateur", "3 contrats rédigés par an", "Support standard"],
            "Professional": ["18 contrats analysés par an", "3 utilisateurs", "Suivi des contrats et alertes d'échéances", "6 contrats rédigés par an", "Support prioritaire"],
            "Business": ["Analyse illimitée", "10 utilisateurs et plus", "Audit conformité / ISO", "Rédaction illimitée", "Support dédié"],
        },
        "cmp_rows": [
            ["Analyse de contrats", "Limité · 6 contrats/an", "Limité · 18 contrats/an", "Illimité"],
            ["Risques / obligations", "✓", "✓", "✓"],
            ["Rapport", "✓", "✓", "✓"],
            ["Historique", "Limité", "✓", "✓"],
            ["Suivi des contrats", "—", "✓", "✓"],
            ["Alertes délais / échéances", "—", "✓", "✓"],
            ["Rédaction de contrats", "Limitée · 3 contrats/an", "Limitée · 6 contrats/an", "Illimitée"],
            ["Audit conformité / ISO", "—", "Limité", "✓"],
            ["Utilisateurs", "1", "3", "10+"],
            ["Tableau de bord", "✓", "✓", "✓"],
            ["Support", "Standard", "Prioritaire", "Dédié"],
            ["Services à la carte", "✓", "✓", "✓"],
        ],
    },
}


# ------------------------------------------------------------------
# Arabic UI text is shown WITHOUT diacritics (tashkeel): cleaner and
# closer to how the rest of the interface reads.
# ------------------------------------------------------------------
import re as _re

_TASHKEEL = _re.compile("[\u064B-\u0652\u0670]")


def strip_tashkeel(obj):
    """Recursively remove Arabic diacritics from strings in dicts/lists."""
    if isinstance(obj, str):
        return _TASHKEEL.sub("", obj)
    if isinstance(obj, dict):
        return {k: strip_tashkeel(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [strip_tashkeel(v) for v in obj]
    return obj


NEW_T["العربية"] = strip_tashkeel(NEW_T["العربية"])
