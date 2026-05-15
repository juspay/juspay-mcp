"""Unit smoke test for the api-key env-file writer.

Exercises juspay_dashboard_mcp.api.api_keys._write_env_var in isolation —
no Portal, no network. Verifies create, append, in-place update (no dupes),
preservation of unrelated lines, and 0600 permissions.
"""

from __future__ import annotations

import os
import stat
import sys
import tempfile

from juspay_dashboard_mcp.api.api_keys import _write_env_var

PASS = "[OK]"
FAIL = "[FAIL]"
failures = 0


def check(label, cond, detail=""):
    global failures
    print(f"{PASS if cond else FAIL} {label}" + (f"  — {detail}" if detail else ""))
    if not cond:
        failures += 1


def read(path):
    with open(path) as f:
        return f.read()


def run():
    tmp = tempfile.mkdtemp(prefix="jmcp-envtest-")

    # 1. Create a fresh file
    p1 = os.path.join(tmp, ".env")
    info = _write_env_var(p1, "JUSPAY_API_KEY", "KEY_ONE")
    check("fresh file: created flag", info["created"] is True)
    check("fresh file: not updated-in-place", info["updated_in_place"] is False)
    check("fresh file: content", read(p1) == "JUSPAY_API_KEY=KEY_ONE\n", repr(read(p1)))
    mode = stat.S_IMODE(os.stat(p1).st_mode)
    check("fresh file: mode 0600", mode == 0o600, oct(mode))

    # 2. Append a different var — existing line preserved
    info = _write_env_var(p1, "OTHER_VAR", "abc")
    check("append: not created", info["created"] is False)
    check("append: not updated-in-place", info["updated_in_place"] is False)
    check(
        "append: both lines present",
        read(p1) == "JUSPAY_API_KEY=KEY_ONE\nOTHER_VAR=abc\n",
        repr(read(p1)),
    )

    # 3. Update JUSPAY_API_KEY in place — no duplicate line
    info = _write_env_var(p1, "JUSPAY_API_KEY", "KEY_TWO")
    check("update: updated-in-place flag", info["updated_in_place"] is True)
    content = read(p1)
    check("update: new value present", "JUSPAY_API_KEY=KEY_TWO" in content)
    check("update: old value gone", "KEY_ONE" not in content)
    check("update: exactly one JUSPAY_API_KEY line", content.count("JUSPAY_API_KEY=") == 1, content)
    check("update: OTHER_VAR preserved", "OTHER_VAR=abc" in content)

    # 4. Comment lines and unrelated content preserved
    p2 = os.path.join(tmp, "with-comments.env")
    with open(p2, "w") as f:
        f.write("# a comment\nFOO=1\n#JUSPAY_API_KEY=commented_out\nBAR=2\n")
    _write_env_var(p2, "JUSPAY_API_KEY", "KEY_NEW")
    content = read(p2)
    check("comments: comment line preserved", "# a comment" in content)
    check("comments: commented JUSPAY line untouched", "#JUSPAY_API_KEY=commented_out" in content)
    check("comments: real key appended", "JUSPAY_API_KEY=KEY_NEW" in content)
    check("comments: FOO/BAR preserved", "FOO=1" in content and "BAR=2" in content)

    # 5. Parent directory auto-created
    p3 = os.path.join(tmp, "nested", "deep", ".env")
    info = _write_env_var(p3, "JUSPAY_API_KEY", "KEY_NESTED")
    check("nested: file created with parent dirs", os.path.exists(p3) and info["created"])

    print()
    if failures:
        print(f"{FAIL} {failures} assertion(s) failed")
        sys.exit(1)
    print(f"{PASS} all env-writer checks passed")


if __name__ == "__main__":
    run()
