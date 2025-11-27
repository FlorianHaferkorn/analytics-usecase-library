# Use Case Dictionary – Aurora Group (Synthetic Backbone)

Purpose:
- Provide a synthetic yet realistic backbone to demo core Aurora Group use cases end-to-end.
- Anchor data contracts, scopes, and configs that feed the action-ready semantic model.
- Enable repeatable regeneration of showcase data (config + notebook).

Contents:
- `synthetic_data_contract.yaml` and `synthetic_data_scope*.yaml` – source/contract definition and scope.
- `synthetic_config_core_v1.yaml` – generation settings.
- `fabric_nb_generate_backbone_core_v1.py` – generation notebook/script.
- `usecase_dictionary_template.yaml` – semantic dictionary aligning use cases, KPIs, and model objects.
- `synthetic_data_readme.md` – additional design notes.

Usage:
- Use this as the default demo data source for the Aurora showcase.
- Keep contracts and scopes in sync with KPIs/action codes and the core_action_ready model.
- When moving to a client, replace this source with the real contracts; keep the structure.
