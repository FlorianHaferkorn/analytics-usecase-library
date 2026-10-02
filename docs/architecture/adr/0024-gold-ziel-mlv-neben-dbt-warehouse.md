# ADR-0024 — Gold-Ziel je Domäne: Lakehouse (empfohlen), MLV, Warehouse (Option)

| Feld | Wert |
|---|---|
| Status | **Accepted** (01.10.2026), **Nachtrag 02.10.2026** (§8: Lakehouse empfohlen, Werte umbenannt) |
| Entscheider | Florian Haferkorn (Entscheidung 01.10.2026: „ALUCA bekommt alle neuen Meridian-Optionen samt MLV-Pfad“; Entscheidung 02.10.2026: „Lakehouse ist die Empfehlung, Warehouse bleibt eine wählbare Option“) |
| Dateiname | bleibt `0024-gold-ziel-mlv-neben-dbt-warehouse.md` (Links aus `_INDEX.md`, `adr/README.md`, Orchestrator-README und der Fehlermeldung in `arch_targets/fabric.py`); der Titel ist maßgeblich |
| Kontext | FabCon-Europe-Nachzug (`internal/project_mgmt/FABRIC_FABCON_EU_2026_PLAN.md`, Nachmessung 01.10.2026): der Spiegel trägt `emit_mlv`, `tooling/superversion/arch_targets/fabric.py` rief ihn nicht auf |
| Betrifft | `tooling/generator/schemas/architecture_blueprint_inputs.schema.json` (neu) · `tooling/superversion/architecture_blueprint.py` (`validate_inputs`, `gold_targets`) · `tooling/superversion/arch_targets/fabric.py` · `tooling/superversion/architecture_blueprint_cli.py` · `tooling/superversion/_dataarch_vendor.py` (`PUBLIC_API`) · `tooling/generator/export_governed_catalog.py` (Feld `key`) · `showcases/aurora_group/architecture/aurora_architecture_inputs.json` |
| Bezug | Meridian D-529 (MLV-Refresh braucht einen Auslöser) · Meridian D-621 (MLV-Zeitplan als Option, Graph-Zeitplan) · Meridian D-622 (Gold-Ladeform bei Direct Lake: append-freundlich) · ADR-0005/SHARED_SUBSTANCE.md Klasse A (Spiegel) · ADR-0015 (Architecture-Blueprint-Schicht) |
| Nummer | 0022 und 0023 sind auf offenen Branches vergeben (`runde/2026-10-01-adr-authn-authz`, `claude/fabric-knowledge-management-dlru9d`); diese ADR nimmt deshalb 0024 |

## 1. Kontext

Gold entsteht in ALUCA heute auf zwei Wegen, und keiner davon ist ein MLV:

- `products/fabric/orchestrator` legt Gold in den Trf-Workspace als **Warehouse**, transformiert mit
  **dbt-fabric** (T-SQL) — `README.md`, Abschnitt „Layer-Definitionen“.
- `tooling/superversion/arch_targets/fabric.py` emittiert über die gespiegelten Meridian-Emitter
  Gold-Transformationen (`transforms/…/silver_to_gold__<p>.sql`) und Notebooks
  (`notebooks/nb_gold_<p>.Notebook`) für ein Lakehouse.

~~⚠️ UNKLAR: „dbt/Warehouse“ beschreibt den Orchestrator; das Arch-Target liefert Notebook-Transforms
ins Lakehouse. Der Wert `warehouse_dbt` steht hier für „die Gold-Strecke wie bisher“.~~
**Geklärt 02.10.2026 (§8):** der Name war falsch. Die Vorgabe heißt jetzt `lakehouse`;
`warehouse_dbt` wird als veralteter Alias mit Warnung weiter gelesen.

Der Spiegel trägt seit 01.10.2026 (Ref 498599e1) den MLV-Emitter in der korrigierten Form. Meridian
schaltet ihn mit `cli.py --emit-mlv`, `--mlv-refresh-hints`, `--mlv-zeitplan je_schicht|graph` und
`--onelake-rollen-modus gesamt|einzeln`. ALUCA hatte keinen Weg dorthin.

## 2. Optionen

