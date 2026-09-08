import {test,expect} from '@playwright/test';
import {readFile} from 'node:fs/promises';
import {unzipSync,strFromU8} from 'fflate';
import type {AutomationOutput} from '../src/lib/bridge/project-automation';
const hash='d'.repeat(64);

test.beforeEach(async({page})=>{
  let savedRun:AutomationOutput|null=null;
  await page.route('**/api/project/list',route=>route.fulfill({json:{projects:[]}}));
  await page.route('**/api/projects/*/view*',route=>{
    const id=new URL(route.request().url()).pathname.split('/')[3];
    return route.fulfill({json:{projectId:id,revision:{revision_hash:hash,package_id:'fixture',project_ref:id,revision:3,parent_revision_hash:null},state:'approved',modules:[]}});
  });
  await page.route(/\/api\/projects\/[^/]+\/automation(?:\?|$)/,route=>{
    const id=new URL(route.request().url()).pathname.split('/')[3];
    if(route.request().method()==='POST'){
      savedRun={report:{run_id:hash,created_at:'2026-09-07T15:00:00Z',actor:'fixture@example.test',project_ref:id,revision_hash:hash,status:'generated',scope:'selected_generation_only',delivery_complete:false,apply_ready:false,tenant_actions_performed:false,files:[{path:'architecture_bundle/architecture.json',sha256:hash}],limitations:['No tenant actions or acceptance'],report_sha256:hash},files:[{path:'architecture_bundle/architecture.json',content:'{}'}]};
      return route.fulfill({json:savedRun});
    }
    if(new URL(route.request().url()).searchParams.has('run'))return route.fulfill({json:savedRun});
    return route.fulfill({json:{project_ref:id,revision_hash:hash,generation_allowed:true,can_generate:true,apply_ready:false,latest_run:savedRun?.report??null,
      stages:[{id:'discovery',label:'Discovery evidence',status:'recorded',summary:'Reviewed source evidence is versioned with this Package.',blockers:[]},{id:'decisions',label:'Decisions',status:'ready',summary:'Recorded approved decision states.',blockers:[]},{id:'architecture',label:'Architecture contracts',status:'recorded',summary:'Explicit source, transformation and workspace contracts.',blockers:['Security acceptance test still required']},{id:'release',label:'Input release',status:'ready',summary:'This exact revision has an existing release attestation.',blockers:[]},{id:'verification',label:'Tenant verification',status:'unsupported',summary:'Runtime evidence is not supplied.',blockers:['Trusted execution identity and live verification required']}],
      targets:[{id:'architecture_bundle',label:'Architecture and delivery specification',status:'ready',reason:'Exact recorded contracts; no tenant changes.'},{id:'fabric_workspace_requests',label:'Fabric workspace requests',status:'blocked',reason:'Physical workspaces not recorded.'},{id:'fabric_item_requests',label:'Native Fabric item definitions',status:'blocked',reason:'Native definition parts missing.'}],
      automation_gaps:['Security and CI/CD require their own supported adapters.','No customer acceptance or live execution is inferred.']}});
  });
});

