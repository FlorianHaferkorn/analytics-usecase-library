/** Binary-safe browser transport for complete Project Package directories. */

import { lstat, mkdir, mkdtemp, readdir, readFile, rm, writeFile } from 'node:fs/promises';
import { dirname, join, relative, resolve, sep } from 'node:path';
import { tmpdir } from 'node:os';
import { createHash } from 'node:crypto';

export interface PackageFile {
  path: string;
  sha256: string;
  size: number;
  encoding: 'base64';
  contentBase64: string;
}

const MAX_FILES = 2_000;
const MAX_FILE_BYTES = 20 * 1024 * 1024;
const MAX_TOTAL_BYTES = 100 * 1024 * 1024;
const MAX_PATH_LENGTH = 512;
const MAX_SEGMENT_LENGTH = 255;
const BASE64 = /^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/;
const SHA256 = /^[a-f0-9]{64}$/;

function validateRelativePath(value: string): string[] {
  if (!value || value.length > MAX_PATH_LENGTH || value.includes('\\') || value.includes('\0')) {
    throw new Error(`Unsafe package file path: ${JSON.stringify(value)}`);
  }
  const parts = value.split('/');
  if (parts.some((part) => (
    !part || part.length > MAX_SEGMENT_LENGTH || part === '.' || part === '..' || part.includes(':')
  ))) {
    throw new Error(`Unsafe package file path: ${JSON.stringify(value)}`);
  }
  return parts;
}

function decodeBase64(value: string): Buffer {
  if (value.length % 4 !== 0 || !BASE64.test(value)) {
    throw new Error('Package file content is not canonical base64');
  }
  const decoded = Buffer.from(value, 'base64');
  if (decoded.length > MAX_FILE_BYTES) throw new Error('Package file exceeds size limit');
  return decoded;
}

function sha256(value: Buffer): string {
  return createHash('sha256').update(value).digest('hex');
}

export async function writePackageFiles(root: string, files: PackageFile[]): Promise<void> {
  if (!Array.isArray(files) || files.length === 0 || files.length > MAX_FILES) {
    throw new Error('Package file count is outside the allowed range');
  }
  const targetRoot = resolve(root);
  const seen = new Set<string>();
  let totalBytes = 0;
  await mkdir(targetRoot, { recursive: false });
  try {
    for (const file of files) {
      const parts = validateRelativePath(file.path);
      const normalized = parts.join('/');
      const collisionKey = normalized.toLocaleLowerCase('en-US');
      if (seen.has(collisionKey)) throw new Error(`Duplicate package file path: ${normalized}`);
      seen.add(collisionKey);
      if (file.encoding !== 'base64') throw new Error('Unsupported package file encoding');
      const content = decodeBase64(file.contentBase64);
      if (!Number.isSafeInteger(file.size) || file.size < 0 || file.size !== content.length) {
        throw new Error(`Package file size mismatch: ${normalized}`);
      }
      if (!SHA256.test(file.sha256) || file.sha256 !== sha256(content)) {
        throw new Error(`Package file hash mismatch: ${normalized}`);
      }
      totalBytes += content.length;
      if (totalBytes > MAX_TOTAL_BYTES) throw new Error('Package payload exceeds total size limit');
      const destination = resolve(targetRoot, ...parts);
      const relativePath = relative(targetRoot, destination);
      if (relativePath.startsWith(`..${sep}`) || relativePath === '..') {
        throw new Error(`Package file escapes target root: ${normalized}`);
      }
      await mkdir(dirname(destination), { recursive: true });
      await writeFile(destination, content, { flag: 'wx' });
    }
  } catch (error) {
    await rm(targetRoot, { recursive: true, force: true });
    throw error;
  }
}

export async function readPackageFiles(root: string): Promise<PackageFile[]> {
  const packageRoot = resolve(root);
  const output: PackageFile[] = [];
  let totalBytes = 0;

  async function visit(directory: string): Promise<void> {
    for (const entry of await readdir(directory, { withFileTypes: true })) {
      const path = join(directory, entry.name);
      const metadata = await lstat(path);
      if (metadata.isSymbolicLink()) throw new Error('Package directory contains a symbolic link');
      if (entry.isDirectory()) {
        await visit(path);
        continue;
      }
      if (!entry.isFile()) throw new Error('Package directory contains a non-regular file');
      if (metadata.size > MAX_FILE_BYTES) throw new Error('Package file exceeds size limit');
      totalBytes += metadata.size;
      if (totalBytes > MAX_TOTAL_BYTES) throw new Error('Package payload exceeds total size limit');
      if (output.length >= MAX_FILES) throw new Error('Package file count exceeds limit');
      const content = await readFile(path);
      output.push({
        path: relative(packageRoot, path).split(sep).join('/'),
        sha256: sha256(content),
        size: content.length,
        encoding: 'base64',
        contentBase64: content.toString('base64'),
      });
    }
  }

  await visit(packageRoot);
  return output.sort((left, right) => left.path.localeCompare(right.path, 'en'));
}

export async function withTemporaryDirectory<T>(
  prefix: string,
  callback: (directory: string) => Promise<T>,
): Promise<T> {
  const directory = await mkdtemp(join(tmpdir(), prefix));
  try {
    return await callback(directory);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
}
