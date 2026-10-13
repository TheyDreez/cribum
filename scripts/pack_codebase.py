import os

target_files = []
ignore_dirs = {'.git', '.venv', 'node_modules', '__pycache__', 'dist', '.pytest_cache'}
ignore_exts = {'.pyc', '.jpg', '.jpeg', '.png', '.ico', '.svg', '.db', '.log'}

for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ignore_dirs]
    for f in sorted(files):
        ext = os.path.splitext(f)[1].lower()
        if ext in ignore_exts:
            continue
        rel_path = os.path.relpath(os.path.join(root, f), '.').replace('\\', '/')
        if rel_path in ('docs/FULL_CODEBASE.md', 'package-lock.json', 'scripts/pack_codebase.py'):
            continue
        target_files.append(rel_path)

print(f"Total files to pack: {len(target_files)}")

header = "# CRIBUM / AUDITRX — MASTER CONSOLIDATED CODEBASE\n"
header += f"# Total Files: {len(target_files)}\n"
header += "# Branch: fix/peer-review-hardening\n\n"
header += "## File Manifest\n"
for tf in target_files:
    header += f"- {tf}\n"
header += "\n" + "=" * 80 + "\n\n"

content = header
for tf in target_files:
    ext_label = os.path.splitext(tf)[1].lstrip(".") or "text"
    content += f"### FILE: {tf}\n"
    content += f"```{ext_label}\n"
    with open(tf, "r", encoding="utf-8", errors="replace") as fp:
        content += fp.read()
    content += "\n```\n\n" + "-" * 80 + "\n\n"

with open("docs/FULL_CODEBASE.md", "w", encoding="utf-8") as fp:
    fp.write(content)

artifact_path = r"C:\Users\andre\.gemini\antigravity\brain\bcb952f8-d97f-4ac7-8009-31e09a18b0c4\cribum_full_codebase.md"
with open(artifact_path, "w", encoding="utf-8") as fp:
    fp.write(content)

print(f"Done! Master file written: {len(content)} chars.")
