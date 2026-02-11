const fs = require('fs');
const path = require('path');
const yaml = require('yaml');
const Ajv = require('ajv');
const Ajv2020 = require('ajv/dist/2020').default;

function loadYaml(filePath) {
  const raw = fs.readFileSync(filePath, 'utf8');
  return yaml.parse(raw);
}

function loadSchema(schemaPath) {
  const raw = fs.readFileSync(schemaPath, 'utf8');
  const normalized = raw.replace(/^\uFEFF/, '').replace(/\u0000/g, '');
  return JSON.parse(normalized);
}

function validateFile(ajv, schema, targetPath) {
  let data;
  try {
    data = loadYaml(targetPath);
  } catch (err) {
    return `Invalid YAML: ${targetPath} (${err.message})`;
  }
  const validate = ajv.compile(schema);
  const valid = validate(data);
  if (!valid) {
    const msg = validate.errors.map(e => `${e.instancePath || '(root)'} ${e.message}`).join('; ');
    return `Schema validation failed: ${targetPath} (${msg})`;
  }
  return null;
}

function main() {
  const [schemaPath, ...targets] = process.argv.slice(2);
  if (!schemaPath || targets.length === 0) {
    console.error('Usage: node validate_schema.js <schema.json> <file1.yaml> [file2.yaml ...]');
    process.exit(2);
  }

  const schema = loadSchema(schemaPath);
  const schemaDraft = typeof schema.$schema === 'string' ? schema.$schema : '';
  const isDraft2020 = schemaDraft.includes('2020-12');
  const ajv = isDraft2020
    ? new Ajv2020({ allErrors: true, strict: true, allowUnionTypes: true })
    : new Ajv({ allErrors: true, strict: true, allowUnionTypes: true });

  const errors = [];
  for (const target of targets) {
    const err = validateFile(ajv, schema, target);
    if (err) errors.push(err);
  }

  if (errors.length > 0) {
    errors.forEach(e => console.error(e));
    process.exit(1);
  }
}

main();