test('pinned automation run, downloads, private scenario and narrow layout',async({page})=>{
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  await page.setViewportSize({width:1440,height:1000});await page.goto('/automation');
  await expect(page.getByRole('heading',{name:'Delivery automation',exact:true})).toBeVisible();
  const run=page.getByRole('button',{name:'Run selected generation'});
  await expect(run).toBeDisabled();
  await page.getByRole('checkbox',{name:/Architecture and delivery specification/}).check();
  await page.getByRole('checkbox',{name:/Generate only these outputs/}).check();
  await expect(run).toBeEnabled();
  await expect(page.getByRole('checkbox',{name:/Native Fabric item definitions/})).toBeDisabled();
  await page.screenshot({path:test.info().outputPath('automation-desktop.png'),fullPage:true});
  const request=page.waitForRequest(r=>r.method()==='POST'&&r.url().includes('/automation'));
  await run.click();expect((await request).postDataJSON()).toEqual({revisionHash:hash,targets:['architecture_bundle'],confirmGeneration:true});
  await expect(page.getByRole('heading',{name:'Latest run for this version'})).toBeVisible();
  await expect(page.getByText('Not granted by this run',{exact:true})).toBeVisible();
  const downloaded=page.waitForEvent('download');await page.getByRole('button',{name:'Download generated ZIP'}).click();const file=await downloaded;expect(file.suggestedFilename()).toMatch(/outputs.*\.zip$/);
  const archive=unzipSync(await readFile((await file.path())!));
  expect(strFromU8(archive['architecture_bundle/architecture.json'])).toBe('{}');
  expect(JSON.parse(strFromU8(archive['run-report.json'])).revision_hash).toBe(hash);
  await page.reload();await page.getByRole('button',{name:'Run evidence',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Latest run for this version'})).toBeVisible();
  const restoredRequest=page.waitForRequest(r=>r.url().includes('/automation?')&&r.url().includes('&run='));
  const restoredDownload=page.waitForEvent('download');await page.getByRole('button',{name:'Download generated ZIP'}).click();
  expect((await restoredRequest).method()).toBe('GET');expect((await restoredDownload).suggestedFilename()).toMatch(/\.zip$/);
  await page.getByRole('button',{name:'Cost & staffing',exact:true}).click();
  await page.getByLabel('Currency code',{exact:true}).fill('EUR');
  await page.getByLabel('Planning horizon (working days)',{exact:true}).fill('20');
  await page.getByLabel('Effort contingency (%)',{exact:true}).fill('10');
  await page.getByLabel('Person 1 name',{exact:true}).fill('Consultant');
  await page.getByLabel('Person 1 hours / day',{exact:true}).fill('8');
  await page.getByLabel('Person 1 availability (%)',{exact:true}).fill('80');
  await page.getByLabel('Work 1 role',{exact:true}).fill('Data engineer');
  await page.getByLabel('Work 1 effort (hours)',{exact:true}).fill('40');
  await page.getByLabel('Work 1 cost / hour',{exact:true}).fill('50');
  await page.getByLabel('Work 1 sell rate / hour',{exact:true}).fill('100');
  await page.getByRole('button',{name:'Workflow & gates',exact:true}).click();
  await page.getByRole('button',{name:'Cost & staffing',exact:true}).click();
  await expect(page.getByLabel('Person 1 name',{exact:true})).toHaveValue('Consultant');
  await page.screenshot({path:test.info().outputPath('estimation-desktop.png'),fullPage:true});
  await page.setViewportSize({width:768,height:900});
  await expect(page.getByRole('button',{name:'Search Studio'}).locator('svg')).toBeVisible();
  await expect(page.getByRole('button',{name:'Search Studio'}).locator('kbd')).toBeHidden();
  expect(await page.locator('main').evaluate(el=>el.scrollWidth<=el.clientWidth+1)).toBe(true);
  for (const label of ['Person 1 name','Person 1 hours / day','Person 1 availability (%)','Work 1 role','Work 1 effort (hours)','Work 1 cost / hour','Work 1 sell rate / hour']) {
    const input=page.getByLabel(label,{exact:true});await expect(input).toBeVisible();
    const bounds=await input.boundingBox();expect(bounds!.x).toBeGreaterThanOrEqual(0);expect(bounds!.x+bounds!.width).toBeLessThanOrEqual(768);
  }
  await page.screenshot({path:test.info().outputPath('estimation-narrow.png'),fullPage:true});
  await page.getByRole('button',{name:'Deployment preflight',exact:true}).click();
  await expect(page.getByRole('button',{name:'Build workspace plan'})).toBeDisabled();
  await expect(page.getByRole('button',{name:/apply|deploy now/i})).toHaveCount(0);
  await page.getByRole('button',{name:'Workflow & gates',exact:true}).click();
  expect(await page.locator('main').evaluate(el=>el.scrollWidth<=el.clientWidth+1)).toBe(true);
  await page.screenshot({path:test.info().outputPath('automation-narrow.png'),fullPage:true});
  expect(errors).toEqual([]);
});
