// @vitest-environment node

import { describe, expect, it } from 'vitest';
import { strFromU8, unzipSync } from 'fflate';

import { buildDeliveryZip } from '@/lib/delivery/export-bundle';

describe('buildDeliveryZip', () => {
  it('preserves governed artifact paths and content', () => {
    const archive = unzipSync(buildDeliveryZip([
      { filename: 'Model.SemanticModel/definition/model.tmdl', content: 'model M\n' },
      { filename: 'Report.Report/definition/report.json', content: '{}\n' },
    ]));

    expect(strFromU8(archive['Model.SemanticModel/definition/model.tmdl'])).toBe('model M\n');
    expect(strFromU8(archive['Report.Report/definition/report.json'])).toBe('{}\n');
  });

  it.each(['../escape.txt', '/absolute.txt', 'folder//file.txt'])('rejects unsafe path %s', (filename) => {
    expect(() => buildDeliveryZip([{ filename, content: 'x' }])).toThrow(/Unsafe/);
  });

  it('rejects duplicate artifact paths instead of overwriting silently', () => {
    expect(() => buildDeliveryZip([
      { filename: 'same.txt', content: 'a' },
      { filename: 'same.txt', content: 'b' },
    ])).toThrow(/Duplicate/);
  });
});
