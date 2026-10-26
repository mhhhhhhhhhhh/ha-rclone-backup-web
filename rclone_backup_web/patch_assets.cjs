/* Patch real JSX asset attributes, never text inside JavaScript strings. */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const ts = require('/web/node_modules/typescript');

function patchSource(source, filename) {
  const parsed = ts.createSourceFile(filename, source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  if (parsed.parseDiagnostics.length) {
    throw new Error(`Cannot safely patch ${filename}: input contains syntax errors.`);
  }
  const edits = [];
  function visit(node) {
    if (ts.isJsxAttribute(node) && node.name.getText(parsed) === 'src' &&
        node.initializer && ts.isStringLiteral(node.initializer) &&
        /^\/[^\r\n]+\.(svg|png|ico|jpg|jpeg|webp)$/.test(node.initializer.text)) {
      edits.push({
        start: node.initializer.getStart(parsed),
        end: node.initializer.getEnd(),
        text: `{window.__HA_INGRESS_PATH__ + ${JSON.stringify(node.initializer.text)}}`,
      });
    }
    ts.forEachChild(node, visit);
  }
  visit(parsed);
  let result = source;
  for (const edit of edits.sort((a, b) => b.start - a.start)) {
    result = result.slice(0, edit.start) + edit.text + result.slice(edit.end);
  }
  const checked = ts.createSourceFile(filename, result, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  if (checked.parseDiagnostics.length) {
    throw new Error(`Asset patch produced invalid syntax in ${filename}.`);
  }
  return {source: result, count: edits.length};
}

function selfTest() {
  const selector = `const element = document.querySelector('header img[src="/icon.svg"]');`;
  const comment = `// Example selector: src="/icon.svg"`;
  const sample = `${selector}\n${comment}\nconst view = <img src="/icon.svg" alt="Logo" />;\n`;
  const result = patchSource(sample, 'regression.tsx');
  assert.equal(result.count, 1);
  assert.ok(result.source.includes(selector), 'Quoted selector must remain unchanged');
  assert.ok(result.source.includes(comment), 'Comments must remain unchanged');
  assert.ok(result.source.includes('src={window.__HA_INGRESS_PATH__ + "/icon.svg"}'));
  const noJsx = patchSource(selector, 'selector-only.tsx');
  assert.equal(noJsx.source, selector);
  assert.equal(noJsx.count, 0);
  console.log('PASS: TSX asset patch regression tests (selector, comment, JSX, syntax)');
}

function walk(directory) {
  for (const entry of fs.readdirSync(directory, {withFileTypes: true})) {
    const file = path.join(directory, entry.name);
    if (entry.isDirectory()) walk(file);
    else if (entry.isFile() && file.endsWith('.tsx')) {
      const result = patchSource(fs.readFileSync(file, 'utf8'), file);
      if (result.count) {
        fs.writeFileSync(file, result.source, 'utf8');
        console.log(`Patched JSX assets in ${file}: ${result.count}`);
      }
    }
  }
}

selfTest();
if (!process.argv.includes('--self-test')) walk('/web/src');
