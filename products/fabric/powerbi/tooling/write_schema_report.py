"""write_schema_report — den Schema-Update-Report als Markdown schreiben.

Liest `internal/reviews/schema_update_report.json` (von `discover_schema_latest.py`) und
schreibt `internal/reviews/schema_update_report.md`. Exit 1, wenn die JSON fehlt oder
unlesbar ist — dann steht der Grund im Markdown.

Warum das eine Datei ist und kein `python -c "…"` im Workflow: eingebettet stand der Block
auf Spaltenposition 0 und beendete damit den YAML-Blockskalar `run: |`. Die Workflow-Datei
war dadurch **kein gueltiges YAML** — GitHub legte fuer jeden Lauf null Jobs an
(`list_workflow_jobs` -> total_count 0, gemessen 31.07.2026 an Lauf 30650634969). Ein
`python -c` mit `def`/`try` laesst sich auch nicht einfach einruecken: Pythons oberste Ebene
darf keinen Einzug haben. Als Datei ist das Problem strukturell weg — und der Code wird
testbar, statt in einer YAML-Zeichenkette zu leben.
"""
import json, pathlib, sys, datetime

report_json = pathlib.Path('internal/reviews/schema_update_report.json')
report_md = pathlib.Path('internal/reviews/schema_update_report.md')
now = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')

def write_failure(reason: str) -> None:
    report_md.write_text(
        '\n'.join([
            '# Schema Update Report',
            '',
            f'Generated: {now}',
            '',
            f'_Discovery failed: {reason}_',
        ]) + '\n',
        encoding='utf-8',
    )

if not report_json.exists() or report_json.stat().st_size == 0:
    write_failure('no JSON output file')
    sys.exit(1)

try:
    data = json.loads(report_json.read_text(encoding='utf-8'))
except json.JSONDecodeError as exc:
    write_failure(f'invalid JSON ({exc})')
    sys.exit(1)

lines = [
    '# Schema Update Report',
    '',
    f'Generated: {now}',
    '',
    '| Schema | Pinned | Latest | Status |',
    '|---|---|---|---|',
]
for item in data if isinstance(data, list) else []:
    status = 'UP-TO-DATE' if item.get('pinned') == item.get('latest') else 'UPDATE AVAILABLE'
    lines.append(
        f"| {item.get('name', '?')} | {item.get('pinned', '?')} | {item.get('latest', '?')} | {status} |"
    )
report_md.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('Schema report written.')