| | Option | Aufwand | Risiko |
|---|---|---|---|
| (a) | dbt/Warehouse bleibt einziges Gold-Ziel (heute) | null | MLV-Fähigkeit (deklarativ, SQL-only, Optimal Refresh) bleibt im Spiegel ungenutzt; ALUCA liefert weniger als Meridian aus derselben Substanz |
| (b) | MLV als einziges Gold-Ziel | mittel | jede Domäne mit Nicht-SQL-Logik, Historie (D-551..D-553) oder SCD-Bezügen (D-559) fiele aus; MLV braucht ein schema-fähiges Lakehouse |
| (c) | **je Domäne wählbar**, Vorgabe dbt/Warehouse | mittel | gemischte Läufe: zwei Gold-Stores in einer Lieferung, je Produkt genau einer |

## 3. Entscheidung

**(c).** Jede Domäne wählt ihr Gold-Ziel; die Vorgabe bleibt die bisherige Gold-Strecke —
seit dem Nachtrag 02.10.2026 (§8) unter dem Namen `lakehouse`.

1. **Feld.** `domains[].gold_target: lakehouse | mlv | warehouse` (Stand 02.10.2026; bis dahin
   `warehouse_dbt | mlv`) in den Ableitungs-Eingaben
   (`architecture_blueprint_inputs.schema.json`, ALUCA-eigen). Das IR-Schema
   `architecture_blueprint.schema.json` ist byte-identisch mit Meridian und kennt keine solche
   Wahl; es wird **nicht** geändert. Die Wahl reist deshalb neben dem Blueprint als Target-Option
   `gold_targets={Domäne: "mlv"}` (`architecture_blueprint.gold_targets`).
2. **Verdrahtung.** `arch_targets/fabric.py` ruft für die MLV-Domänen den gespiegelten
   `emit_mlv(schemas=True, governed_catalog, refresh_hints, zeitplan)` wie Meridians `cli.py`,
   reicht bei `refresh_hints` die Hint-Schlüssel (`mlv_hint_schluessel`) als
   `emit_dq_gates(schluessel_tests=…)` weiter und baut den Apply-Plan mit
   `sql_ddl_layers=("mlv",)` und dem emittierten Baum, damit `run_sql_ddl`,
   `create_mlv_execution_definition` und `schedule_mlv_refresh` an ihren Dateien hängen.
3. **Ein Store je Produkt.** Die Gold-bauenden Emitter (`emit_transforms`, `emit_notebooks`,
   `emit_orchestration`) sehen die Gold-Produkte einer MLV-Domäne nicht. Bronze → Silber bleibt,
   die Sichten lesen Silber. Ein Produkt, das eine MLV- und eine Vorgabe-Domäne teilen, wird
   abgewiesen.
4. **Schema-fähiges Lakehouse.** Ein Lauf mit MLV-Domäne ist durchgehend schema-fähig
   (`enableSchemas=true`, `gold.<p>`), weil MLV es verlangt.
5. **OneLake-Rollen-Modus** (`gesamt|einzeln`) wird für jeden Fabric-Lauf durchgereicht, der ihn
   setzt — mit oder ohne MLV.
6. **Optionen, die nichts bewirken, werden abgewiesen** (`mlv_refresh_hints`, `mlv_zeitplan`,
   `governed_catalog` ohne MLV-Domäne; Databricks/Snowflake mit `gold_targets`).

## 4. Begründung

Belege aus der Spiegelquelle (`tooling/superversion/vendor/meridian_dataarch/provision_transforms.py`,
Docstring `emit_mlv` und Kommentare, dort mit Lesedatum) und Meridians Entscheidungen:

- **MLV GA.** MS Learn *What's new archive*, gelesen 01.10.2026: „March 2026 · Materialized Lake
  Views (Generally Available)“; Preview ist nur das PySpark-Authoring, das hier nicht genutzt wird.
  Grammatik am 01.10.2026 gegen *Spark SQL reference for materialized lake views* nachgeprüft.
- **Optimal Refresh.** Fabric wählt je Lauf Skip, inkrementell oder voll — aber nur, wenn ein
  Auslöser läuft (D-529, MS Learn *Optimal refresh*, gelesen 23.09.2026). Inkrementell wird es nur
  mit Change Data Feed auf allen Quellen und append-only Quellen im Zyklus; jede Sicht trägt
  deshalb `delta.enableChangeDataFeed = true`.
