const { test } = require('node:test');
const assert = require('node:assert/strict');
const { summarize } = require('../dashboard/comparison.js');

// April 2022 through April 2024. Make April 2023 large to catch accidental inclusion.
const rows = Array.from({ length: 25 }, (_, i) => {
  const monthOffset = 3 + i;
  const month = monthOffset % 12 + 1;
  const date = `${2022 + Math.floor(monthOffset / 12)}-${String(month).padStart(2, '0')}`;
  const summer = month === 7 || month === 8;
  const total = i < 12 ? 10 : (summer ? 80 : 20);
  return { date, month, total: i === 12 ? 10000 : total, cannabis: 2 };
});

test('compares two complete years around the launch, with a matched July/August exclusion', () => {
  assert.deepEqual(summarize(rows, 'total'), {
    beforeMean: 10, afterMean: 30, changeRate: 200, withoutSummerRate: 100,
  });
  assert.equal(summarize(rows, 'cannabis').changeRate, 0);
});

test('handles missing comparison months and a zero baseline', () => {
  assert.equal(summarize(rows.slice(1), 'total'), null);
  assert.equal(summarize(rows.slice(0, -1), 'total'), null);
  const noBaseline = rows.map(row => ({ ...row, total: row.date < '2023-04' ? 0 : row.total }));
  const stats = summarize(noBaseline, 'total');
  assert.equal(stats.changeRate, null);
  assert.equal(stats.withoutSummerRate, null);
});
