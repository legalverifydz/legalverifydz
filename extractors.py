"""
extractors.py -- LegalVerifyDZ
================================================================
Pure text-extraction primitives, pulled out of the original
monolithic analyse() function (sections 1-9): normalization,
contract-language detection, contract-type classification, and
extraction of parties / amounts / durations / clause segments.

None of this depends on Streamlit, on the report language (TR/fx/ox/
sx), or on the risk-scoring logic -- it only reads raw contract text
and returns structured facts about it. That is what makes it safe to
unit-test on its own (see the __main__ block at the bottom).
================================================================
"""

import re


def extract_all(text, report_lang=None):
    """
    Run every text-extraction step on `text` and return a single
    context dict consumed by rules.build_findings() and
    scoring.compute_score(). `report_lang` is accepted for interface
    symmetry with the other modules but is not used here: extraction
    only cares about the CONTRACT's own language (detected below as
    `detected_language`), never the interface language the user chose.
    """

    # =========================================================
    # 1. BASIC NORMALIZATION
    # =========================================================

    if not text:
        text = ""

    original_text = str(text)

    # Normalize spaces without destroying line structure
    normalized = re.sub(r"\r\n?", "\n", original_text)
    normalized = re.sub(r"[ \t]+", " ", normalized)

    # Keep a second version for keyword analysis
    analysis_text = re.sub(r"\s+", " ", normalized).strip()

    # =========================================================
    # 2. LANGUAGE DETECTION
    #    Contract language != report/interface language
    # =========================================================

    arabic_chars = len(re.findall(r"[\u0600-\u06FF]", analysis_text))

    french_keywords = [
        "contrat", "article", "entre", "société", "prestataire",
        "client", "résiliation", "pénalité", "paiement",
        "responsabilité", "litige", "tribunal", "obligation",
        "maintenance", "service", "durée", "montant"
    ]

    english_keywords = [
        "contract", "article", "between", "company", "provider",
        "client", "termination", "penalty", "payment",
        "liability", "dispute", "court", "obligation",
        "maintenance", "service", "duration", "amount"
    ]

    french_hits = sum(
        1 for word in french_keywords
        if re.search(r"\b" + re.escape(word) + r"\b", analysis_text, re.I)
    )

    english_hits = sum(
        1 for word in english_keywords
        if re.search(r"\b" + re.escape(word) + r"\b", analysis_text, re.I)
    )

    if arabic_chars >= 20:
        detected_language = "Arabic"
    elif french_hits >= english_hits and french_hits >= 2:
        detected_language = "French"
    elif english_hits >= 2:
        detected_language = "English"
    else:
        detected_language = "French"

    # =========================================================
    # 3. GENERIC HELPERS
    # =========================================================

    def clean_text(value):

        if not value:
            return ""

        value = re.sub(r"\s+", " ", value)
        value = value.strip(" \t\r\n:;-–—,.")

        return value.strip()

    def unique_keep_order(items):

        result = []
        seen = set()

        for item in items:

            item = clean_text(item)

            if not item:
                continue

            key = item.lower()

            if key not in seen:
                seen.add(key)
                result.append(item)

        return result

    def is_boilerplate_party(value):

        if not value:
            return True

        low = value.lower().strip()

        forbidden = [
            "les soussignés",
            "soussignés",
            "ci-après",
            "ci-après dénommé",
            "ci-après dénommée",
            "représenté par",
            "représentée par",
            "agissant en qualité",
            "the undersigned",
            "hereinafter",
            "represented by",
            "acting as",
            "الطرف الأول",
            "الطرف الثاني",
            "الموقع أدناه",
            "الموقعون أدناه",
            "الموقعين أدناه"
        ]

        return any(
            phrase in low
            for phrase in forbidden
        )

    def clean_party(value):

        if not value:
            return ""

        value = clean_text(value)

        # Remove common introductory expressions
        value = re.sub(
            r"^(les\s+)?soussignés\s*:?\s*",
            "",
            value,
            flags=re.I
        )

        value = re.sub(
            r"^the\s+undersigned\s*:?\s*",
            "",
            value,
            flags=re.I
        )

        value = re.sub(
            r"^(الطرف\s+الأول|الطرف\s+الثاني)\s*:?\s*",
            "",
            value,
            flags=re.I
        )

        # Remove descriptions after the legal entity name
        value = re.split(
            r",\s*(?:situ[ée]e?|représent[ée]e?|agissant|"
            r"ayant|dont|ci-après|représenté|représentée)\b",
            value,
            maxsplit=1,
            flags=re.I
        )[0]

        value = re.split(
            r"\s+(?:ci-après|hereinafter)\b",
            value,
            maxsplit=1,
            flags=re.I
        )[0]

        value = clean_text(value)

        if is_boilerplate_party(value):
            return ""

        return value

    # =========================================================
    # 4. CONTRACT TYPE
    #    Canonical values are returned.
    #    Renderer can translate them later.
    # =========================================================

    def detect_contract_type():

        service_patterns = [
            r"\bmaintenance\b",
            r"\bprestataire\b",
            r"\bprestation\b",
            r"\bservices?\b",
            r"\bservice contract\b",
            r"\bmaintenance contract\b",
            r"الصيانة",
            r"الخدمات",
            r"الخدمة",
            r"مقدم الخدمة",
            r"عقد خدمات"
        ]

        sale_patterns = [
            r"\bvente\b",
            r"\bvendeur\b",
            r"\bachat\b",
            r"\bpurchase\b",
            r"\bsale\b",
            r"\bbuyer\b",
            r"\bseller\b",
            r"البيع",
            r"الشراء",
            r"المشتري",
            r"البائع"
        ]

        lease_patterns = [
            r"\blocation\b",
            r"\blocataire\b",
            r"\bbailleur\b",
            r"\blease\b",
            r"\brental\b",
            r"\btenant\b",
            r"\blandlord\b",
            r"الإيجار",
            r"المؤجر",
            r"المستأجر"
        ]

        service_score = sum(
            bool(re.search(pattern, analysis_text, re.I))
            for pattern in service_patterns
        )

        sale_score = sum(
            bool(re.search(pattern, analysis_text, re.I))
            for pattern in sale_patterns
        )

        lease_score = sum(
            bool(re.search(pattern, analysis_text, re.I))
            for pattern in lease_patterns
        )

        scores = {
            "Service / Maintenance Contract": service_score,
            "Sale / Purchase Contract": sale_score,
            "Lease / Rental Contract": lease_score
        }

        best_type = max(
            scores,
            key=scores.get
        )

        if scores[best_type] == 0:
            return "Unknown"

        return best_type

    contract_type = detect_contract_type()

    # =========================================================
    # 5. PARTY EXTRACTION
    # =========================================================

    def extract_parties():

        parties = []

        # -----------------------------------------------------
        # FRENCH
        # -----------------------------------------------------

        if detected_language == "French":

            # Entre X et Y
            patterns = [
                r"\bentre\s+(.+?)\s+et\s+(.+?)(?=\s+(?:ci-après|d'une part|d’autre part|"
                r"ci-apres|représenté|représentée|ci-après dénommé|$))",

                r"\bentre\s+(.+?)\s+et\s+(.+?)(?=\n|$)"
            ]

            for pattern in patterns:

                match = re.search(
                    pattern,
                    analysis_text,
                    re.I
                )

                if match:

                    for group in match.groups():

                        party = clean_party(group)

                        if (
                            party
                            and len(party) > 3
                            and not is_boilerplate_party(party)
                        ):
                            parties.append(party)

                    if len(parties) >= 2:
                        break

            # Société / SARL / SPA / EURL names
            entity_pattern = (
                r"\b(?:Société|SARL|SPA|EURL|"
                r"S\.A\.R\.L\.|S\.P\.A\.|E\.U\.R\.L\.)"
                r"\s+[A-ZÀ-ÖØ-Ý0-9][^,\n;:.]+"
            )

            for match in re.findall(
                entity_pattern,
                normalized,
                re.I
            ):

                party = clean_party(match)

                if (
                    party
                    and len(party) > 3
                    and not is_boilerplate_party(party)
                ):
                    parties.append(party)

        # -----------------------------------------------------
        # ENGLISH
        # -----------------------------------------------------

        elif detected_language == "English":

            patterns = [
                r"\bbetween\s+(.+?)\s+and\s+(.+?)(?=\s+(?:hereinafter|represented|"
                r"on the one hand|on the other hand|$))",

                r"\bbetween\s+(.+?)\s+and\s+(.+?)(?=\n|$)"
            ]

            for pattern in patterns:

                match = re.search(
                    pattern,
                    analysis_text,
                    re.I
                )

                if match:

                    for group in match.groups():

                        party = clean_party(group)

                        if (
                            party
                            and len(party) > 3
                            and not is_boilerplate_party(party)
                        ):
                            parties.append(party)

                    if len(parties) >= 2:
                        break

            entity_pattern = (
                r"\b(?:Company|Corporation|Corp\.|LLC|Ltd\.|Inc\.)"
                r"\s+[A-Z0-9][^,\n;:.]+"
            )

            for match in re.findall(
                entity_pattern,
                normalized,
                re.I
            ):

                party = clean_party(match)

                if (
                    party
                    and len(party) > 3
                    and not is_boilerplate_party(party)
                ):
                    parties.append(party)

        # -----------------------------------------------------
        # ARABIC
        # -----------------------------------------------------

        else:

            # بين X و Y
            arabic_between_patterns = [
                r"بين\s+(.+?)\s+(?:و|وَ)\s+(.+?)(?=\s+(?:ويمثل|ويمثلها|"
                r"ويشار إليه|ويشار إليها|المشار إليه|المشار إليها|$))",

                r"بين\s+(.+?)\s+(?:و|وَ)\s+(.+?)(?=\n|$)"
            ]

            for pattern in arabic_between_patterns:

                match = re.search(
                    pattern,
                    analysis_text,
                    re.I
                )

                if match:

                    for group in match.groups():

                        party = clean_party(group)

                        if (
                            party
                            and len(party) > 3
                            and not is_boilerplate_party(party)
                        ):
                            parties.append(party)

                    if len(parties) >= 2:
                        break

            # الطرف الأول / الطرف الثاني
            arabic_label_patterns = [
                r"الطرف\s+الأول\s*[:\-]\s*(.+?)(?=\s+الطرف\s+الثاني|\n|$)",
                r"الطرف\s+الثاني\s*[:\-]\s*(.+?)(?=\s+الطرف|\n|$)"
            ]

            for pattern in arabic_label_patterns:

                match = re.search(
                    pattern,
                    analysis_text,
                    re.I
                )

                if match:

                    party = clean_party(match.group(1))

                    if (
                        party
                        and len(party) > 3
                        and not is_boilerplate_party(party)
                    ):
                        parties.append(party)

            # Company / المؤسسة / الشركة patterns
            arabic_entity_pattern = (
                r"(?:شركة|مؤسسة|مكتب|مصنع|مجمع)\s+"
                r"[^،,;\n:]+"
            )

            for match in re.findall(
                arabic_entity_pattern,
                normalized
            ):

                party = clean_party(match)

                if (
                    party
                    and len(party) > 3
                    and not is_boilerplate_party(party)
                ):
                    parties.append(party)

        # -----------------------------------------------------
        # Final cleaning
        # -----------------------------------------------------

        parties = unique_keep_order(parties)

        # Remove obvious non-party fragments
        final_parties = []

        for party in parties:

            low = party.lower()

            if any(
                x in low
                for x in [
                    "montant",
                    "duration",
                    "article",
                    "pénalité",
                    "penalty",
                    "résiliation",
                    "termination",
                    "paiement",
                    "payment"
                ]
            ):
                continue

            if len(party) < 4:
                continue

            final_parties.append(party)

        return final_parties[:4]

    # ---------------------------------------------------------------
    # Tier 1: parties named in the contract's PREAMBLE
    # ---------------------------------------------------------------
    # extract_parties() above scans the WHOLE contract, so it also picks
    # up later mentions of an entity ("...تلتزم مؤسسة الصيانة بالتدخل..."),
    # signature blocks that glue both names on one line, and suffix-style
    # names ("ALPHA INDUSTRIES LLC") it does not recognise. A contract
    # names its parties once, in the opening paragraph -- so we first read
    # ONLY that window, and fall back to the legacy scan only if the
    # window does not yield two parties.
    # (Limitation: bilateral contracts are assumed, so at most two
    # parties are returned.)

    _AR_ENTITY_KEYS = {
        "شركة", "مؤسسة", "مكتب", "مصنع", "مجمع", "جمعية", "وكالة",
        "مجموعة", "بنك", "مقاولة", "ورشة",
    }
    _AR_NAME_STOP_PREFIXES = (
        "ويمثل", "يمثل", "ممثل", "ومقر", "مقر", "الكائن", "وعنوان",
        "عنوان", "المسجل", "الواقع", "بصفت", "ويشار", "المشار",
        "والتي", "والذي", "التي", "الذي", "المولود", "القاطن",
        "الساكن", "الحامل", "وبين",
    )
    _LATIN_PREFIX_FORMS = {
        "société", "societe", "entreprise", "établissement",
        "etablissement", "ets", "sarl", "spa", "eurl", "snc",
        "company", "corporation", "corp", "ltd", "limited", "inc",
        "llc", "association", "groupe", "group",
    }
    _LATIN_SUFFIX_FORMS = {
        "llc", "sarl", "spa", "eurl", "snc", "sa", "ltd", "inc",
        "corp", "gmbh",
    }
    _LATIN_NAME_STOP = {
        "between", "entre", "and", "et", "the", "le", "la", "les",
        "with", "avec", "by", "par",
    }
    _PUNCT_END = ",;:.،؛"

    def _core(tok):
        return tok.strip(",;:.،؛()«»\"“”'")

    def _form(tok):
        return _core(tok).replace(".", "").lower()

    def _is_name_token(c):
        return bool(c) and (c[0].isupper() or c[0].isdigit() or c == "&")

    def _preamble_window():
        markers = [
            r"بين\s", r"\bentre\b", r"\bbetween\b",
        ]
        start = None
        for marker in markers:
            m = re.search(marker, analysis_text, re.I)
            if m and (start is None or m.start() < start):
                start = m.start()
        if start is None:
            start = 0

        limit = 1500
        tail = analysis_text[start:start + limit]
        end_m = re.search(
            r"\barticle\s*(?:1|premier|one|i)\b|المادة\s*(?:الأولى|1|01)\b"
            r"|\bsection\s*1\b",
            tail,
            re.I
        )
        if end_m and end_m.start() > 20:
            tail = tail[:end_m.start()]
        return tail

    def _arabic_entities(tokens):
        found = []
        for i, (pos, tok) in enumerate(tokens):
            core = _core(tok)
            if core in _AR_ENTITY_KEYS:
                key = core
            elif core.startswith("و") and core[1:] in _AR_ENTITY_KEYS:
                key = core[1:]
            else:
                continue

            name = [key]
            ended = tok[-1:] in _PUNCT_END
            j = i + 1

            while not ended and j < len(tokens) and len(name) < 7:
                t = tokens[j][1]
                c = _core(t)

                if (
                    not c
                    or c in ("و", "بين")
                    or any(c.startswith(p) for p in _AR_NAME_STOP_PREFIXES)
                    or c in _AR_ENTITY_KEYS
                    or (c.startswith("و") and c[1:] in _AR_ENTITY_KEYS)
                ):
                    break

                name.append(c)
                ended = t[-1:] in _PUNCT_END
                j += 1

            if len(name) >= 2:
                found.append((pos, " ".join(name)))

        return found

    def _latin_entities(tokens):
        found = []
        n = len(tokens)

        for i, (pos, tok) in enumerate(tokens):
            form = _form(tok)

            # (a) prefix style: "Société ALPHA INDUSTRIE", "Company Alpha"
            if form in _LATIN_PREFIX_FORMS and _is_name_token(_core(tok)):
                name = [_core(tok)]
                ended = tok[-1:] in _PUNCT_END
                j = i + 1

                while not ended and j < n and len(name) < 7:
                    t = tokens[j][1]
                    c = _core(t)

                    if not _is_name_token(c) or _form(t) in _LATIN_NAME_STOP:
                        break

                    name.append(c)
                    ended = t[-1:] in _PUNCT_END
                    j += 1

                if len(name) >= 2:
                    found.append((pos, " ".join(name)))

            # (b) suffix style: "ALPHA INDUSTRIES LLC", "TECHNISERV SARL"
            if form in _LATIN_SUFFIX_FORMS and _is_name_token(_core(tok)):
                name = [_core(tok)]
                j = i - 1

                while j >= 0 and len(name) < 7:
                    prev = tokens[j][1]
                    c = _core(prev)

                    if (
                        not _is_name_token(c)
                        or prev[-1:] in _PUNCT_END
                        or _form(prev) in _LATIN_NAME_STOP
                        or _form(prev) in _LATIN_SUFFIX_FORMS
                    ):
                        break

                    name.insert(0, c)
                    j -= 1

                if len(name) >= 2:
                    found.append((tokens[j + 1][0], " ".join(name)))

        return found

    _CIVILITY = {
        "السيد", "السيدة", "الآنسة", "المسمى", "المدعو",
        "monsieur", "madame", "mademoiselle", "m", "mme", "mlle",
        "mr", "mrs", "ms", "mister", "madam",
    }
    _REPRESENTATION_MARKERS = (
        "ويمثل", "يمثل", "ممثل", "représenté", "representé", "represented",
        "بواسطة", "agissant", "acting", "المدير", "gérant", "manager",
    )

    def _person_entities(tokens):
        """Natural persons ("السيد محمد ..."), skipping anyone introduced
        as a REPRESENTATIVE of an entity ("ويمثلها السيد ...")."""
        found = []

        for i, (pos, tok) in enumerate(tokens):
            if _form(tok) not in _CIVILITY:
                continue

            before = " ".join(t for _, t in tokens[max(0, i - 3):i]).lower()
            if any(marker in before for marker in _REPRESENTATION_MARKERS):
                continue

            name = []
            ended = False
            j = i + 1
            while not ended and j < len(tokens) and len(name) < 5:
                t = tokens[j][1]
                c = _core(t)
                latin = bool(re.match(r"[A-Za-zÀ-ÿ]", c or " "))
                if (
                    not c
                    or c in ("و", "et", "and", "بين")
                    or any(c.startswith(p) for p in _AR_NAME_STOP_PREFIXES)
                    or (latin and not _is_name_token(c))
                ):
                    break
                name.append(c)
                ended = t[-1:] in _PUNCT_END
                j += 1

            if len(name) >= 2:
                found.append((pos, " ".join([_core(tok)] + name)))

        return found

    def _prune_parties(items):
        uniq = []
        seen = set()
        for it in items:
            clean = re.sub(r"\s+", " ", it).strip()
            if clean and clean.lower() not in seen:
                seen.add(clean.lower())
                uniq.append(clean)

        lows = [u.lower() for u in uniq]

        # Drop concatenations: an entry that contains 2+ other entries
        keep = []
        for idx, u in enumerate(uniq):
            inside = [
                k for k in range(len(uniq))
                if k != idx and lows[k] != lows[idx] and lows[k] in lows[idx]
            ]
            if len(inside) >= 2:
                continue
            keep.append(u)

        # Drop shortened references contained in a longer entry
        lows = [u.lower() for u in keep]
        final = []
        for idx, u in enumerate(keep):
            if any(
                k != idx and len(lows[k]) > len(lows[idx])
                and lows[idx] in lows[k]
                for k in range(len(keep))
            ):
                continue
            final.append(u)

        return final

    def extract_parties_smart():
        window = _preamble_window()
        tokens = [(m.start(), m.group()) for m in re.finditer(r"\S+", window)]

        found = _arabic_entities(tokens) + _latin_entities(tokens)

        if len({n for _, n in found}) < 2:
            found += _person_entities(tokens)

        found.sort(key=lambda item: item[0])

        names = _prune_parties([n for _, n in found])
        names = [
            n for n in names
            if len(n) > 3 and not is_boilerplate_party(n)
        ]

        if len(names) >= 2:
            return names[:2]

        # Fallback: legacy whole-contract scan, merged and pruned
        legacy = extract_parties()
        return _prune_parties(names + legacy)[:2]

    parties = extract_parties_smart()

    # Post-processing fix: some extraction patterns capture a whole
    # "X and Y" / "X et Y" / "X و Y" phrase as a single party instead of
    # two, which then duplicates against an already-captured "X" entry
    # (e.g. ["Company Alpha", "Company Alpha and Company Beta"]).
    # Split those connector phrases apart and de-duplicate again.
    def _split_and_dedupe_parties(raw_parties):
        connectors = [" and ", " et ", " و "]
        expanded = []

        for party in raw_parties:
            fragments = [party]
            for connector in connectors:
                next_fragments = []
                for fragment in fragments:
                    next_fragments.extend(
                        piece.strip()
                        for piece in fragment.split(connector)
                        if piece.strip()
                    )
                fragments = next_fragments
            expanded.extend(fragments)

        seen = set()
        deduped = []
        for party in expanded:
            key = party.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(party)

        return deduped

    parties = _split_and_dedupe_parties(parties)

    # =========================================================
    # 6. AMOUNT EXTRACTION
    # =========================================================

    def extract_amounts():

        amounts = []

        # -----------------------------------------------------
        # 1. Amounts explicitly followed by a currency
        # -----------------------------------------------------

        # Thousands separators: space, dot, COMMA ("500,000 DZD" used to
        # be read as "000 DZD"), and non-breaking spaces.
        currency_pattern = (
            r"(?<![\d.,])"
            r"(\d{1,3}(?:[ .,\u00a0\u202f]\d{3})+|\d+)"
            r"\s*"
            r"(DA|DZD|EUR|USD|\$|€|دينار(?:\s+جزائري)?|دج)"
        )

        for match in re.finditer(
            currency_pattern,
            analysis_text,
            re.I
        ):

            number = clean_text(match.group(1))
            currency = clean_text(match.group(2))

            value = f"{number} {currency}"

            amounts.append(value)

        # -----------------------------------------------------
        # 2. Amounts written with contextual words
        #    only if no currency amount was found
        # -----------------------------------------------------

        if not amounts:

            contextual_patterns = [

                # French
                r"(?:montant|prix|valeur|somme)"
                r"\s*(?:de|:)?\s*"
                r"(\d{1,3}(?:[ .]\d{3})+|\d+)",

                # English
                r"(?:amount|price|value|sum)"
                r"\s*(?:of|:)?\s*"
                r"(\d{1,3}(?:[ ,]\d{3})+|\d+)",

                # Arabic
                r"(?:مبلغ|قيمة|سعر|مقابل)"
                r"\s*(?:العقد|الخدمة|البيع)?"
                r"\s*(?:هو|:)?\s*"
                r"(\d{1,3}(?:[ .]\d{3})+|\d+)"
            ]

            for pattern in contextual_patterns:

                matches = re.findall(
                    pattern,
                    analysis_text,
                    re.I
                )

                for match in matches:

                    value = clean_text(match)

                    if value:
                        amounts.append(value)

        # -----------------------------------------------------
        # 3. Remove duplicates
        # -----------------------------------------------------

        return unique_keep_order(amounts)

    amounts = extract_amounts()

    # =========================================================
    # 7. DURATION EXTRACTION
    # =========================================================

    def extract_durations():

        durations = []

        patterns = [

            # French
            r"\b(?:pour|pendant|d'une durée de|durée de)\s+"
            r"(une année|un an|deux ans|trois ans|"
            r"\d+\s+(?:an|ans|mois|jours))",

            r"\b(une année|un an|deux ans|trois ans|"
            r"\d+\s+(?:an|ans|mois|jours))\b",

            # English
            r"\b(?:for|during|duration of)\s+"
            r"(one year|one month|two years|three years|"
            r"\d+\s+(?:year|years|month|months|day|days))",

            r"\b(one year|one month|two years|three years|"
            r"\d+\s+(?:year|years|month|months|day|days))\b",

            # Arabic
            r"(?:لمدة|مدة)\s*"
            r"(سنة|عام|عام واحد|سنة واحدة|"
            r"سنتين|ثلاث سنوات|\d+\s*(?:سنة|سنوات|شهر|أشهر|يوم|أيام))",

            r"\b(سنة|عام|سنتين|ثلاث سنوات)\b"
        ]

        for pattern in patterns:

            for match in re.finditer(
                pattern,
                analysis_text,
                re.I
            ):

                value = clean_text(
                    match.group(1)
                )

                if value:
                    durations.append(value)

        return unique_keep_order(durations)

    durations = extract_durations()

    # =========================================================
    # 8. CLAUSE SEGMENTATION
    # =========================================================

    def split_clauses():

        source_text = normalized

        # -----------------------------------------------------
        # Article / Article 1 / Article 2 ...
        # French + English + Arabic
        # -----------------------------------------------------

        heading_pattern = re.compile(
            r"(?im)^\s*"
            r"("
            r"Article\s+\d+\s*[-–—:.]?"
            r"|Art\.\s*\d+\s*[-–—:.]?"
            r"|ARTICLE\s+\d+\s*[-–—:.]?"
            r"|المادة\s+\d+\s*[-–—:.]?"
            r"|البند\s+\d+\s*[-–—:.]?"
            r")"
        )

        matches = list(
            heading_pattern.finditer(source_text)
        )

        clauses = []

        # -----------------------------------------------------
        # If Articles are detected
        # -----------------------------------------------------

        if matches:

            for index, match in enumerate(matches):

                start = match.start()

                if index + 1 < len(matches):

                    end = matches[index + 1].start()

                else:

                    end = len(source_text)

                block = source_text[start:end].strip()

                # -------------------------------------------------
                # Remove signature / closing section
                # -------------------------------------------------

                # A signature block is a line made of ROLE NAMES only
                # ("Le Client      Le Prestataire", "The Client"). The old
                # patterns matched any paragraph merely STARTING with
                # "Le Client" / "The Client" -- so a payment paragraph such
                # as "Le Client s'engage a regler ... 30 jours" was cut off
                # as if it were a signature, and its deadline was lost.
                role = (
                    r"(?:Le\s+(?:Client|Prestataire|Vendeur|Bailleur|Locataire)"
                    r"|L['’](?:Acheteur|Entrepreneur)"
                    r"|The\s+(?:Client|Service\s+Provider|Provider|Seller|Buyer"
                    r"|Lessor|Lessee|Contractor)"
                    r"|الطرف\s+(?:الأول|الثاني))"
                )

                signature_patterns = [

                    r"\n\s*Fait\s+à\b",
                    r"\n\s*Fait\s+le\b",
                    r"\n\s*Done\s+(?:at|in)\b",
                    r"\n\s*Signed\s+(?:at|in)\b",
                    r"\n\s*Signatures?\b",
                    r"\n\s*حرر\s+ب\b",
                    r"\n\s*حرر\s+في\b",
                    r"\n\s*الإمضاء\b",
                    r"\n\s*التوقيع\b",

                    # role-only line: role followed by end of line or by
                    # another role (two signatories on the same line)
                    r"\n\s*" + role + r"\s*(?=\n|$|" + role + r")",
                ]

                for pattern in signature_patterns:

                    signature_match = re.search(
                        pattern,
                        block,
                        re.I
                    )

                    if signature_match:

                        block = block[
                            :signature_match.start()
                        ].strip()

                        break

                if len(block) >= 20:

                    heading = clean_text(
                        match.group(1)
                    )

                    clauses.append(
                        {
                            "heading": heading,
                            "text": block
                        }
                    )

        return clauses
    clauses = split_clauses()

    # =========================================================
    # 9. CLAUSE FINDER
    #    Returns ONLY the relevant article/block.
    # =========================================================

    def find_clause(keyword_groups):

        # Use the normalized contract text available
        # in the outer analyse() scope.
        source_text = normalized

        # -----------------------------------------------------
        # 1. First priority: search inside identified articles
        # -----------------------------------------------------

        for clause in clauses:

            haystack = (
                clause.get("heading", "")
                + " "
                + clause.get("text", "")
            ).lower()

            for group in keyword_groups:

                if any(
                    keyword.lower() in haystack
                    for keyword in group
                ):
                    return clause.get("text", "").strip()

        # -----------------------------------------------------
        # 2. Fallback: search sentence by sentence
        # -----------------------------------------------------

        sentences = re.split(
            r"(?<=[.!؟])\s+|\n+",
            source_text
        )

        for sentence in sentences:

            sentence = sentence.strip()

            if not sentence:
                continue

            low = sentence.lower()

            for group in keyword_groups:

                if any(
                    keyword.lower() in low
                    for keyword in group
                ):
                    return sentence

        return ""

    return {
        "original_text": original_text,
        "normalized": normalized,
        "analysis_text": analysis_text,
        "detected_language": detected_language,
        "contract_type": contract_type,
        "parties": parties,
        "amounts": amounts,
        "durations": durations,
        "clauses": clauses,
        "find_clause": find_clause,
        "clean_text": clean_text,
        "unique_keep_order": unique_keep_order,
    }


if __name__ == "__main__":
    demo = """This service contract is made between Company Alpha and Company Beta.
The contract value is 15000 USD. The duration is 12 months.
The parties agree to termination conditions, liability provisions and a penalty clause."""

    ctx = extract_all(demo)
    assert ctx["detected_language"] == "English"
    assert ctx["contract_type"] == "Service / Maintenance Contract"
    assert ctx["parties"] == ["Company Alpha", "Company Beta"], ctx["parties"]
    assert any("15000" in a for a in ctx["amounts"])
    assert any("12" in d for d in ctx["durations"])
    assert callable(ctx["find_clause"])
    print("extractors self-test OK:", ctx["contract_type"], ctx["parties"], ctx["amounts"], ctx["durations"])
