// Build-time stub for @azure/keyvault-secrets.
// Replaced at runtime by serverExternalPackages when the real package is installed.
module.exports = {
  SecretClient: class SecretClient {
    constructor() {
      throw new Error('@azure/keyvault-secrets is not installed. Run: npm install @azure/keyvault-secrets');
    }
  },
};