- **REFRESH_HINT ist Preview.** MS Learn *Enable optimal refresh for deletes and updates*, gelesen
  01.10.2026: `[( CONSTRAINT … )] ( REFRESH_HINT <name> UNIQUE (…) )` als **eigener** Klammerblock;
  „Fabric doesn't validate uniqueness at runtime“. Deshalb opt-in (`--mlv-refresh-hints`) und je
  Sicht mit Hint ein `unique`-Test in `dq/` (D-622).
- **Direct Lake.** Partition nur nach deklarierter Periodenspalte: „the column should have fewer
  than 100-200 distinct values“ (MS Learn *direct-lake-understand-storage*, gelesen 01.10.2026);
  „Avoid partitioning by default“ (*delta-lake-partitioning*). Die Semantikmodelle lesen Gold per
  Direct Lake (`semantic_binding.json`), ein MLV ist für sie eine Delta-Tabelle wie jede andere.
- **D-622 append-freundlich.** Overwrite löscht das Delta-Log, Direct Lake rahmt dann nicht
  inkrementell; „Prefer append-friendly update patterns where possible“ (Learn, ebd.). Für Gold
  gilt die Ladeform-Wahl je Domäne, nicht eine Vorgabe — dieselbe Logik wie hier beim Gold-Ziel.
- **Gegen (a):** dieselbe gespiegelte Substanz, in ALUCA unerreichbar. **Gegen (b):** MLV hält
  keine Historie (D-551..D-553) und führt SCD-Bezugsspalten nicht (D-559); der Emitter schreibt
  das als BEFUND in die DDL. Eine Vorgabe MLV würde diese Domänen still schlechter stellen.

## 5. Folgen

- Ohne `gold_target: mlv` ändert sich nichts. Gemessen 01.10.2026: Render der Fixture aus
  `test_architecture_blueprint_fabric.py` vorher/nachher 126 Dateien, sha256 je Datei identisch;
  Aurora-Eingaben ohne `gold_target` auf `HEAD` (Worktree) und auf dem Branch je 149 Dateien,
  identisch.
- Mit MLV: `fabric/mlv/<domäne>/<p>.mlv.sql`, `mlv/_MLV.md`, `mlv/refresh_schedule.json`
  (+ `execution_definition.json` bei `graph`), bei Hints `dq/` mit `unique`-Tests.
- Der gespiegelte Apply-Plan nimmt die DDL-Schicht **je Lauf**, nicht je Domäne: in gemischten
  Läufen schreibt er `run_sql_ddl` auch für die Gold-Produkte der Vorgabe-Domänen, auf nie
  emittierte Sichten. ALUCA ändert den Spiegel nicht; das Runbook nennt diese Schritte zum
  Streichen. Gehört als Änderung nach Meridian (`build_apply_plan`, DDL-Schicht je Domäne).
- Der Apply-Plan erhält den emittierten Baum nur, wenn eine der neuen Optionen gesetzt ist. Der
  Vorgabelauf bleibt ohne Artefaktspalte, wie bisher (siehe „Nicht entschieden“).
- Der exportierte Governed Catalog trägt jetzt `key` (Spalten mit `role: key` im Vertrag) — ohne
  ihn fand der MLV-Emitter in Aurora keinen Schlüssel (`CustomerKey` endet nicht auf `_key`).

## 6. Andockstelle für Meridians Konformitätsbefunde

Meridians `conformance.py` wird in einer parallelen Meridian-Runde in die Spiegelmenge
aufgenommen. Seine MLV-Befunde (`gold_mlv_shortcut_source`, `gold_fact_full_rebuild_direct_lake`)
lesen nur den Blueprint. Eingehängt werden sie in
`tooling/superversion/architecture_blueprint_cli.run`, direkt neben `score = conformance(bp)`
(Kommentar dort), und erscheinen in `CONFORMANCE.md`. Hier wird nichts davon nachgebaut.

## 7. Nicht entschieden

