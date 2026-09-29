"""Replaceable local account adapter; no network or email verification.

Accounts identify a user of this Windows workspace, not isolated data tenants.
Passwords use salted PBKDF2; recovery secrets are returned once, never stored raw.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets
import struct
import sqlite3
import time
from pathlib import Path


class LocalAccounts:
    def __init__(self, user: Path):
        self.user = Path(user)
        self.path = self.user / "local-accounts.sqlite3"

    def _connect(self):
        for p in (self.user, self.path):
            if p.is_symlink() or getattr(p, "is_junction", lambda: False)():
                raise ValueError("ACCOUNT_UNAVAILABLE")
        self.user.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.path, timeout=10)
        try:
            db.execute("CREATE TABLE IF NOT EXISTS accounts (email TEXT PRIMARY KEY, salt TEXT NOT NULL, password TEXT NOT NULL, recovery TEXT NOT NULL, failures INTEGER NOT NULL DEFAULT 0, locked REAL NOT NULL DEFAULT 0)")
            db.execute("CREATE TABLE IF NOT EXISTS session (id INTEGER PRIMARY KEY CHECK(id=1), email TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS profiles (email TEXT PRIMARY KEY, name TEXT NOT NULL, bio TEXT NOT NULL, avatar TEXT NOT NULL)")
        except Exception:
            db.close()
            raise
        return db

    @staticmethod
    def _account(db, email):
        row = db.execute("SELECT name,bio,avatar FROM profiles WHERE email=?", (email,)).fetchone()
        return {"email": email, "local": True, "display_name": row[0] if row else email.split('@')[0], "bio": row[1] if row else "", "avatar": row[2] if row else ""}

    @staticmethod
    def _profile(payload):
        name, bio, avatar = (payload.get(k, "") for k in ("display_name", "bio", "avatar"))
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 60 or any(ord(c) < 32 for c in name):
            raise ValueError("ACCOUNT_PROFILE_INVALID")
        if not isinstance(bio, str) or len(bio) > 500 or any(ord(c) < 32 and c not in '\n\t' for c in bio):
            raise ValueError("ACCOUNT_PROFILE_INVALID")
        if not isinstance(avatar, str) or len(avatar) > 350000:
            raise ValueError("ACCOUNT_AVATAR_INVALID")
        if avatar:
            prefix = 'data:image/png;base64,'
            try:
                if not avatar.startswith(prefix): raise ValueError()
                data = base64.b64decode(avatar[len(prefix):], validate=True)
                if len(data) < 45 or data[:16] != b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR': raise ValueError()
                width, height = struct.unpack('>II', data[16:24])
                if not 1 <= width <= 512 or not 1 <= height <= 512 or data[-8:-4] != b'IEND': raise ValueError()
            except Exception as exc:
                raise ValueError("ACCOUNT_AVATAR_INVALID") from exc
        return name.strip(), bio.strip(), avatar

    @staticmethod
    def _password(password, salt):
        if not isinstance(password, str) or not 10 <= len(password) <= 256:
            raise ValueError("ACCOUNT_PASSWORD_INVALID")
        return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 600000).hex()

    def request(self, payload):
        if not isinstance(payload, dict):
            raise ValueError("ACCOUNT_INVALID")
        op = payload.get("operation")
        if op not in {"state", "register", "login", "logout", "reset", "update_profile"}:
            raise ValueError("ACCOUNT_INVALID")
        db = self._connect()
        try:
            with db:
                if op == "state":
                    row = db.execute("SELECT email FROM session WHERE id=1").fetchone()
                    return {"ok": True, "account": self._account(db, row[0]) if row else None}
                if op == "update_profile":
                    db.execute("BEGIN IMMEDIATE")
                    row = db.execute("SELECT email FROM session WHERE id=1").fetchone()
                    if not row: raise ValueError("ACCOUNT_LOGIN_REQUIRED")
                    name, bio, avatar = self._profile(payload)
                    db.execute("INSERT INTO profiles(email,name,bio,avatar) VALUES(?,?,?,?) ON CONFLICT(email) DO UPDATE SET name=excluded.name,bio=excluded.bio,avatar=excluded.avatar", (row[0], name, bio, avatar))
                    return {"ok": True, "account": self._account(db, row[0])}
                if op == "logout":
                    db.execute("DELETE FROM session")
                    return {"ok": True, "account": None}
                email = payload.get("email")
                if not isinstance(email, str) or len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email.strip()):
                    raise ValueError("ACCOUNT_EMAIL_INVALID")
                email = email.strip().casefold()
                # Serialize attempts and registration; never overwrite another account.
                db.execute("BEGIN IMMEDIATE")
                row = db.execute("SELECT salt,password,recovery,failures,locked FROM accounts WHERE email=?", (email,)).fetchone()
                if op == "register":
                    if row:
                        raise ValueError("ACCOUNT_EXISTS")
                    salt, recovery = secrets.token_hex(16), secrets.token_urlsafe(24)
                    digest = self._password(payload.get("password"), salt)
                    db.execute("INSERT INTO accounts(email,salt,password,recovery) VALUES(?,?,?,?)", (email, salt, digest, hashlib.sha256(recovery.encode()).hexdigest()))
                else:
                    if row and row[4] > time.time():
                        return {"ok": False, "message": "ACCOUNT_RETRY_LATER"}
                    if op == "login":
                        supplied = self._password(payload.get("password"), row[0] if row else "00" * 16)
                        valid = row is not None and hmac.compare_digest(supplied, row[1])
                    else:
                        code = payload.get("recovery_code", "")
                        valid = isinstance(code, str) and len(code) <= 256 and row is not None and hmac.compare_digest(hashlib.sha256(code.strip().encode()).hexdigest(), row[2])
                    if not valid:
                        if row:
                            failures = row[3] + 1
                            db.execute("UPDATE accounts SET failures=?,locked=? WHERE email=?", (failures, time.time()+60 if failures >= 5 else 0, email))
                        return {"ok": False, "message": "ACCOUNT_CREDENTIALS_INVALID"}
                    if op == "reset":
                        salt, recovery = secrets.token_hex(16), secrets.token_urlsafe(24)
                        digest = self._password(payload.get("password"), salt)
                        db.execute("UPDATE accounts SET salt=?,password=?,recovery=? WHERE email=?", (salt, digest, hashlib.sha256(recovery.encode()).hexdigest(), email))
                    db.execute("UPDATE accounts SET failures=0,locked=0 WHERE email=?", (email,))
                db.execute("INSERT INTO session(id,email) VALUES(1,?) ON CONFLICT(id) DO UPDATE SET email=excluded.email", (email,))
                result = {"ok": True, "account": self._account(db, email)}
                if op in {"register", "reset"}:
                    result["recovery_code"] = recovery
                return result
        finally:
            db.close()
