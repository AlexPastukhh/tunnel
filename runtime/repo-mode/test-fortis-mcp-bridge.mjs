import test from 'node:test';
import assert from 'node:assert/strict';
import {REPO_GUIDANCE, presentResponse} from './fortis-mcp-bridge.mjs';

test('initialize guidance describes the verified shared workspace volume', () => {
  assert.match(REPO_GUIDANCE, /fortis-repo-workspace ext4 volume/);
  assert.match(REPO_GUIDANCE, /\/workspace\/repos is its Repos subpath/);
  assert.match(REPO_GUIDANCE, /\/workspace\/files is its Workfiles subpath/);
  assert.match(REPO_GUIDANCE, /not independent Windows bind mounts/);
  assert.doesNotMatch(REPO_GUIDANCE, /Only these host folders are bind-mounted/);
  assert.doesNotMatch(REPO_GUIDANCE, /read-only root filesystem, no Docker socket/);
});

test('initialize response exposes the current guidance without claiming unverified hardening', () => {
  const message = {
    result: {
      capabilities: {tools: {}, resources: {}},
      serverInfo: {name: 'desktop-commander', version: '1'}
    }
  };
  const result = presentResponse(message, {method: 'initialize'});
  assert.equal(result.result.serverInfo.name, 'fortis-repo');
  assert.equal(result.result.instructions, REPO_GUIDANCE);
  assert.deepEqual(result.result.capabilities, {tools: {}});
});

test('tools/list replaces stale Windows bind-mount text and appends accurate workspace guidance', () => {
  const message = {
    result: {
      tools: [{
        name: 'read_file',
        description: 'Read files.\nPATH TRANSLATION IN DOCKER:\nOld Windows bind mounts.\nContainer: runtime-id',
        _meta: {'ui/legacy': true, custom: 'keep'}
      }]
    }
  };
  const result = presentResponse(message, {method: 'tools/list'});
  const tool = result.result.tools[0];
  assert.match(tool.description, /Verified workspace layout \(2026-11-03\)/);
  assert.match(tool.description, /\/workspace\/repo is the root/);
  assert.match(tool.description, /not independent Windows bind mounts/);
  assert.match(tool.description, /tool allowlists are not OS isolation/);
  assert.doesNotMatch(tool.description, /Only C:\\\\Users/);
  assert.doesNotMatch(tool.description, /Host Repos =/);
  assert.deepEqual(tool._meta, {custom: 'keep'});
});

test('operation responses are unchanged by presentation wrapper', () => {
  const message = {result: {content: [{type: 'text', text: 'unchanged'}], isError: false}};
  assert.deepEqual(presentResponse(message, {method: 'tools/call'}), message);
});
