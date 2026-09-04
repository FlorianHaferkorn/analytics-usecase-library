import { mkdtemp, readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import { afterEach, describe, expect, it } from 'vitest';

import {
  readPackageFiles,
  withTemporaryDirectory,
  writePackageFiles,
} from '@/lib/project-package/package-files';

const cleanup: string[] = [];
afterEach(async () => {
  const { rm } = await import('node:fs/promises');
  await Promise.all(cleanup.splice(0).map((path) => rm(path, { recursive: true, force: true })));
});

describe('Project Package file transport', () => {
  it('round-trips text and binary files deterministically', async () => {
    const parent = await mkdtemp(join(tmpdir(), 'package-files-test-'));
    cleanup.push(parent);
    const root = join(parent, 'draft');
    const transport = (path: string, content: Buffer) => ({
      path,
      sha256: createHash('sha256').update(content).digest('hex'),
      size: content.length,
      encoding: 'base64' as const,
      contentBase64: content.toString('base64'),
    });
    const files = [
      transport('assets/icon.bin', Buffer.from([0, 1, 2, 255])),
      transport('package.yaml', Buffer.from('schema_version: 2.0.0\n')),
    ];
    await writePackageFiles(root, files);

    expect(await readPackageFiles(root)).toEqual(files);
    expect([...await readFile(join(root, 'assets', 'icon.bin'))]).toEqual([0, 1, 2, 255]);
  });

  it.each(['../outside', '/absolute', 'C:/absolute', 'nested\\windows']) (
    'rejects unsafe path %s and cleans the partial draft',
    async (path) => {
      const parent = await mkdtemp(join(tmpdir(), 'package-files-test-'));
      cleanup.push(parent);
      const root = join(parent, 'draft');
      await expect(writePackageFiles(root, [{
        path,
        sha256: createHash('sha256').digest('hex'),
        size: 0,
        encoding: 'base64',
        contentBase64: '',
      }])).rejects.toThrow(
        'Unsafe package file path',
      );
      await expect(readFile(root)).rejects.toThrow();
    },
  );

  it('rejects duplicate paths and malformed base64', async () => {
    const parent = await mkdtemp(join(tmpdir(), 'package-files-test-'));
    cleanup.push(parent);
    await expect(writePackageFiles(join(parent, 'duplicate'), [
      { path: 'package.yaml', sha256: createHash('sha256').digest('hex'), size: 0, encoding: 'base64', contentBase64: '' },
      { path: 'PACKAGE.yaml', sha256: createHash('sha256').digest('hex'), size: 0, encoding: 'base64', contentBase64: '' },
    ])).rejects.toThrow('Duplicate');
    await expect(writePackageFiles(join(parent, 'invalid'), [
      { path: 'package.yaml', sha256: '0'.repeat(64), size: 1, encoding: 'base64', contentBase64: '**not-base64**' },
    ])).rejects.toThrow('canonical base64');
  });

  it('rejects declared size and digest mismatches', async () => {
    const parent = await mkdtemp(join(tmpdir(), 'package-files-test-'));
    cleanup.push(parent);
    const contentBase64 = Buffer.from('content').toString('base64');
    await expect(writePackageFiles(join(parent, 'size'), [{
      path: 'package.yaml', sha256: '0'.repeat(64), size: 999, encoding: 'base64', contentBase64,
    }])).rejects.toThrow('size mismatch');
    await expect(writePackageFiles(join(parent, 'hash'), [{
      path: 'package.yaml', sha256: '0'.repeat(64), size: 7, encoding: 'base64', contentBase64,
    }])).rejects.toThrow('hash mismatch');
  });

  it('always removes its temporary directory', async () => {
    let captured = '';
    await expect(withTemporaryDirectory('package-files-test-', async (directory) => {
      captured = directory;
      throw new Error('expected failure');
    })).rejects.toThrow('expected failure');
    await expect(readFile(captured)).rejects.toThrow();
  });
});
