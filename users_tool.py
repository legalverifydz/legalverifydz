# -*- coding: utf-8 -*-
"""
users_tool.py -- LegalVerifyDZ
Compare the user database (legalverify.db) with the old Excel file
(users.xlsx) and, only if you ask, import the users that exist in the
Excel file but not in the database.

    python users_tool.py            -> REPORT ONLY (changes nothing)
    python users_tool.py --import   -> imports the missing users
                                       (a backup of the database is made first)

Run it from the project folder (the one containing legalverify.db).
Passwords are never printed. Output is plain ASCII on purpose, so it
displays correctly in the Windows console.
"""

import re
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
DB_FILE = HERE / "legalverify.db"
XLSX_FILE = HERE / "users.xlsx"


def safe(text):
    """ASCII-safe text for any console (non-ASCII shown as '?')."""
    return str(text if text is not None else "").encode("ascii", "replace").decode("ascii")


def norm(header):
    return re.sub(r"[^a-z0-9]", "", str(header or "").lower())


ALIASES = {
    "user_id": {"userid", "id"},
    "name": {"name", "fullname", "nom"},
    "email": {"email", "mail", "emailaddress"},
    "company": {"company", "societe", "entreprise", "organisation", "organization"},
    "password_hash": {"passwordhash", "password", "hash", "passwordhashed", "motdepasse"},
    "plan": {"plan", "offre"},
    "status": {"status", "statut"},
    "created_at": {"createdat", "created", "date", "signupdate", "datecreation"},
    "last_login": {"lastlogin", "derniereconnexion"},
}


def looks_like_hash(value):
    v = str(value or "").strip()
    return v.startswith(("bcrypt$", "sha256$")) or bool(re.fullmatch(r"[0-9a-fA-F]{64}", v))


def read_db_users():
    if not DB_FILE.exists():
        return None
    con = sqlite3.connect(DB_FILE)
    try:
        rows = con.execute(
            "SELECT user_id, name, email, plan, created_at FROM users ORDER BY created_at"
        ).fetchall()
    except sqlite3.OperationalError:
        rows = []
    con.close()
    return rows


def read_excel_users():
    if not XLSX_FILE.exists():
        return None, []
    try:
        from openpyxl import load_workbook
    except ImportError:
        print("openpyxl is not installed. Run: pip install openpyxl")
        sys.exit(1)
    wb = load_workbook(XLSX_FILE, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    if not rows:
        return [], []
    headers = [norm(h) for h in rows[0]]
    mapping = {}
    for field, names in ALIASES.items():
        for idx, h in enumerate(headers):
            if h in names and field not in mapping:
                mapping[field] = idx
    users = []
    for r in rows[1:]:
        if not any(r):
            continue
        u = {f: (r[i] if i < len(r) else None) for f, i in mapping.items()}
        users.append(u)
    return [str(h) for h in rows[0]], users


def main():
    do_import = "--import" in sys.argv

    print("=" * 60)
    print("Folder :", safe(HERE))
    db_users = read_db_users()
    if db_users is None:
        print("legalverify.db : NOT FOUND in this folder")
        db_users = []
    else:
        print("legalverify.db : found, %d user(s)" % len(db_users))
    for uid, name, email, plan, created in db_users:
        print("   %-8s %-34s %-10s %s" % (safe(uid), safe(email), safe(plan), safe(created)))

    headers, xl_users = read_excel_users()
    print("-" * 60)
    if headers is None:
        print("users.xlsx     : NOT FOUND in this folder")
        return
    print("users.xlsx     : found, %d row(s)" % len(xl_users))
    print("Columns        :", safe(", ".join(headers)))

    db_emails = {str(e).strip().lower() for _, _, e, _, _ in db_users}
    missing = [u for u in xl_users if str(u.get("email") or "").strip().lower() not in db_emails
               and str(u.get("email") or "").strip()]
    present = len(xl_users) - len(missing)
    print("In Excel AND in database      : %d" % present)
    print("In Excel but NOT in database  : %d" % len(missing))
    for u in missing:
        ok = looks_like_hash(u.get("password_hash"))
        print("   %-34s password: %s" % (safe(u.get("email")),
              "usable hash" if ok else "NOT usable (not a hash) -> would be skipped"))

    if not missing:
        print("\nNothing to import.")
        return
    if not do_import:
        print("\nREPORT ONLY. To import the users listed above run:")
        print("    python users_tool.py --import")
        return

    # ---- import (with backup)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = HERE / ("legalverify_backup_%s.db" % stamp)
    shutil.copy2(DB_FILE, backup)
    print("\nBackup created:", safe(backup.name))

    con = sqlite3.connect(DB_FILE)
    cols = {r[1] for r in con.execute("PRAGMA table_info(users)").fetchall()}
    used_ids = {r[0] for r in con.execute("SELECT user_id FROM users").fetchall()}
    next_n = len(used_ids) + 1
    imported = skipped = 0
    for u in missing:
        pw = str(u.get("password_hash") or "").strip()
        if not looks_like_hash(pw):
            skipped += 1
            continue
        uid = str(u.get("user_id") or "").strip()
        if not uid or uid in used_ids:
            while "LV-%04d" % next_n in used_ids:
                next_n += 1
            uid = "LV-%04d" % next_n
        used_ids.add(uid)
        record = {
            "user_id": uid,
            "name": str(u.get("name") or "").strip() or "-",
            "email": str(u["email"]).strip().lower(),
            "company": str(u.get("company") or "").strip(),
            "password_hash": pw,
            "plan": str(u.get("plan") or "Free").strip() or "Free",
            "status": str(u.get("status") or "Active").strip() or "Active",
            "created_at": str(u.get("created_at") or ""),
            "last_login": str(u.get("last_login") or ""),
        }
        record = {k: v for k, v in record.items() if k in cols}
        con.execute(
            "INSERT INTO users (%s) VALUES (%s)" % (",".join(record), ",".join("?" * len(record))),
            list(record.values()),
        )
        imported += 1
    con.commit()
    con.close()
    print("Imported: %d   Skipped (no usable password hash): %d" % (imported, skipped))
    print("Done. Restart the platform to see them in the Accounts page.")


if __name__ == "__main__":
    main()
