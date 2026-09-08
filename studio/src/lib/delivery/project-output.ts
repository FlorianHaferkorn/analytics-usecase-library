import type {AutomationOutput} from '@/lib/bridge/project-automation';
import {buildDeliveryZip} from './export-bundle';

/** Preserve the generated folder layout; never require manual extraction from JSON. */
export function projectOutputZip(output:AutomationOutput):Uint8Array {
  const declared=output.report.files.map(file=>file.path);
  const actual=output.files.map(file=>file.path);
  if(declared.length!==actual.length || actual.some((path,i)=>path!==declared[i]) ||
    actual.some(path=>!path.startsWith('architecture_bundle/')&&!path.startsWith('fabric_workspace_requests/')&&!path.startsWith('fabric_item_requests/')) ||
    actual.some(path=>path.includes(':')||path.includes('\\')) ||
    new Set(actual.map(path=>path.toLowerCase())).size!==actual.length) throw new Error('Output file manifest does not match the generated bundle');
  return buildDeliveryZip([...output.files.map(file=>({filename:file.path,content:file.content})),{filename:'run-report.json',content:JSON.stringify(output.report,null,2)}],true);
}
