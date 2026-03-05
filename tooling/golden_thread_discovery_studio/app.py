"""
Golden Thread Discovery Studio – Streamlit app.

Triple-pane: Sources (left), Discovery Chat (center), Living Tree + YAML Editor (right).
Single global state (DiscoverySession); Tree and YAML stay in sync.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

# Load .env from repo root so GOOGLE_API_KEY etc. are available
try:
    from dotenv import load_dotenv
    _env = Path(__file__).resolve().parents[2] / ".env"
    if _env.exists():
        load_dotenv(_env)
except ImportError:
    pass

from chat import call_llm, get_context_from_sources
from models import DiscoverySession, UseCaseDraft
from registry_loader import load_registry_for_studio
from serializer import draft_to_bracket_dict, draft_to_yaml, yaml_to_draft
from suggestion_parser import parse_kpi_suggestion
from url_fetcher import fetch_url_text
from validator import validate_bracket


def _html_escape(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _chat_messages_to_html(messages: List[Dict[str, str]]) -> str:
    """Render chat history as one scrollable HTML block."""
    parts = ['<div class="chat-history-scroll">']
    for msg in messages:
        role = msg.get("role") or "user"
        content = (msg.get("content") or "").strip()
        content = _html_escape(content).replace("\n", "<br/>")
        label = "Sie" if role == "user" else "Assistant"
        parts.append(f'<p><strong>{_html_escape(label)}:</strong> {content}</p>')
    parts.append("</div>")
    return "\n".join(parts)

_STUDIO_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _STUDIO_DIR.parents[1]


def _default_session() -> DiscoverySession:
    return {
        "sources": [],
        "chat_messages": [],
        "strategy_anchors": [],
        "use_cases": [],
        "catalog_snapshot": {"kpi_ids": [], "action_code_ids": []},
        "selected_use_case_id": None,
        "project_mode": "greenfield",
        "imported_artefacts": [],
        "mappings": {},
    }


def _init_session_state() -> None:
    if "discovery_session" not in st.session_state:
        st.session_state.discovery_session = _default_session()
        repo = st.session_state.get("repo_root") or _REPO_ROOT
        try:
            loaded = load_registry_for_studio(repo)
            st.session_state.discovery_session["catalog_snapshot"] = loaded["catalog_snapshot"]
        except Exception:
            pass
    if "repo_root" not in st.session_state:
        st.session_state.repo_root = _REPO_ROOT


def _session() -> DiscoverySession:
    _init_session_state()
    return st.session_state.discovery_session


def _update_session(updates: Dict[str, Any]) -> None:
    s = _session()
    for k, v in updates.items():
        s[k] = v


def _sources_list() -> List[Dict[str, Any]]:
    """Return mutable list of sources from session."""
    session = _session()
    return list(session.get("sources") or [])


def _selected_draft() -> Optional[UseCaseDraft]:
    session = _session()
    uid = session.get("selected_use_case_id")
    for uc in session.get("use_cases") or []:
        if uc.get("id") == uid:
            return uc
    return None


def _set_draft_for_use_case(use_case_id: str, draft: UseCaseDraft) -> None:
    session = _session()
    use_cases: List[UseCaseDraft] = list(session.get("use_cases") or [])
    for i, uc in enumerate(use_cases):
        if uc.get("id") == use_case_id:
            use_cases[i] = draft
            _update_session({"use_cases": use_cases})
            return
    use_cases.append(draft)
    _update_session({"use_cases": use_cases})


def render_living_tree(draft: Optional[UseCaseDraft]) -> None:
    """Render Golden Thread tree: Strategic Intent -> Strategic KPI -> Influencing KPIs -> Action Codes."""
    if not draft:
        st.info("Use Case wählen oder anlegen, um den Treiberbaum zu sehen.")
        return
    orch = draft.get("orchestration") or {}
    sk = orch.get("strategic_kpi_id") or "(none)"
    infl = orch.get("influencing_kpi_ids") or []
    acts = orch.get("action_code_ids") or []
    with st.expander("Strategic KPI", expanded=True):
        st.write(f"**{sk}**")
    with st.expander("Influencing KPIs", expanded=True):
        for k in infl:
            st.write(f"- {k}")
    with st.expander("Action Codes", expanded=True):
        for a in acts:
            st.write(f"- {a}")
    # Actionability: warn if no action code
    if not acts and sk and sk != "(none)":
        st.warning("Kein Action Code verknüpft – Zweig nicht handlungsfähig.")


def _inject_notebooklm_css() -> None:
    """CSS: strong pane separation, full-height scrollable columns, chat history scroll."""
    st.markdown(
        """
        <style>
        /* Three panes: visible border, fit viewport, scroll when overflow */
        section[data-testid="stSidebar"] + div .stColumns > div {
            border: 2px solid #555;
            border-radius: 8px;
            padding: 0.75rem;
            margin: 0 6px;
            max-height: 88vh;
            overflow-y: auto;
            background: var(--background-secondary, #0e1117);
        }
        /* Chat history as one scrollable block (messages rendered as HTML below) */
        .chat-history-scroll {
            max-height: 52vh;
            overflow-y: auto;
            padding: 0.5rem 0;
            margin-bottom: 0.5rem;
            border-bottom: 1px solid #333;
        }
        .chat-history-scroll p { margin: 0.4rem 0; line-height: 1.4; }
        .chat-history-scroll strong { color: var(--primary-color, #fafafa); }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="Golden Thread Discovery Studio", layout="wide")

    _inject_notebooklm_css()
    _init_session_state()
    repo_root = st.sidebar.text_input("Repo root", value=str(st.session_state.repo_root))
    st.session_state.repo_root = Path(repo_root) if repo_root else _REPO_ROOT

    project_mode = st.sidebar.radio("Project mode", ["greenfield", "brownfield"], index=0)
    _update_session({"project_mode": project_mode})

    st.sidebar.slider(
        "Chat input height",
        min_value=100,
        max_value=450,
        value=200,
        step=25,
        key="chat_height_slider",
    )

    # Reload registry on demand
    if st.sidebar.button("Reload registry"):
        try:
            loaded = load_registry_for_studio(Path(repo_root))
            _update_session({"catalog_snapshot": loaded["catalog_snapshot"]})
            st.sidebar.success("Registry reloaded.")
        except Exception as e:
            st.sidebar.error(str(e))

    session = _session()
    use_cases = session.get("use_cases") or []

    # Triple-pane layout (NotebookLM: Quellen | Chat | Studio)
    col_sources, col_chat, col_artifacts = st.columns([3, 4, 4])

    with col_sources:
        st.subheader("Quellen")
        # NotebookLM-style: single "Add sources" entry point
        with st.expander("+ Quellen hinzufügen", expanded=False):
            url_input = st.text_input("URL", key="source_url", placeholder="https://…", label_visibility="collapsed")
            if st.button("URL hinzufügen", key="add_url"):
                url = (url_input or "").strip()
                if url:
                    sources = _sources_list()
                    src_id = f"src_{len(sources)}"
                    sources.append({
                        "id": src_id,
                        "type": "url",
                        "name": url[:60] + ("…" if len(url) > 60 else ""),
                        "content_or_url": url,
                        "include_in_chat": True,
                    })
                    with st.spinner("URL wird geladen …"):
                        text, err = fetch_url_text(url)
                        if not err and text:
                            sources[-1]["fetched_content"] = text
                    _update_session({"sources": sources})
                    st.rerun()
            st.caption("oder Datei auswählen (wird automatisch hinzugefügt):")
            uploaded = st.file_uploader("Upload", type=["pdf", "txt", "md"], key="source_upload", label_visibility="collapsed")
            if uploaded is not None:
                raw = uploaded.getvalue()
                content_hash = hash(raw)
                added = st.session_state.get("added_file_hashes") or set()
                if content_hash not in added:
                    sources = _sources_list()
                    src_id = f"src_{len(sources)}"
                    name = uploaded.name or "document"
                    ext = (Path(name).suffix or "").lower()
                    typ = "pdf" if ext == ".pdf" else "file"
                    if ext == ".pdf":
                        content = "(PDF hochgeladen; Textextraktion in Phase 4)"
                    else:
                        try:
                            content = raw.decode("utf-8", errors="replace")
                            if len(content) > 8000:
                                content = content[:8000] + "\n… (gekürzt)"
                        except Exception:
                            content = "(binär)"
                    sources.append({
                        "id": src_id,
                        "type": typ,
                        "name": name,
                        "content_or_url": content,
                        "include_in_chat": True,
                    })
                    _update_session({"sources": sources})
                    st.session_state["added_file_hashes"] = added | {content_hash}
                    st.rerun()
        sources = _sources_list()
        included_count = sum(1 for s in sources if s.get("include_in_chat", True))
        if sources:
            st.caption(f"**{len(sources)} Quellen** · **{included_count}** in Discovery")
        st.markdown("---")
        for i, src in enumerate(sources):
            src_id = src.get("id") or f"src_{i}"
            name = src.get("name") or src_id
            typ = src.get("type") or "?"
            include = src.get("include_in_chat", True)
            url = src.get("content_or_url") if isinstance(src.get("content_or_url"), str) else ""
            is_url = url.strip().lower().startswith(("http://", "https://"))
            has_fetched = bool(src.get("fetched_content"))
            with st.container():
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.caption(f"{name}" if len(name) > 45 else name)
                with c2:
                    new_include = st.checkbox("In Discovery", value=include, key=f"include_{src_id}")
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if is_url and st.button("Inhalt laden" if not has_fetched else "Inhalt neu laden", key=f"fetch_{src_id}"):
                        with st.spinner("Lade …"):
                            text, err = fetch_url_text(url)
                        if err:
                            st.error(err)
                        else:
                            sources = _sources_list()
                            for s in sources:
                                if (s.get("id") or "") == src_id:
                                    s["fetched_content"] = text
                                    break
                            _update_session({"sources": sources})
                            st.success("Inhalt geladen.")
                            st.rerun()
                with btn_col2:
                    if st.button("Löschen", key=f"remove_{src_id}"):
                        new_sources = [s for s in _sources_list() if (s.get("id") or "") != src_id]
                        _update_session({"sources": new_sources})
                        st.rerun()
                if new_include != include:
                    sources = _sources_list()
                    for s in sources:
                        if (s.get("id") or "") == src_id:
                            s["include_in_chat"] = new_include
                            break
                    _update_session({"sources": sources})
                    st.rerun()
                if is_url and has_fetched:
                    st.caption("✓ Inhalt für Chat geladen")
                elif is_url:
                    st.caption("Inhalt laden klicken. Wenn die Seite blockiert: Text im Browser kopieren und als .txt/.md hochladen.")
        if not sources:
            st.info("Noch keine Quellen. Klicke auf „+ Quellen hinzufügen“.")

    with col_chat:
        st.subheader("Chat")
        included_count = sum(1 for s in _sources_list() if s.get("include_in_chat", True))
        chat_messages = _session().get("chat_messages") or []
        if chat_messages:
            st.markdown(_chat_messages_to_html(chat_messages), unsafe_allow_html=True)
        st.caption(f"{included_count} Quellen im Kontext")
        user_input = st.text_area(
            "Chat",
            key="chat_input",
            height=st.session_state.get("chat_height_slider", 180),
            placeholder="Text eingeben … z. B. Strategie ableiten, KPIs vorschlagen …",
            label_visibility="collapsed",
        )
        if st.button("Senden", key="send_chat"):
            if not (user_input or "").strip():
                st.warning("Bitte zuerst eine Nachricht eingeben.")
            else:
                session = _session()
                messages = list(session.get("chat_messages") or [])
                messages.append({"role": "user", "content": user_input.strip()})
                _update_session({"chat_messages": messages})
                with st.spinner("Thinking…"):
                    context = get_context_from_sources(_sources_list())
                    reply = call_llm(
                        user_input.strip(),
                        context,
                        session.get("catalog_snapshot") or {},
                        chat_history=messages[:-1],
                    )
                messages.append({"role": "assistant", "content": reply})
                _update_session({"chat_messages": messages})
                st.rerun()

    with col_artifacts:
        st.subheader("Studio")
        # Use case selector at top (NotebookLM Studio has cards; we use dropdown + cards)
        use_case_ids = [uc.get("id") or "" for uc in (session.get("use_cases") or [])]
        if not use_case_ids:
            use_case_ids = [""]
        sel_id = st.selectbox(
            "Use Case",
            options=use_case_ids,
            format_func=lambda x: x or "(neu)",
            key="studio_use_case_select",
        )
        _update_session({"selected_use_case_id": sel_id if sel_id else None})
        draft = _selected_draft()
        # Vorschlag aus Chat: letzte Assistant-Nachricht parsen und als Treiberbaum-Vorschau anzeigen
        chat_messages = session.get("chat_messages") or []
        last_assistant = ""
        for m in reversed(chat_messages):
            if (m.get("role") or "") == "assistant":
                last_assistant = m.get("content") or ""
                break
        suggestion = parse_kpi_suggestion(last_assistant) if last_assistant else None
        if suggestion and (suggestion.get("strategic_kpi_id") or suggestion.get("influencing_kpi_ids") or suggestion.get("action_code_ids")):
            with st.expander("Vorschlag aus Chat → Treiberbaum", expanded=True):
                sk = suggestion.get("strategic_kpi_id") or "(keine)"
                inf = suggestion.get("influencing_kpi_ids") or []
                acts = suggestion.get("action_code_ids") or []
                st.markdown(f"**Strategic KPI:** {sk}")
                st.markdown("**Influencing KPIs:** " + (", ".join(inf) if inf else "(keine)"))
                st.markdown("**Action Codes:** " + (", ".join(acts) if acts else "(keine)"))
                st.caption("So würde der Werttreiberbaum aussehen. Übernehmen übernimmt in den ausgewählten Use Case.")
                if st.button("Vorschlag in Treiberbaum übernehmen", key="apply_suggestion"):
                    if not draft:
                        st.warning("Zuerst Use Case anlegen oder auswählen.")
                    else:
                        orch = dict(draft.get("orchestration") or {})
                        orch["strategic_kpi_id"] = sk if sk != "(keine)" else ""
                        orch["influencing_kpi_ids"] = inf
                        orch["action_code_ids"] = acts
                        draft = dict(draft)
                        draft["orchestration"] = orch
                        _set_draft_for_use_case(draft.get("id") or "", draft)
                        st.success("Treiberbaum aktualisiert.")
                        st.rerun()
        if draft:
            status = draft.get("status") or "draft"
            st.caption(f"Status: **{status}**")
            if st.button("Freigeben" if status == "draft" else "Zurück auf Entwurf", key="approve_toggle"):
                new_status = "approved" if status == "draft" else "draft"
                draft["status"] = new_status
                _set_draft_for_use_case(draft.get("id") or "", draft)
                st.success(f"Status: {new_status}.")
                st.rerun()
        with st.expander("Living Tree (Treiberbaum)", expanded=True):
            render_living_tree(draft)
        if draft:
            orch = draft.get("orchestration") or {}
            sk = orch.get("strategic_kpi_id") or ""
            inf = orch.get("influencing_kpi_ids") or []
            if sk or inf:
                with st.expander("Factsheet-Vorschau", expanded=False):
                    st.caption("Kernaussage (für Business Factsheet):")
                    title = draft.get("title") or "Use Case"
                    st.markdown(f"**{title}**")
                    if sk:
                        st.markdown(f"- Strategische KPI: `{sk}`")
                    for k in inf[:5]:
                        st.markdown(f"- Beeinflussende KPI: `{k}`")
                    if len(inf) > 5:
                        st.caption(f"… und {len(inf) - 5} weitere.")
        with st.expander("YAML-Editor", expanded=True):
            current_yaml = draft_to_yaml(draft) if draft else "# Use Case wählen oder neu anlegen\n"
            yaml_text = st.text_area("YAML", value=current_yaml, height=280, key="yaml_editor", label_visibility="collapsed")

        if st.button("YAML in State übernehmen"):
            if not yaml_text.strip():
                st.warning("Bitte zuerst YAML eingeben.")
            else:
                parsed, err = yaml_to_draft(yaml_text, status=draft.get("status", "draft") if draft else "draft")
                if err:
                    st.error(err)
                else:
                    valid, errors = validate_bracket(draft_to_bracket_dict(parsed) if parsed else {})  # type: ignore[arg-type]
                    if not valid and errors:
                        st.error("Validierung fehlgeschlagen: " + "; ".join(errors))
                    elif parsed:
                        uc_id = parsed.get("id") or "NEW-001"
                        _set_draft_for_use_case(uc_id, parsed)
                        _update_session({"selected_use_case_id": uc_id})
                        st.success("State aus YAML übernommen.")
                        st.rerun()

        # Add new use case (NotebookLM-style: "Notiz hinzufügen" / new artifact)
        if st.button("Neuen Use-Case-Entwurf anlegen"):
            use_cases = _session().get("use_cases") or []
            new_id = "NEW-001"
            for uc in use_cases:
                existing = uc.get("id")
                if existing and existing.startswith("NEW-"):
                    n = existing.replace("NEW-", "").split("-")[0]
                    try:
                        new_id = f"NEW-{int(n) + 1:03d}"
                    except ValueError:
                        pass
            new_draft: UseCaseDraft = {
                "schema_version": "2.0",
                "id": new_id,
                "title": "New Use Case",
                "domain": "Commercial",
                "governance": {"owner_role": "", "steward_role": ""},
                "orchestration": {
                    "strategic_kpi_id": "",
                    "influencing_kpi_ids": [],
                    "action_code_ids": [],
                },
                "value_driver_model": {"formula": "", "impact_direction": "maximize"},
                "ux_layout_rules": {
                    "report_structure": "2-Page-Lead",
                    "page_1_summary": {"title": "", "component_3s": {"kpi_id": "", "visual_type": "kpi_card"}, "component_30s": []},
                    "page_2_execution": {
                        "title": "",
                        "component_300s": {
                            "evidence_grain": "",
                            "evidence_columns": [],
                            "action_panel": True,
                            "payload_mode": "full",
                        },
                    },
                },
                "documentation": {"business_factsheet": "./Business_Factsheet.md"},
                "status": "draft",
            }
            _set_draft_for_use_case(new_id, new_draft)
            _update_session({"selected_use_case_id": new_id})
            st.success(f"{new_id} angelegt. Im Dropdown wählen und YAML bearbeiten.")
            st.rerun()

        st.divider()
        st.caption("Export")
        if st.button("Pre-Export-Gate ausführen", key="pre_export_gate"):
            import subprocess
            import sys
            repo = Path(repo_root)
            script = repo / "tooling" / "ontology" / "registry_builder.py"
            if script.exists():
                r = subprocess.run(
                    [sys.executable, str(script), "--strict"],
                    cwd=str(repo),
                    capture_output=True,
                    text=True,
                )
                if r.returncode == 0:
                    st.success("Pre-Export-Gate bestanden.")
                else:
                    st.error("Pre-Export-Gate fehlgeschlagen:\n" + (r.stderr or r.stdout or ""))
            else:
                st.warning("Registry-Builder nicht gefunden. Bracket manuell prüfen.")
        export_path = st.text_input("Exportpfad (relativ zum Repo)", value="core/usecases/core", key="export_path")
        if st.button("Ausgewählten Use Case ins Repo exportieren", key="export_btn"):
            d = _selected_draft()
            if not d:
                st.error("Bitte einen Use Case zum Export auswählen.")
            else:
                valid, errs = validate_bracket(draft_to_bracket_dict(d))
                if not valid and errs:
                    st.error("Validierung fehlgeschlagen: " + "; ".join(errs))
                else:
                    repo = Path(repo_root)
                    uc_id = d.get("id") or "NEW-001"
                    title = (d.get("title") or "New_Use_Case").replace(" ", "_").replace("-", "_")[:40]
                    dir_name = f"{uc_id}_{title}"
                    out_dir = repo / export_path.strip().rstrip("/") / dir_name
                    out_dir.mkdir(parents=True, exist_ok=True)
                    out_file = out_dir / "UseCase_Bracket.yaml"
                    out_file.write_text(draft_to_yaml(d), encoding="utf-8")
                    st.success(f"Exportiert nach {out_file.relative_to(repo)}.")


if __name__ == "__main__":
    main()
