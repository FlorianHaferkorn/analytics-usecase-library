# Archiv: Report in der dist-Wurzel (Stand 04.09.2026)

Archiviert am 30.09.2026 (Entscheidung Florian). Herkunft: Commit `ac1c8881`
(„feat: support governed customer package imports“, 04.09.2026) legte einen
COM-001-Report direkt in `products/fabric/powerbi/dist/` ab (`definition/`,
`definition.pbir`, `dist.pbip`) statt in einem `<ID>_<Name>.Report/`-Ordner.

Gemessen 30.09.2026: kein Generator schreibt dorthin (`generate_full_report.py`
schreibt `<Name>.Report/definition/…` unter die dist-Wurzel), kein Test und keine
Ratsche zählen ihn (`test_dist_validator_ratchet.py` globbt `*.Report`), er
referenziert noch das Basis-Theme `CY25SU10` ohne Datei (vor Meridian D-587).

Nicht mehr gepflegt; Rückweg: `git mv` zurück nach `products/fabric/powerbi/dist/`.
