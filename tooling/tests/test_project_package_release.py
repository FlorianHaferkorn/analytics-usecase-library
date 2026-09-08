from pathlib import Path
import json

import pytest
import yaml

from tooling.superversion.project_package.migrations import migrate_project_package
from tooling.superversion.project_package.repository import ProjectPackageRevisionRepository
from tooling.superversion.project_package.release import release_input

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / 'tooling/generator/schemas'
FIXTURE = ROOT / 'tooling/tests/fixtures/project_package/v1'


def setup_package(tmp_path, approved=True):
    package = migrate_project_package(FIXTURE, tmp_path / 'package', SCHEMAS)
    manifest = yaml.safe_load((package / 'package.yaml').read_text(encoding='utf-8'))
    if approved:
        manifest['state'] = 'approved'
        (package / 'package.yaml').write_text(yaml.safe_dump(manifest), encoding='utf-8')
    repository = ProjectPackageRevisionRepository(tmp_path / 'repositories/project_demo', SCHEMAS)
    record = repository.commit(package)
    return repository, record


def test_release_requires_explicit_attestation_then_exports_pinned_inputs(tmp_path):
    repository, record = setup_package(tmp_path)
    with pytest.raises(ValueError, match='no explicit'):
        release_input(repository, record.project_ref, record.revision_hash)
    first = release_input(repository, record.project_ref, record.revision_hash,
                          actor='admin@example.test', rationale='Approved input package reviewed against evidence.')
    second = release_input(repository, record.project_ref, record.revision_hash)
    assert first == second
    assert first['release']['attested_by'] == 'admin@example.test'
    assert first['release']['revision_hash'] == record.revision_hash
    assert first['compiler_input']['readiness']['build_ready']
    assert first['files']
    assert first['output_type'] == 'approved_project_input_bundle'
    repository.verify()  # release records must not corrupt the strict history format


def test_release_blocks_unapproved_stale_and_cross_project(tmp_path):
    repository, record = setup_package(tmp_path, approved=False)
    for project, revision, message in [
        (record.project_ref, 'a' * 64, 'no longer HEAD'),
        ('another_project', record.revision_hash, 'does not match'),
        (record.project_ref, record.revision_hash, 'package_not_approved'),
    ]:
        with pytest.raises(ValueError, match=message):
            release_input(repository, project, revision, actor='admin@example.test', rationale='Reviewed input bundle for release.')


def test_release_record_is_immutable_and_tamper_detected(tmp_path):
    repository, record = setup_package(tmp_path)
    first = release_input(repository, record.project_ref, record.revision_hash,
                          actor='admin@example.test', rationale='Approved input package reviewed against evidence.')
    repeated = release_input(repository, record.project_ref, record.revision_hash,
                             actor='other@example.test', rationale='This cannot replace the initial attestation.')
    assert repeated['release'] == first['release']
    path = repository.root.parent / 'release-attestations' / repository.root.name / f'{record.revision_hash}.json'
    value = json.loads(path.read_text())
    value['attested_by'] = 'tampered@example.test'
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match='integrity'):
        release_input(repository, record.project_ref, record.revision_hash)
