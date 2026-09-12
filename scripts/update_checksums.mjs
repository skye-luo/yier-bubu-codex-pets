// Regenerate the checksum manifest from versioned and unignored project files.
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
const root = fileURLToPath(new URL('../', import.meta.url));
const files = [...new Set(execFileSync('git', ['ls-files', '--cached', '--others', '--exclude-standard', '-z'], { cwd: root, encoding: 'utf8' }).split('\0').filter(Boolean))]
  .filter(path => path !== 'SHA256SUMS')
  .sort();
const contents = files.map(path => `${createHash('sha256').update(readFileSync(new URL('../' + path, import.meta.url))).digest('hex')}  ./${path}`).join('\n') + '\n';
writeFileSync(new URL('../SHA256SUMS', import.meta.url), contents);
console.log(`Checksums updated for ${files.length} files.`);
