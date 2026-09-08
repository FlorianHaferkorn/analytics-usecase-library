import {test,expect} from '@playwright/test';

const hash = 'c'.repeat(64);
test.beforeEach(async ({page}) => {
  await page.route('**/api/project/list',route => route.fulfill({json:{projects:[]}}));
  await page.route('**/api/projects/*/view*',route => {
    const id = new URL(route.request().url()).pathname.split('/')[3];
    return route.fulfill({json:{projectId:id,revision:{revision_hash:hash,package_id:'fixture',project_ref:id,revision:2,parent_revision_hash:null},state:'approved',modules:[
      {type:'opportunity',data:{scope_status:'qualified',objectives:['Reduce reporting lead time'],constraints:['Daily batch only']}},
      {type:'commercial',data:{status:'assumption',currency:'EUR',estimate:{value:1000,basis_refs:['estimate_1']},authority_ref:'commercial_record'}},
      {type:'plan',data:{work_packages:[{id:'source_contract',title:'Agree source contract',status:'planned',effort:{value:2,unit:'person_days',provenance:'assumption'},role_refs:['data_owner'],decision_refs:['dec_1']}],dependencies:[]}},
      {type:'decision_set',data:{definitions:[],instances:[]}},
    ]}});
  });
  await page.route(/\/api\/projects\/[^/]+\/architecture(?:\?|$)/,route => {
    const id = new URL(route.request().url()).pathname.split('/')[3];
    if (route.request().method() === 'POST') return route.fulfill({json:{output_type:'architecture_bundle',manifest:{project_ref:id,revision_hash:hash,apply_ready:false},files:[{path:'architecture.json',content:'{}'}]}});
    return route.fulfill({json:{project_ref:id,revision_hash:hash,compiler_input_sha256:hash,architecture:{tenant:'Fixture tenant',environments:{accepted:true,recommended:['dev','test','prod']}},use_cases:[{id:'sales',name:'Sales delivery',transformations:[{engine:'SQL',rationale:'Simple projection'}]}],
      graph:{nodes:[
        {id:'src',label:'SQL.orders',kind:'source',layer:'source',use_case_ref:'sales',details:{boundary:'canonical',purpose:'Daily orders'}},
        {id:'tx',label:'clean_orders',kind:'transformation',layer:'silver',use_case_ref:'sales',details:{engine:'SQL'}},
        {id:'product',label:'clean_orders_table',kind:'data_product',layer:'silver',use_case_ref:'sales',details:{grain:'One row per order'}},
        {id:'reference',label:'Legacy sales report',kind:'reference_report',use_case_ref:'sales',details:{purpose:'Reference only'}},
      ],edges:[{id:'e1',source:'src',target:'tx',kind:'transformation',label:'Input'},{id:'e2',source:'tx',target:'product',kind:'transformation',label:'Output'}]},
      readiness:{review_ready:true,release_ready:true,apply_ready:false,blockers:['tenant_apply_and_verification_not_implemented']},
      outputs:[{id:'architecture_bundle',label:'Architecture and delivery specification',status:'ready',reason:'Recorded contracts only'},{id:'fabric_workspace_requests',label:'Fabric workspace creation request bodies',status:'blocked',reason:'No explicit physical_workspaces contract'}]}});
  });
});

test('delivery journey exposes commercial, plan and architecture without claiming staffing or deployment',async ({page}) => {
  await page.goto('/engagement');
  await expect(page.getByRole('heading',{name:'Delivery workspace',exact:true})).toBeVisible();
  await expect(page.getByRole('button',{name:'Open scope & offer',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Scope & offer',exact:true}).click();
  await expect(page.getByText('Reduce reporting lead time',{exact:true})).toBeVisible();
  await expect(page.getByText('1000 EUR',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Plan & roles',exact:true}).click();
  await expect(page.getByText('Agree source contract',{exact:true})).toBeVisible();
  await expect(page.getByText(/not named staffing assignments/)).toBeVisible();
  await page.getByRole('button',{name:'Delivery map',exact:true}).click();
  await page.getByRole('link',{name:'Open architecture',exact:true}).click();
  await expect(page.locator('.react-flow__node')).toHaveCount(3);
  await page.getByRole('link',{name:'Generate',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Release approved project inputs',exact:true})).toBeVisible();
});

test('architecture graph, full contracts and pinned output confirmation work',async ({page}) => {
  await page.setViewportSize({width:1440,height:900});
  await page.goto('/architecture');
  await expect(page.locator('.react-flow__node')).toHaveCount(3);
  await expect(page.getByRole('heading',{name:'Architecture',exact:true})).toBeVisible();
  const bounds = await page.locator('.react-flow').boundingBox();
  expect(bounds!.height).toBeGreaterThan(450);
  expect(bounds!.y).toBeLessThan(360);
  await page.screenshot({path:test.info().outputPath('architecture-desktop.png'),fullPage:true});
  await page.getByLabel('Reference reports and alternative/excluded sources').check();
  await expect(page.locator('.react-flow__node')).toHaveCount(4);
  await page.getByRole('button',{name:'Contracts & rationale',exact:true}).click();
  await page.locator('summary').filter({hasText:'Sales delivery'}).click();
  await page.locator('summary').filter({hasText:'Show transformations'}).click();
  await expect(page.getByText('Simple projection',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Build outputs',exact:true}).click();
  const generate = page.getByRole('button',{name:'Generate architecture bundle',exact:true});
  await expect(generate).toBeDisabled();
  await page.getByLabel('Generate files from this released revision only. Do not deploy.').check();
  await expect(page.getByRole('button',{name:'Generate workspace requests',exact:true})).toBeDisabled();
  const requested = page.waitForRequest(r => r.method() === 'POST' && r.url().includes('/architecture'));
  const download = page.waitForEvent('download');
  await generate.click();
  expect((await requested).postDataJSON()).toEqual({revisionHash:hash,target:'architecture_bundle',confirmGeneration:true});
  expect((await download).suggestedFilename()).toContain('architecture_bundle');
  await expect(page.getByRole('status')).toHaveText(/Nothing was applied/);
  await page.setViewportSize({width:768,height:900});
  expect(await page.locator('main').evaluate(el => el.scrollWidth <= el.clientWidth + 1)).toBe(true);
  await page.screenshot({path:test.info().outputPath('architecture-narrow.png'),fullPage:true});
});
