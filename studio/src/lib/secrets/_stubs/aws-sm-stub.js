// Build-time stub for @aws-sdk/client-secrets-manager.
// Replaced at runtime by serverExternalPackages when the real package is installed.
module.exports = {
  SecretsManagerClient: class SecretsManagerClient {
    constructor() {
      throw new Error('@aws-sdk/client-secrets-manager is not installed. Run: npm install @aws-sdk/client-secrets-manager');
    }
  },
  GetSecretValueCommand: class GetSecretValueCommand {
    constructor() {
      throw new Error('@aws-sdk/client-secrets-manager is not installed.');
    }
  },
};
