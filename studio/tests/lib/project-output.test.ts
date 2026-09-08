// @vitest-environment node
import {describe,expect,it} from 'vitest';
import {unzipSync,strFromU8} from 'fflate';
import {projectOutputZip} from '@/lib/delivery/project-output';
import type {AutomationOutput} from '@/lib/bridge/project-automation';
function fixture(paths=['fabric_item_requests/fabric/items/model.request.json']):AutomationOutput {
  return {report:{project_ref:'alpha',revision_hash:'a'.repeat(64),files:paths.map(path=>({path,sha256:'b'.repeat(64)}))} as AutomationOutput['report'],files:paths.map(path=>({path,content:'{"displayName":"model"}'}))};
}
describe('Generated project ZIP',()=>{
  it('preserves native request folders and includes the run report',()=>{
    const output=fixture();const zip=unzipSync(projectOutputZip(output));
    expect(strFromU8(zip[output.files[0].path])).toBe(output.files[0].content);
    expect(JSON.parse(strFromU8(zip['run-report.json'])).project_ref).toBe('alpha');
  });
  it('rejects mismatched manifests, Windows paths and case collisions',()=>{
    const output=fixture();output.report.files=[];expect(()=>projectOutputZip(output)).toThrow();
    for(const paths of [['fabric_item_requests/C:/x'],['fabric_item_requests/../../x'],['fabric_item_requests/x','fabric_item_requests/X']])expect(()=>projectOutputZip(fixture(paths))).toThrow();
  });
});
