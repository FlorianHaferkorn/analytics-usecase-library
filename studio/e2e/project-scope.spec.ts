import { test, expect } from '@playwright/test';

test('project selection pins views, clears cross-project content and preserves library tools', async ({page}) => {
  test.setTimeout(120_000);
  const hashes = {alpha: 'a'.repeat(64), beta: 'b'.repeat(64)};
  const projects = ['alpha', 'beta'].map(id => ({id, name: `${id} project`, strategy_anchor:'', updated_at:''}));
  const requests: string[] = [];
  await page.route('**/api/project/list', route => route.fulfill({json:{projects}}));
  await page.route('**/api/projects/*/view*', route => {
    const url = new URL(route.request().url()); requests.push(url.pathname + url.search);
    const id = url.pathname.split('/')[3] as 'alpha' | 'beta';
    return route.fulfill({json:{ projectId:id, revision:{revision_hash:hashes[id],package_id:`package_${id}`,project_ref:id,revision:1,parent_revision_hash:null},state:'working',modules:[
      {type:'opportunity',path:'opportunity.json',environment:null,data:{scope_status:'draft',objectives:[`${id} objective`]}},
      {type:'plan',path:'plan.json',environment:null,data:{work_packages:[{id:'one',title:`${id} work`,status:'planned',effort:{value:null,unit:'hours',provenance:'unknown'}}]}},
      {type:'decision_set',path:'decisions.json',environment:null,data:{definitions:[],instances:[]}},
      ...(id === 'alpha' ? [{type:'architecture_input',path:'architecture.json',environment:null,data:{tenant:'Alpha tenant',region:'West Europe',stack:'fabric',domains:[{id:'alpha_domain',capacity:'fbalpha01',delivery_scope:'domain'}],use_cases:[{id:'alpha_uc',name:'Alpha delivery',domain_ref:'alpha_domain',architecture_detail:'Recorded scope'}]}}] : []),
    ]}});
  });
  await page.goto('/login');
  await page.getByPlaceholder('demo@aurora-group.eu').fill('demo@aurora-group.eu');
  await page.getByText('Sign in with Demo').click();
  await page.waitForURL('**/overview');
  await page.getByRole('button', {name:/Switch project/}).click();
  await page.getByRole('button', {name:/alpha project/}).click();
  await expect(page.getByRole('heading',{name:'Project overview',exact:true})).toBeVisible();
  await expect(page.getByText('alpha objective',{exact:true})).toBeVisible();
  await page.screenshot({path:test.info().outputPath('project-overview.png'),fullPage:true});
  await expect.poll(() => requests.some(r => r.includes(`alpha/view?revision=${hashes.alpha}`))).toBe(true);
  await page.reload();
  await expect(page.getByText('alpha objective',{exact:true})).toBeVisible();
  await page.getByRole('link',{name:'Blueprint',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Project architecture',exact:true})).toBeVisible();
  await expect(page.locator('.react-flow__node')).toHaveCount(2);
  await expect(page.getByRole('group',{name:/^Domain: alpha_domain/})).toBeVisible();
  await page.getByRole('button',{name:'Fit',exact:true}).click();
  await page.screenshot({path:test.info().outputPath('project-architecture.png'),fullPage:true});
  await page.getByRole('link',{name:'Overview',exact:true}).click();
  await page.getByRole('button',{name:/Switch project/}).click();
  await page.getByRole('button',{name:/beta project/}).click();
  await expect(page.getByText('beta objective',{exact:true})).toBeVisible();
  await expect(page.getByText('alpha objective',{exact:true})).toHaveCount(0);
  await page.getByRole('link',{name:'Blueprint',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Project architecture',exact:true})).toBeVisible();
  await expect(page.getByText('No architecture module recorded in this version.')).toBeVisible();
  await page.getByRole('link',{name:'Library',exact:true}).click();
  await expect(page.getByRole('navigation',{name:'Library tools'})).toBeVisible();
  await expect(page.getByText('Library · reusable definitions, not project evidence')).toBeVisible();
  await page.getByRole('link',{name:'Manage definitions',exact:true}).click();
  await expect(page).toHaveURL(/view=manage/);
  await expect(page.getByRole('heading',{name:'Library',exact:true})).toBeVisible();
  await page.screenshot({path:test.info().outputPath('scoped-library.png'),fullPage:true});
});
