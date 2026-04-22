// Build-time stub for @azure/identity.
// Replaced at runtime by serverExternalPackages when the real package is installed.
module.exports = {
  DefaultAzureCredential: class DefaultAzureCredential {
    constructor() {
      throw new Error('@azure/identity is not installed. Run: npm install @azure/identity');
    }
  },
};
