import copy
import hashlib
import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator, FormatChecker

from tooling.superversion.project_package.architecture_compile import compile_architecture, build_architecture_output, read_architecture
from tooling.superversion.project_package.compiler_input import build_compiler_input
from tooling.superversion.project_package.hashes import canonical_sha256
from tooling.superversion.project_package.migrations import migrate_project_package
from tooling.superversion.project_package.repository import ProjectPackageRevisionRepository
from tooling.superversion.project_package.release import release_input

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / 'tooling/generator/schemas'


def compiler():
    delivery = yaml.safe_load((ROOT / 'core/fixtures/neutral/use-case-delivery-spec/use_case_delivery.yaml').read_text(encoding='utf8'))
    architecture = {'schema_version': '2.0.0', 'stack': 'fabric', 'reference_date': '2026-09-07', 'tenant': 'Neutral tenant', 'region': 'West Europe',
        'ledger_ref': 'ledger.md', 'model_ref': 'model.json', 'blueprint_ref': 'blueprint.json', 'mapping_ref': 'mapping.json',
        'domains': [{'id':'domain_commercial', 'key':'commercial', 'capacity':'fbcommercial01', 'delivery_scope':'detailed', 'use_case_refs':['uc_revenue_demo']}],
        'use_cases': [{'id':'uc_revenue_demo', 'name':'Revenue performance', 'domain_ref':'domain_commercial', 'architecture_detail':'full'}],
        'environments': {'recommended':['dev','test','prod'], 'accepted':True, 'decision_ref':'decision_environment_model'}, 'contracts':[],
        'compiler_policy': {'version':'1', 'generated_ref':'generated', 'fail_closed_for_apply':True, 'allow_review_with_blockers':True},
        'physical_workspaces': [{'id':'workspace_gold_dev', 'name':'acme_commercial_gold_dev', 'domain_ref':'domain_commercial', 'environment':'dev',
            'capacity_id':'11111111-1111-4111-8111-111111111111', 'domain_id':'22222222-2222-4222-8222-222222222222', 'decision_refs':['decision_environment_model']}]}
    return {'package': {'project_ref':'project_demo'}, 'modules': {'architecture_input':architecture, 'use_case_delivery':delivery,
        'decision_set':{'instances':[{'id':'decision_environment_model','approval':{'state':'approved'}}]}},
        'readiness':{'build_ready':True,'blockers':[]}, 'provenance':{'module_locks':[]}}


def test_projection_exact_stable_with_no_customer_defaults():
    data = compiler()
    before = copy.deepcopy(data)
    view = compile_architecture(data, 'a'*64)
    assert view == compile_architecture(data, 'a'*64)
    assert data == before
    assert view['readiness']['apply_ready'] is False
    assert 'ws-commercial' not in json.dumps(view)
    source = next(node for node in view['graph']['nodes'] if node['id'].endswith(':source_sales_month'))
    assert source['label'] == 'enterprise_erp.published.sales_month'
    assert all(not edge['target'].endswith(':report_revenue_legacy') for edge in view['graph']['edges'])
    assert next(item for item in view['outputs'] if item['id']=='fabric_workspace_requests')['status']=='ready'


@pytest.mark.parametrize('mutation', ['reference', 'collision', 'project'])
def test_projection_rejects_invalid_relationships(mutation):
    data = compiler()
    uc = data['modules']['use_case_delivery']['use_cases'][0]
    if mutation == 'reference': uc['data_products'][0]['source_refs']=['unrelated']
    if mutation == 'collision': uc['transformations'][0]['id']=uc['data_products'][0]['id']
    if mutation == 'project': data['modules']['use_case_delivery']['project_ref']='other'
    with pytest.raises(ValueError): compile_architecture(data, 'a'*64)


@pytest.mark.parametrize('mutation', ['absent','env','domain','decision','stack','duplicate'])
def test_workspace_target_fails_closed(mutation):
    data = compiler()
    architecture = data['modules']['architecture_input']
    if mutation=='absent': architecture.pop('physical_workspaces')
    if mutation=='env': architecture['environments']['accepted']=False
    if mutation=='domain': architecture['physical_workspaces'][0]['domain_ref']='unknown'
    if mutation=='decision': data['modules']['decision_set']['instances']=[]
    if mutation=='stack': architecture['stack']='snowflake'
    if mutation=='duplicate': architecture['physical_workspaces']*=2
    view = compile_architecture(data,'a'*64)
    assert view['outputs'][1]['status']=='blocked'


