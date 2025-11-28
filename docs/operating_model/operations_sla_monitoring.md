# Operations & SLA Monitoring

Purpose:
- Define how service levels and operational KPIs are monitored and governed in the ActionReady Analytics Framework.

Scope:
- Data pipeline SLAs (latency, freshness, completeness)
- RI/QA checks from data contracts
- Report/model health (refresh success, performance)

Practices:
- Set SLAs per domain/source; monitor with alerts and escalation paths.
- Track RI/QA asserts; investigate breaches before publishing.
- Maintain runbooks for incidents, including rollback/disable steps.

Integration:
- Link SLA metrics to operations dashboards; align with action codes for remediation.
- Review SLA performance regularly with owners; adjust contracts and capacities as needed.
