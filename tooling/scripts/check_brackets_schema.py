import json, yaml, pathlib, jsonschema
repo = pathlib.Path(".")
schema = json.loads((repo / "tooling/generator/schemas/usecase_bracket.schema.json").read_text())
brackets = sorted((repo / "core/usecases/core").rglob("UseCase_Bracket.yaml"))
errors = []
for b in brackets:
    data = yaml.safe_load(b.read_text(encoding="utf-8"))
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        errors.append(f"{b.parent.name}: {e.message[:100]}")
print(f"Brackets checked: {len(brackets)}")
print(f"Validation errors: {len(errors)}")
for e in errors:
    print(" ", e)
