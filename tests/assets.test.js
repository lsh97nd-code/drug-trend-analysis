const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync, readdirSync } = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
function webAssets(directory) {
  return readdirSync(path.join(root, directory))
    .filter(name => /\.(html|css|js)$/i.test(name))
    .sort();
}

test('GitHub Pages serves the same dashboard code and data as the local dashboard', () => {
  const assets = webAssets('dashboard');
  assert.deepEqual(webAssets('docs'), assets);
  for (const required of ['index.html', 'style.css', 'core.js', 'comparison.js', 'script.js', 'data.js']) {
    assert.ok(assets.includes(required), `missing dashboard/${required}`);
  }
  for (const name of assets) {
    const local = readFileSync(path.join(root, 'dashboard', name));
    const pages = readFileSync(path.join(root, 'docs', name));
    assert.ok(local.equals(pages), `docs/${name} differs from dashboard/${name}`);
  }
});
