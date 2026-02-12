# Implementation Guides

Single entry for the **procedure** from strategy to first report. Data layers: we **define Silver** via contracts; we **deliver** Gold + Semantics. Start from Silver. See `framework/strategy_operating_model/operating_model/data_layers_standard.md`.

## Tool-agnostic playbook

- **From strategy to first report:** [playbook_strategy_to_first_report.md](playbook_strategy_to_first_report.md) — Step-by-step: choose strategy pattern, select use-case pack, align **Silver** data, build semantic model (from Silver), build first report, validate. Use this before or alongside platform-specific guides.

## Platform-specific guides

Implementation guides for specific platforms live under each platform adapter.

- **Fabric / Power BI:** `implementations/microsoft_fabric_powerbi/guide/`
  - [fabric_powerbi.md](../../implementations/microsoft_fabric_powerbi/guide/fabric_powerbi.md)
  - [tmdl_best_practices.md](../../implementations/microsoft_fabric_powerbi/guide/tmdl_best_practices.md)
