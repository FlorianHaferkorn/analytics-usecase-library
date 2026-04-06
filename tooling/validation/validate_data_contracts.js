/**
 * Validates domain data contracts under core/data_contracts/domains/.
 * Writes tooling/validation/results/contract_validation.json.
 * Exit 1 if any contract fails (used when PowerShell ConvertFrom-Yaml is not available, e.g. CI).
 * Usage: node validate_data_contracts.js [<repoRoot>]
 */
const fs = require('fs');
const path = require('path');
const yaml = require('yaml');

function main() {
  const root = process.argv[2] || process.cwd();
  const rootPath = path.isAbsolute(root) ? root : path.resolve(process.cwd(), root);
  const contractsDir = path.join(rootPath, 'core', 'data_contracts', 'domains');
  const resultsDir = path.join(rootPath, 'tooling', 'validation', 'results');
  const outPath = path.join(resultsDir, 'contract_validation.json');

  const failedContracts = [];

  if (!fs.existsSync(contractsDir)) {
    if (!fs.existsSync(resultsDir)) fs.mkdirSync(resultsDir, { recursive: true });
    const payload = { failed_contracts: [], timestamp: new Date().toISOString() };
    fs.writeFileSync(outPath, JSON.stringify(payload, null, 2), 'utf8');
    console.log('check_validate_data_contracts: no core/data_contracts/domains, skipped.');
    process.exit(0);
  }

  const files = fs.readdirSync(contractsDir).filter((f) => f.endsWith('.yaml'));
  for (const name of files) {
    const contractPath = `core/data_contracts/domains/${name}`;
    const filePath = path.join(contractsDir, name);
    const relPath = path.relative(rootPath, filePath).replace(/\\/g, '/');
    let fileFailed = false;
    try {
      const raw = fs.readFileSync(filePath, 'utf8');
      const data = yaml.parse(raw);
      if (!data || typeof data !== 'object') {
        fileFailed = true;
        console.error(`FAIL ${relPath} : not a YAML object`);
      } else {
        const hasDomain = data.domain != null;
        const hasDimension = data.dimension != null;
        const hasFact = data.fact != null;
        if (!hasDomain && !hasDimension && !hasFact) {
          fileFailed = true;
          console.error(`FAIL ${relPath} : missing domain, dimension, or fact`);
        }
        if (!fileFailed && data.dimension) {
          const dims = Array.isArray(data.dimension) ? data.dimension : [data.dimension];
          for (const d of dims) {
            if (!d || !d.name) {
              fileFailed = true;
              console.error(`FAIL ${relPath} : dimension entry missing name`);
              break;
            }
          }
        }
        if (!fileFailed && data.fact) {
          const facts = Array.isArray(data.fact) ? data.fact : [data.fact];
          for (const f of facts) {
            if (!f || !f.name) {
              fileFailed = true;
              console.error(`FAIL ${relPath} : fact entry missing name`);
              break;
            }
            if (!f.grain) {
              fileFailed = true;
              console.error(`FAIL ${relPath} : fact '${f.name}' missing grain`);
              break;
            }
          }
        }
      }
    } catch (err) {
      fileFailed = true;
      console.error(`FAIL ${relPath} : ${err.message}`);
    }
    if (fileFailed) failedContracts.push(contractPath);
  }

  if (!fs.existsSync(resultsDir)) fs.mkdirSync(resultsDir, { recursive: true });
  const payload = { failed_contracts: failedContracts, timestamp: new Date().toISOString() };
  fs.writeFileSync(outPath, JSON.stringify(payload, null, 2), 'utf8');

  if (failedContracts.length > 0) {
    console.error(`check_validate_data_contracts: ${failedContracts.length} failed contract(s). Results: ${outPath}`);
    process.exit(1);
  }
  console.log(`check_validate_data_contracts: all domain contracts valid. Results: ${outPath}`);
  process.exit(0);
}

main();
