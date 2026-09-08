import json
import yaml
import pytest
from pathlib import Path
from tooling.superversion.project_package.migrations import migrate_project_package
from tooling.superversion.project_package.repository import ProjectPackageRevisionRepository, StaleProjectPackageDraftError
from tooling.superversion.project_package.discovery_transfer import transfer_discovery

ROOT = Path(__file__).resolve().parents[2]

def setup(tmp_path):
    schemas = ROOT / 'tooling/generator/schemas'
    root = migrate_project_package(ROOT / 'tooling/tests/fixtures/project_package/v1', tmp_path / 'package', schemas)
    repository = ProjectPackageRevisionRepository(tmp_path / 'repository', schemas)
    first = repository.commit(root)
    candidate = dict(type='anchor', id='objective_1', name='Reduce manual reconciliation', details='Proposed improvement', status='draft', sourceId='source_1', source='Workshop', sourceContext='Reduce manual reconciliation', evidenceStatus='quote-verified')
    source = dict(id='source_1', type='text', name='Workshop', content='Reduce manual reconciliation by reviewing exceptions.', addedAt='2026-09-07T12:00:00Z')
    payload = dict(projectId=first.project_ref, discoveryRevision='a'*64, expectedHeadRevisionHash=first.revision_hash, candidateKeys=['anchor:objective_1'], objectiveKeys=['anchor:objective_1'], rationale='Reviewed the exact source and proposed draft objective.', actor='editor@example.test', document=dict(schemaVersion=1, sources=[source], candidates=[candidate]))
    return repository, first, payload

def test_transfers_exact_sources_maps_objective_and_resets_working(tmp_path):
    repository, first, payload = setup(tmp_path)
    second = transfer_discovery(repository, payload)
    assert second.parent_revision_hash == first.revision_hash
    root = repository.checkout(tmp_path / 'check', second.revision_hash)
    manifest = yaml.safe_load((root/'package.yaml').read_text())
    assert manifest['state'] == 'working'
    opportunity = yaml.safe_load((root/next(item['path'] for item in manifest['modules'] if item['module_type']=='opportunity')).read_text())
    assert opportunity['objectives'][-1] == 'Reduce manual reconciliation'
    assert opportunity['scope_status'] == 'draft'
    dossier = json.loads((root/opportunity['source_refs'][-1]).read_text())
    assert dossier['status'] == 'proposed'
    assert dossier['sources'][0]['content'] == payload['document']['sources'][0]['content']
    assert dossier['draft_module_mappings'][0]['value'] == opportunity['objectives'][-1]
    for item in manifest['modules']:
        if item['module_type'] != 'opportunity':
            assert (root/item['path']).read_bytes() == (first.package_root/item['path']).read_bytes()

@pytest.mark.parametrize('change,message', [('project','different project'),('quote','exact verified'),('duplicate','unique'),('mapping','Only selected')])
def test_fail_closed_before_commit(tmp_path, change, message):
    repository, first, payload = setup(tmp_path)
    if change == 'project': payload['projectId']='other_project'
    if change == 'quote': payload['document']['candidates'][0]['sourceContext']='invented'
    if change == 'duplicate': payload['candidateKeys'] *= 2
    if change == 'mapping': payload['objectiveKeys']=['kpi:unknown']
    with pytest.raises(ValueError, match=message): transfer_discovery(repository,payload)
    assert repository.head().revision_hash == first.revision_hash

def test_stale_and_repeated_transfer_preserve_head(tmp_path):
    repository, first, payload = setup(tmp_path)
    second=transfer_discovery(repository,payload)
    with pytest.raises(StaleProjectPackageDraftError): transfer_discovery(repository,payload)
    payload['expectedHeadRevisionHash']=second.revision_hash
    with pytest.raises(ValueError,match='already'): transfer_discovery(repository,payload)
    assert repository.head().revision_hash==second.revision_hash

def test_dossier_only_does_not_create_objective_or_registry_definition(tmp_path):
    repository, first, payload=setup(tmp_path)
    payload['objectiveKeys']=[]
    second=transfer_discovery(repository,payload)
    manifest=yaml.safe_load((second.package_root/'package.yaml').read_text())
    for item in manifest['modules']:
        assert (second.package_root/item['path']).read_bytes()==(first.package_root/item['path']).read_bytes()
