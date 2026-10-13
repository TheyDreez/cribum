import os

target_files = []
ignore_dirs = {'.git', '.venv', 'node_modules', '__pycache__', 'dist', '.pytest_cache', 'test-results', 'playwright-report', 'screenshots'}
ignore_exts = {'.pyc', '.jpg', '.jpeg', '.png', '.ico', '.svg', '.db', '.sqlite3', '.log'}

for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ignore_dirs]
    for f in sorted(files):
        ext = os.path.splitext(f)[1].lower()
        if ext in ignore_exts:
            continue
        rel_path = os.path.relpath(os.path.join(root, f), '.').replace('\\', '/')
        if 'package-lock.json' in rel_path or 'FULL_CODEBASE' in rel_path or rel_path.endswith('.png'):
            continue
        target_files.append(rel_path)

target_files.sort()
print(f"Total files to pack: {len(target_files)}")

header = "# CRIBUM / AUDITRX - MASTER CONSOLIDATED CODEBASE\n\n"
header += f"**Total de Arquivos:** {len(target_files)}  \n"
header += "**Branch:** `fix/redesign-integrity`  \n"
header += "**Repositorio:** `scratch/cribum`  \n\n"
header += "## Indice Geral de Arquivos\n\n"
for tf in target_files:
    header += f"- [{tf}](#file-{tf.replace('/', '-').replace('.', '-')})\n"
header += "\n" + "=" * 80 + "\n\n"

content = header
for tf in target_files:
    ext = os.path.splitext(tf)[1].lstrip(".") or "text"
    if ext == "ts" or ext == "tsx":
        ext_label = "typescript"
    elif ext == "js" or ext == "jsx":
        ext_label = "javascript"
    elif ext == "py":
        ext_label = "python"
    elif ext == "json":
        ext_label = "json"
    elif ext == "md":
        ext_label = "markdown"
    elif ext == "yml" or ext == "yaml":
        ext_label = "yaml"
    else:
        ext_label = ext

    anchor = f"file-{tf.replace('/', '-').replace('.', '-')}"
    content += f"<a id=\"{anchor}\"></a>\n"
    content += f"### Arquivo: `{tf}`\n\n"
    content += f"```{ext_label}\n"
    with open(tf, "r", encoding="utf-8", errors="replace") as fp:
        content += fp.read()
    content += "\n```\n\n" + "-" * 80 + "\n\n"

docs_path = os.path.abspath("docs/FULL_CODEBASE.md")
with open(docs_path, "w", encoding="utf-8") as fp:
    fp.write(content)
print(f"Salvo em: {docs_path}")

artifact_path = r"C:\Users\andre\.gemini\antigravity\brain\bcb952f8-d97f-4ac7-8009-31e09a18b0c4\cribum_full_codebase.md"
with open(artifact_path, "w", encoding="utf-8") as fp:
    fp.write(content)
print(f"Salvo em artifact: {artifact_path}")

print(f"Concluído com sucesso! Tamanho final: {len(content)} caracteres.")
