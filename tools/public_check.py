"""Publication guard: blocks personal data, save files and third-party material from this public repository.

Runs automatically (see .githooks/, enabled by `git config core.hooksPath .githooks`):
  pre-commit  python tools/public_check.py --staged      every file in the commit
  pre-push    python tools/public_check.py --pre-push    every commit being pushed: files, message, author/committer
CI runs `--history` on every push and pull request. Without arguments it checks the working tree (all files git
would pick up, including untracked ones).

Exit code 0 = clean, 1 = something must be fixed. To allow a new kind of file, change the rules here in the same
commit, so the exception is visible in review.
"""
import re
import subprocess
import sys

MAX_BYTES = 1_500_000
SELF = "tools/public_check.py"   # holds the patterns below, so its own text is not content-scanned

# paths that must never be published
BLOCKED_PATHS = [
    (r"(^|/)(saves|ext|evidence|out|decoded)/", "save corpus / reference checkouts / research output"),
    # images are blocked except our own artwork: the logo renders and screenshots of the viewer's own UI
    # (taken without the save thumbnail, map or item pictures; decided 2026-10-01)
    (r"^(?!assets/(logo-\d+\.png|screenshots/[\w-]+\.png|social-card\.png|apple-touch-icon\.png)$).*\.(dat|sav|bin|pkl|npy|zip|7z|rar|png|jpe?g|webp|gif|dds|tex|core|stream)$", "save, binary or image file (game assets need explicit review)"),
    (r"(^|/)catalog/game_text/", "full game text dump (downloaded by setup.sh, not redistributed)"),
    (r"localization[^/]*\.json$", "game text dump"),
    (r"steam_guide\.txt$", "copied Steam guide text"),
    (r"(^|/)catalog/sources/", "copied web articles"),
    (r"(^|/)(CLAUDE|HANDOFF|SESSION_TODO|SPOTCHECK|FINDINGS|DS2_SAVE_PROJECT)\.md$", "private research notes"),
    (r"viewer_data\.json$", "build output (embedded in viewer/index.html)"),
]

# content that must never be published (case-insensitive)
_ = "".join   # split some literals so that tooling scanning this file does not trip over them
BLOCKED_CONTENT = [
    (r"7656119\d{10}", "SteamID64"),
    (r"[A-Za-z0-9._%+-]+@(?!users\.noreply\.github\.com\b)[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}", "e-mail address"),
    (_([r"\b(vinc", r"ent|urs", r"em|justama", r"z\w*|boost", r"eroid)\b"]), "personal name / account / setup detail"),
    (r"[a-z]:[\\/]+users[\\/]", "local Windows user path"),
    (r"/c/users/|\\appdata\\|/appdata/|onedrive", "local path"),
    (r"data:image/[a-z]+;base64,[A-Za-z0-9+/]{200}", "embedded image (an example save thumbnail?)"),
    (r"claude\.ai/(code/)?artifact", "private artifact link"),
    (r"\"sample\"\s*:\s*\{", "example save embedded in the viewer (build with --no-sample)"),
]
ALLOWED_EMAIL = re.compile(r"(@users\.noreply\.github\.com|^noreply@anthropic\.com)$", re.I)

PATH_RES = [(re.compile(p, re.I), why) for p, why in BLOCKED_PATHS]
CONTENT_RES = [(re.compile(p, re.I), why) for p, why in BLOCKED_CONTENT]


def git(*args, binary=False):
    out = subprocess.run(["git", *args], capture_output=True, check=True).stdout
    return out if binary else out.decode("utf-8", "replace")


def check_blob(path, data, where):
    problems = []
    for rx, why in PATH_RES:
        if rx.search(path):
            problems.append(f"{where}{path}: blocked path ({why})")
    if len(data) > MAX_BYTES:
        problems.append(f"{where}{path}: {len(data):,} bytes, over the {MAX_BYTES:,} byte limit")
    if path != SELF:
        text = data.decode("utf-8", "replace")
        for rx, why in CONTENT_RES:
            m = rx.search(text)
            if m:
                line = text.count("\n", 0, m.start()) + 1
                problems.append(f"{where}{path}:{line}: {why}: {m.group(0)[:60]!r}")
    return problems


def check_text(label, text):
    out = []
    for rx, why in CONTENT_RES:
        m = rx.search(text)
        if m:
            out.append(f"{label}: {why}: {m.group(0)[:60]!r}")
    return out


def check_commit(sha):
    problems = []
    an, ae, cn, ce = git("show", "-s", "--format=%an%x00%ae%x00%cn%x00%ce", sha).strip().split("\0")
    for role, email in (("author", ae), ("committer", ce)):
        if not ALLOWED_EMAIL.search(email):
            problems.append(f"commit {sha[:10]}: {role} e-mail {email!r} is not a GitHub noreply address")
    msg = git("show", "-s", "--format=%B", sha)
    msg = "\n".join(l for l in msg.splitlines() if not l.startswith("Co-Authored-By: Claude"))
    problems += check_text(f"commit {sha[:10]} message", msg + "\n" + an + "\n" + cn)
    for path in git("diff-tree", "--no-commit-id", "-r", "--name-only", "--diff-filter=ACMR", "--root", sha).splitlines():
        problems += check_blob(path, git("show", f"{sha}:{path}", binary=True), f"commit {sha[:10]} ")
    return problems


def main(argv):
    problems = []
    if "--staged" in argv:
        for path in git("diff", "--cached", "--name-only", "--diff-filter=ACMR").splitlines():
            problems += check_blob(path, git("show", f":{path}", binary=True), "")
    elif "--pre-push" in argv:
        zero = "0" * 40
        for line in sys.stdin.read().splitlines():
            local_ref, local_sha, remote_ref, remote_sha = line.split()
            if local_sha == zero:
                continue   # branch deletion
            rng = local_sha if remote_sha == zero else f"{remote_sha}..{local_sha}"
            for sha in git("rev-list", rng).split():
                problems += check_commit(sha)
    elif "--history" in argv:
        for sha in git("rev-list", "--all").split():
            problems += check_commit(sha)
    else:
        for path in git("ls-files", "--cached", "--others", "--exclude-standard").splitlines():
            try:
                data = open(path, "rb").read()
            except FileNotFoundError:
                continue   # deleted in the working tree
            problems += check_blob(path, data, "")
    for p in dict.fromkeys(problems):
        print("BLOCKED", p)
    if problems:
        print(f"\npublic_check: {len(set(problems))} problem(s). Nothing may be published until they are fixed.")
        return 1
    print("public_check: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