def test_workspace_schema_rejects_guessed_ids():
    architecture=compiler()['modules']['architecture_input']
    validator=Draft202012Validator(json.loads((SCHEMAS/'project_architecture_input.schema.json').read_text(encoding="utf-8")),format_checker=FormatChecker())
    assert list(validator.iter_errors(architecture))==[]
    architecture['physical_workspaces'][0]['capacity_id']='<CAPACITY>'
    assert list(validator.iter_errors(architecture))


def test_released_outputs_exact_native_payload_and_hashes(monkeypatch):
    data=compiler()
    monkeypatch.setattr('tooling.superversion.project_package.architecture_compile.release_input',lambda *args: {'compiler_input':data,'release':{'record_sha256':'b'*64}})
    output=build_architecture_output(None,'project_demo','a'*64,'fabric_workspace_requests')
    files={file['path']:file['content'] for file in output['files']}
    request=json.loads(files['fabric/workspaces/workspace_gold_dev.request.json'])
    assert request=={'displayName':'acme_commercial_gold_dev','capacityId':'11111111-1111-4111-8111-111111111111','domainId':'22222222-2222-4222-8222-222222222222'}
    assert not any(path.endswith(('.ps1','.sh')) for path in files)
    for item in output['manifest']['files']:
        assert hashlib.sha256(files[item['path']].encode()).hexdigest()==item['sha256']
    docs=build_architecture_output(None,'project_demo','a'*64,'architecture_bundle')
    assert any(file['path'].endswith('Use_Case_and_Data_Architecture.md') for file in docs['files'])


def test_real_repository_missing_architecture_and_release_gates(tmp_path):
    package=migrate_project_package(ROOT/'tooling/tests/fixtures/project_package/v1',tmp_path/'package',SCHEMAS)
    manifest=yaml.safe_load((package/'package.yaml').read_text(encoding='utf8'))
    manifest['state']='approved'
    (package/'package.yaml').write_text(yaml.safe_dump(manifest),encoding='utf8')
    repo=ProjectPackageRevisionRepository(tmp_path/'repositories/project_demo',SCHEMAS)
    record=repo.commit(package)
    view=read_architecture(repo,'project_demo',record.revision_hash)
    assert not view['graph']['nodes']
    assert view['readiness']['release_ready'] is False
    assert 'architecture_input_missing' in view['readiness']['blockers']
    with pytest.raises(ValueError,match='no explicit'): build_architecture_output(repo,'project_demo',record.revision_hash,'architecture_bundle')
    release_input(repo,'project_demo',record.revision_hash,actor='test@example.test',rationale='Explicit release for neutral test input.')
    with pytest.raises(ValueError,match='Target blocked'): build_architecture_output(repo,'project_demo',record.revision_hash,'architecture_bundle')
    with pytest.raises(ValueError,match='does not match'): read_architecture(repo,'other',record.revision_hash)


def test_real_revision_to_released_architecture_specification(tmp_path):
    package=migrate_project_package(ROOT/'tooling/tests/fixtures/project_package/v1',tmp_path/'package',SCHEMAS)
    manifest=yaml.safe_load((package/'package.yaml').read_text(encoding='utf8'))
    data=compiler()
    data['modules']['architecture_input'].pop('physical_workspaces')
    for kind in ['architecture_input','use_case_delivery']:
        document=data['modules'][kind]
        relative=kind+'.yaml'
        (package/relative).write_text(yaml.safe_dump(document,sort_keys=False),encoding='utf8')
        schema=json.loads((SCHEMAS/f'project_{kind}.schema.json').read_text(encoding="utf-8"))
        manifest['modules'].append({'module_type':kind,'path':relative,'schema_id':schema['$id'],'sha256':canonical_sha256(document)})
    manifest['state']='approved'
    (package/'package.yaml').write_text(yaml.safe_dump(manifest),encoding='utf8')
    repo=ProjectPackageRevisionRepository(tmp_path/'repositories/project_demo',SCHEMAS)
    record=repo.commit(package)
    view=read_architecture(repo,'project_demo',record.revision_hash)
    assert view['graph']['nodes']
    release_input(repo,'project_demo',record.revision_hash,actor='test@example.test',rationale='Explicit release for neutral architecture input.')
    assert read_architecture(repo,'project_demo',record.revision_hash)['readiness']['release_ready'] is True
    output=build_architecture_output(repo,'project_demo',record.revision_hash,'architecture_bundle')
    assert output==build_architecture_output(repo,'project_demo',record.revision_hash,'architecture_bundle')
    assert output['manifest']['revision_hash']==record.revision_hash
    assert any('enterprise_erp.published.sales_month' in file['content'] for file in output['files'])
    assert output['manifest']['apply_ready'] is False
