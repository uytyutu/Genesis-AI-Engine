import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"d:\Games\Genesis-AI-Engine")


def mask(v):
    if v is None:
        return "NONE"
    s = str(v)
    if s.startswith("sk_test_"):
        return "sk_test***"
    if s.startswith("sk_live_"):
        return "sk_live***"
    if s.startswith("pk_test_"):
        return "pk_test***"
    if s.startswith("pk_live_"):
        return "pk_live***"
    if s.startswith("whsec"):
        return "whsec***"
    if s.startswith("pk_"):
        return "pk_***"
    if s.startswith("sk_"):
        return "sk_***"
    if s == "":
        return "EMPTY"
    return f"SET(len={len(s)})"


def load_dotenv(path: Path) -> dict:
    vals = {}
    if not path.exists():
        return vals
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        vals[k] = v
    return vals


def parse_railway_json(raw: str) -> dict:
    data = json.loads(raw)
    items = {}
    if isinstance(data, dict):
        if "variables" in data and isinstance(data["variables"], dict):
            items = data["variables"]
        else:
            items = {k: v for k, v in data.items() if not str(k).startswith("_")}
    elif isinstance(data, list):
        for row in data:
            if isinstance(row, dict) and "name" in row:
                items[row["name"]] = row.get("value")
    return items


def cmd_capture(args):
    p = subprocess.run(args, cwd=str(ROOT), capture_output=True, text=True, shell=True)
    return p.returncode, p.stdout, p.stderr


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "local-status":
        env = load_dotenv(ROOT / "dashboard" / "backend" / ".env.local")
        if not env:
            env = load_dotenv(ROOT / "dashboard" / "backend" / ".env")
        for k in sorted(env):
            ku = k.upper()
            if "STRIPE" in ku:
                print(f"LOCAL {k}={mask(env[k])}")
        sk = env.get("STRIPE_SECRET_KEY", "")
        pk = env.get("STRIPE_PUBLISHABLE_KEY", "")
        pk_src = "STRIPE_PUBLISHABLE_KEY" if pk.startswith("pk_") else ""
        for cand in [
            "STRIPE_PUBLISHABLE_KEY",
            "NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY",
            "NEXT_PUBLIC_STRIPE_KEY",
            "NEXT_PUBLIC_STRIPE",
        ]:
            if cand in env and env[cand].startswith("pk_test_"):
                pk = env[cand]
                pk_src = cand
                break
        sk_test = sk if sk.startswith("sk_test_") else ""
        if not sk_test:
            for k, v in env.items():
                if v.startswith("sk_test_"):
                    sk_test = v
                    break
        pk_test = pk if pk.startswith("pk_test_") else ""
        if not pk_test:
            for k, v in env.items():
                if v.startswith("pk_test_"):
                    pk_test = v
                    pk_src = k
                    break
        print("HAS_SK_TEST", bool(sk_test))
        print("HAS_PK_TEST", bool(pk_test))
        print("PK_SRC", pk_src or "none")
        return 0

    if action == "railway-status":
        code, out, err = cmd_capture(
            ["railway", "variables", "--service", "renewed-reprieve", "--environment", "production", "--json"]
        )
        if code != 0:
            print("RAILWAY_FAIL", code)
            print(err[:500] if err else "")
            return code
        items = parse_railway_json(out)
        for k in sorted(items):
            if "STRIPE" in k.upper():
                print(f"RAILWAY {k}={mask(items[k])}")
        print("---DONE---")
        return 0

    if action == "apply-test":
        env = load_dotenv(ROOT / "dashboard" / "backend" / ".env.local")
        if not env:
            env = load_dotenv(ROOT / "dashboard" / "backend" / ".env")
        sk_test = ""
        pk_test = ""
        for k, v in env.items():
            if v.startswith("sk_test_") and (k == "STRIPE_SECRET_KEY" or not sk_test):
                if k == "STRIPE_SECRET_KEY" or not sk_test:
                    sk_test = v
            if v.startswith("pk_test_"):
                if k in (
                    "STRIPE_PUBLISHABLE_KEY",
                    "NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY",
                    "NEXT_PUBLIC_STRIPE_KEY",
                    "NEXT_PUBLIC_STRIPE",
                ) or not pk_test:
                    if k == "STRIPE_PUBLISHABLE_KEY" or not pk_test:
                        pk_test = v
        # prefer STRIPE_SECRET_KEY if sk_test
        if env.get("STRIPE_SECRET_KEY", "").startswith("sk_test_"):
            sk_test = env["STRIPE_SECRET_KEY"]
        if env.get("STRIPE_PUBLISHABLE_KEY", "").startswith("pk_test_"):
            pk_test = env["STRIPE_PUBLISHABLE_KEY"]
        else:
            for cand in [
                "NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY",
                "NEXT_PUBLIC_STRIPE_KEY",
                "NEXT_PUBLIC_STRIPE",
            ]:
                if env.get(cand, "").startswith("pk_test_"):
                    pk_test = env[cand]
                    break
        if not sk_test or not pk_test:
            print("MISSING_KEYS", "HAS_SK_TEST", bool(sk_test), "HAS_PK_TEST", bool(pk_test))
            return 2
        print("Applying test keys (masked):", mask(sk_test), mask(pk_test))
        # Clear LIVE override first
        code, out, err = cmd_capture(
            [
                "railway",
                "variables",
                "--set",
                "STRIPE_SECRET_KEY_LIVE=",
                "--service",
                "renewed-reprieve", "--environment", "production",
            ]
        )
        print("CLEAR_LIVE_RC", code)
        if err:
            print("CLEAR_LIVE_ERR", err[:300].replace("\n", " "))
        # Set test keys - do not print values
        code2, out2, err2 = cmd_capture(
            [
                "railway",
                "variables",
                "--set",
                f"STRIPE_SECRET_KEY={sk_test}",
                "--set",
                f"STRIPE_PUBLISHABLE_KEY={pk_test}",
                "--service",
                "renewed-reprieve", "--environment", "production",
            ]
        )
        print("SET_TEST_RC", code2)
        if err2:
            # scrub any accidental secret echo
            scrubbed = err2
            for secret in (sk_test, pk_test):
                if secret and secret in scrubbed:
                    scrubbed = scrubbed.replace(secret, mask(secret))
            print("SET_TEST_ERR", scrubbed[:400].replace("\n", " "))
        if out2:
            scrubbed = out2
            for secret in (sk_test, pk_test):
                if secret and secret in scrubbed:
                    scrubbed = scrubbed.replace(secret, mask(secret))
            print("SET_TEST_OUT", scrubbed[:400].replace("\n", " "))
        return 0 if code2 == 0 else code2

    print("Usage: local-status | railway-status | apply-test")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