- Apply-Plan mit emittiertem Baum auch im Vorgabelauf (würde die Vorgabe-Ausgabe ändern; eigene Runde).
- `gold_target` als Frage in `open_questions`/`answers` (Rückweg aus dem Fragebogen).
- MLV-Laufzeit (`--mlv-runtime`) und Ereignis-Auslöser (`--mlv-ausloeser`): bleiben Meridians Vorgabe.
- ~~Ein Gold-Ziel `warehouse_dbt` als echte Warehouse-DDL im Arch-Target (`emit_warehouse_gold`).~~
  Ersetzt durch den Wert `warehouse` (§8): im Schema gültig, im Fabric-Target abgewiesen, bis
  die drei Lücken aus §8.4 geschlossen sind.
- Orchestrator (`products/fabric/orchestrator`): Vorgabe `warehouse` bleibt, Empfehlung
  `lakehouse` steht in `config.yaml.example` (§8.5). Ob die Vorgabe umgestellt wird, entscheidet
  der erste Mandantenlauf des Lakehouse-Pfads.

## 8. Nachtrag 02.10.2026 — Lakehouse ist die Empfehlung, Warehouse eine Option

### 8.1 Entscheidung

Florian Haferkorn, 02.10.2026: **Lakehouse ist die Empfehlung, Warehouse bleibt eine wählbare
Option.** Für das Arch-Target heißt das: `gold_target` kennt `lakehouse` (Vorgabe und
Empfehlung), `mlv` und `warehouse`.

### 8.2 Belege (MS Learn, gelesen 02.10.2026)

Quellen: *Choose between Warehouse and Lakehouse* (`fabric/fundamentals/decision-guide-lakehouse-warehouse`)
und *Choose a data store* (`fabric/fundamentals/decision-guide-data-store`).

- Entwicklungsweg: „Apache Spark (Python, Scala, Spark SQL, or R): Use **Lakehouse**“ ·
  „T-SQL: Use **Warehouse**“.
- Transaktionen: „Do you need multi-table transactions? Yes: Use **Warehouse**. No: Use **Lakehouse**.“
- Datentyp: „Unstructured and structured data, or you're not sure: Use **Lakehouse**.“
- Empfohlene Nutzung Lakehouse: „Medallion lakehouse architecture with bronze, silver, and gold zones“.
- Empfohlene Nutzung Warehouse: „Enterprise data warehousing“; Warehouse-Eigenschaften „full
  multi-table ACID transactions“ und „Full DQL, DML, and DDL T-SQL support with full transaction support“.
- SQL-Analytics-Endpunkt des Lakehouse: „Read-only“, „Full DQL, no DML, and limited DDL such as
  SQL views and table-valued functions“.

**Learn empfiehlt nicht pauschal Lakehouse.** Der Leitfaden nennt sein Ergebnis selbst „a starting
point“ und entscheidet an drei Fragen. Die Empfehlung ist ALUCAs Antwort auf diese Fragen für
den eigenen Stack: (1) Entwicklung ist Spark-/Notebook-first (die gespiegelten Emitter erzeugen
Notebook-Transforms, `emit_notebooks`/`emit_transforms`); (2) Multi-Table-Transaktionen braucht
keine Gold-Strecke von ALUCA; (3) Materialized Lake Views und OneLake-Shortcuts sind
Lakehouse-Funktionen, auf denen die MLV-Strecke (§3) und die Zugriffsvereinheitlichung (P1)
aufbauen. **Direct Lake ist kein Unterscheidungsmerkmal:** Learn *Direct Lake overview* (gelesen
02.10.2026): „Direct Lake is ideal for semantic models connecting to large Fabric lakehouses,
warehouses, and other Fabric data sources with Delta tables.“ Ein Unterschied liegt bei der
Sicherheit: Schreiben über T-SQL verlangt den delegierten Modus des SQL-Endpunkts, in dem
OneLake-Sicherheitsrollen nicht greifen (Learn `onelake/security/sql-analytics-endpoint-onelake-security`,
zitiert in Meridians `build_apply_plan`/`pruefe_gold_und_sicherheit`, hier nicht nachgelesen).
Wer T-SQL-Entwicklung oder Multi-Table-Transaktionen braucht, wählt `warehouse` — das ist die
Option, nicht ein Fehlerfall.

