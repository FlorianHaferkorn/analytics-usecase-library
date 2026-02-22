# Deploy — Auth and Hosting

Placeholder for deployment and identity:

- **Identity proxy:** Authentik, Keycloak, or Traefik in front of the Evidence app so that only authenticated users can access it.
- **Docker Compose:** Optional stack for local or on-prem (Evidence app + proxy).
- **Audit:** All dashboard changes are in Git; no in-app telemetry required for revision trail.