### 8.3 Werte und Rückwärtskompatibilität

| Wert | Bedeutung | Verhalten im Fabric-Target |
|---|---|---|
| `lakehouse` | Vorgabe und Empfehlung: Delta-Tabellen im Lakehouse aus den gespiegelten Notebook-Transforms | Ausgabe byte-gleich zum Stand vor dem Feld |
| `mlv` | Materialized Lake Views im schema-fähigen Lakehouse (§3) | wie bisher |
| `warehouse` | Gold im Fabric Warehouse (T-SQL) | **abgewiesen** mit Verweis auf §8.4 — nicht halb gebaut |
| `warehouse_dbt` | veralteter Alias, gilt als `lakehouse` | gelesen mit `FutureWarning` (Eingabedatei und Target-Option) |

Warum Alias statt Abweisung: im Repo nutzt niemand `warehouse_dbt` außer der Definition, ihren
Tests und dieser Doku (`git grep` am 02.10.2026, ebenso in Meridian und Freelancing: 0 Treffer).
Der Wert war aber einen Tag lang die dokumentierte Vorgabe, und Eingabedateien außerhalb der
Repos sind nicht prüfbar. Der Alias kostet zwei Zeilen und schweigt nicht.

Gemessen 02.10.2026 (sha256 je Datei, CLI-Lauf vor und nach der Änderung): Aurora-Eingaben ohne
`gold_target` 149 Dateien, identisch. Aurora mit `Commercial → mlv` 141 Dateien, 140 identisch;
abweichend nur `render/fabric/PROVISIONING_PLAN.md` an zwei Stellen, die den Vorgabe-Namen
ausgeben (`Finance → **lakehouse**`, „they belong to `lakehouse` domains“).

### 8.4 Warum `warehouse` noch abgewiesen wird

Der Spiegel hat einen Warehouse-Gold-Emitter (`provision_transforms.emit_warehouse_gold`, dazu
`emit_warehouse_project` für das SDK-Projekt), und `build_apply_plan` kennt die DDL-Schicht
`warehouse`. Ein sauberer Gold-Pfad fehlt trotzdem an drei Stellen:

1. **Kein Laden.** `emit_warehouse_gold` schreibt `CREATE TABLE`-Hüllen; das Befüllen steht als
   Satz im Emitter („populate via CTAS/`COPY INTO` from silver“), nicht als Artefakt. Wer der
   Domäne dafür ihre Notebook-Transforms nimmt (ein Store je Produkt, §3.3), liefert leeres Gold.
2. **Kein Warehouse-Item.** `create_warehouse` entsteht in `build_apply_plan` nur mit der
   Entscheidung `PLAT-LHTOPO = gold_warehouse`; das gespiegelte `emit_apply` reicht
   `entscheidungen` nicht durch. Der Plan liefe `run_sql_ddl` gegen ein Warehouse, das niemand anlegt.
3. **Meridian selbst** führt Warehouse-Gold als eigene Gold-Familie neben den Transforms
   (`profile_emission.GOLD_FAMILIEN`) und schaltet sie per `--emit-warehouse` je Lauf, nicht je
   Domäne.

Offen, in dieser Reihenfolge: Warehouse-Ladeschritt aus Silber in Meridian (Emitter), `entscheidungen`
durch `emit_apply` (Meridian), dann Verdrahtung hier wie bei `mlv` mit `sql_ddl_layers=("warehouse",)`.

### 8.5 Orchestrator

`products/fabric/orchestrator` hat jetzt `gold_target: lakehouse | warehouse` in `config.yaml`.
`warehouse` bleibt dort Vorgabe (bestehende Konfigurationen ohne Schlüssel provisionieren
weiter ein Warehouse), `config.yaml.example` setzt die Empfehlung `lakehouse`. Der Lakehouse-Pfad
legt im Trf-Workspace ein Lakehouse an und erzeugt ein `dbt-fabricspark`-Skelett (Livy). Status
des Adapters und Begründung im Orchestrator-README, Abschnitt „Gold-Ziel“. Keiner der Pfade ist
gegen einen Mandanten gelaufen.
