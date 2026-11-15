'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const core = require('../dashboard/core.js');

const dashboard = path.join(__dirname, '..', 'dashboard');
const read = (file) => readFileSync(path.join(dashboard, file), 'utf8');
const window = {};
vm.runInNewContext(read('data.js'), { window });
const monthly = window.MONTHLY_DATA;
const offense = window.OFFENSE_DATA;
const dates = Array.from(monthly, (row) => row.date);
const years = Array.from(offense, (row) => row.year);
const defaults = {
  start: '2017-01', end: '2025-12', type: 'total', ma: true, year: 2025,
};

test('bundled data contains 108 consecutive monthly rows and nine annual records', () => {
  assert.equal(core.validateMonthlyData(monthly).length, 108);
  assert.equal(core.validateOffenseData(offense).length, 9);
  assert.deepEqual(years, [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]);
});

test('invalid monthly objects, dates, counts, totals and chronology surface errors', () => {
  const [jan, feb, mar] = monthly;
  assert.throws(() => core.validateMonthlyData(null), /배열/);
  assert.throws(() => core.validateMonthlyData([]), /최소/);
  assert.throws(() => core.validateMonthlyData([null]), /객체/);
  assert.throws(() => core.validateMonthlyData([{ ...jan, date: '2017-13' }]), /01~12/);
  assert.throws(() => core.validateMonthlyData([{ ...jan, month: 2 }]), /year\/month/);
  assert.throws(() => core.validateMonthlyData([{ ...jan, total: 0.5 }]), /정수/);
  assert.throws(() => core.validateMonthlyData([{ ...jan, total: -1 }]), /정수/);
  assert.throws(() => core.validateMonthlyData([{ ...jan, total: jan.total + 1 }]), /합계/);
  assert.throws(() => core.validateMonthlyData([jan, jan]), /중복/);
  assert.throws(() => core.validateMonthlyData([jan, mar]), /누락/);
  assert.throws(() => core.validateMonthlyData([feb, jan]), /정렬/);
});

test('calendar-month averages distinguish observed zero from an unobserved month', () => {
  const result = core.calendarMonthAverages([
    { month: 1, total: 0 }, { month: 2, total: 0 }, { month: 1, total: 12 },
  ], 'total');
  assert.equal(result.length, 12);
  assert.deepEqual(result.slice(0, 3), [
    { month: 1, count: 2, value: 6 }, { month: 2, count: 1, value: 0 }, { month: 3, count: 0, value: null },
  ]);
});

test('moving average starts only after 12 observations', () => {
  const values = Array.from({ length: 13 }, (_, i) => i + 1);
  assert.deepEqual(core.movingAverage(values), [...Array(11).fill(null), 6.5, 7.5]);
  assert.deepEqual(core.movingAverage([0]), [null]);
});

test('year-over-year compares selected months against the full data history', () => {
  const [point] = core.yearOverYear(monthly, 'total', { start: '2018-01', end: '2018-01' });
  assert.equal(point.date, '2018-01');
  assert.equal(point.previous, monthly[0].total);
  assert.equal(point.current, monthly[12].total);
  assert.equal(point.changePct, (point.current - point.previous) / point.previous * 100);
  assert.equal(point.reason, null);

  const firstYear = core.yearOverYear(monthly, 'total', { start: '2017-01', end: '2017-12' });
  assert.equal(firstYear.length, 12);
  assert.ok(firstYear.every((item) => item.changePct === null && item.reason === 'missing-base'));

  const synthetic = [
    { date: '2025-01', total: 0 },
    { date: '2026-01', total: 4 },
  ];
  assert.deepEqual(core.yearOverYear(synthetic, 'total', { start: '2026-01', end: '2026-01' }), [{
    date: '2026-01', current: 4, previous: 0, changePct: null, reason: 'zero-base',
  }]);
  assert.throws(() => core.yearOverYear(monthly, 'unknown'), /지원하지 않는/);
});

test('2018 offense message always uses its own year, total and missing-data explanation', () => {
  const missing = core.summarizeOffense(offense, '2018');
  assert.equal(missing.available, false);
  assert.match(missing.message, /2018년 합계 12,613명/);
  assert.match(missing.message, /원자료 불일치/);
  assert.equal(core.summarizeOffense(offense, '2025').available, true);
  assert.throws(() => core.validateOffenseData([{ ...missing.row, manufacture: 0 }]), /세부 값/);
  assert.throws(() => core.validateOffenseData([{ ...offense[0], total: 1 }]), /합계/);
});

test('URL endpoints are normalized and determine the matching preset', () => {
  const url = new URL('https://example.org/?start=2022-12&end=2020-01&type=cannabis&ma=0&year=2018');
  const state = core.readFilters(url, dates, years);
  assert.deepEqual(state, { start: '2020-01', end: '2022-12', type: 'cannabis', ma: false, year: 2018 });
  assert.equal(core.matchingPreset(core.presetRanges(dates), state.start, state.end), 'covid');
  assert.equal(core.matchingPreset(core.presetRanges(dates), state.start, '2022-11'), 'custom');
  const single = core.normalizeRange(dates, '2020-01', '2020-01');
  assert.equal(single.startIndex, single.endIndex);
});

test('preset links and old start/end/type links share the same filter state', () => {
  const preset = core.readFilters(new URL('https://example.org/?preset=pre&type=narcotics'), dates, years);
  const legacy = core.readFilters(new URL('https://example.org/?end=2019-12&type=narcotics'), dates, years);
  assert.deepEqual(preset, legacy);
  assert.deepEqual(core.readFilters(new URL('https://example.org/?preset=toString&type=constructor&year=2099&start=1999-08'), dates, years), defaults);
});

test('presets and labels extend through newly appended complete years', () => {
  const futureDates = [...dates];
  for (let year = 2026; year <= 2027; year++) {
    for (let month = 1; month <= 12; month++) {
      futureDates.push(`${year}-${String(month).padStart(2, '0')}`);
    }
  }
  const ranges = core.presetRanges(futureDates);
  assert.deepEqual(ranges.all, ['2017-01', '2027-12']);
  assert.deepEqual(ranges.post, ['2023-01', '2027-12']);
  assert.equal(core.presetLabel('all', ranges.all), '전체 2017~2027');
  assert.equal(core.presetLabel('post', ranges.post), '이후 2023~2027');
  assert.deepEqual(
    core.readFilters(new URL('https://example.org/?preset=post'), futureDates, [...years, 2026, 2027]),
    { start: '2023-01', end: '2027-12', type: 'total', ma: true, year: 2027 },
  );
});

test('preset labels retain months for a partial terminal year', () => {
  const range = ['2023-01', '2027-06'];
  assert.equal(core.presetLabel('post', range), '이후 2023.01~2027.06');
  assert.throws(() => core.presetLabel('custom', range), /지원하지 않는/);
});

test('URL update and reset preserve other query parameters and anchors', () => {
  const url = new URL('https://example.org/docs/?lang=ko&preset=pre#chart');
  const state = { ...defaults, start: '2020-03', end: '2020-04', ma: false, year: 2018 };
  const changed = core.writeFilters(url, state, defaults);
  assert.deepEqual(core.readFilters(changed, dates, years), state);
  assert.equal(changed.searchParams.has('preset'), false);
  assert.equal(core.writeFilters(changed, defaults, defaults).href, 'https://example.org/docs/?lang=ko#chart');
});

test('directly opened local HTML supports filter changes and reset with a fragment', () => {
  for (const url of ['file:///C:/dashboard/index.html', 'file:///C:/dashboard/index.html?type=cannabis']) {
    const state = { ...defaults, start: '2020-05', end: '2020-10', ma: false };
    const changed = core.writeFilters(url, state, defaults);
    assert.equal(changed.search, new URL(url).search);
    assert.deepEqual(core.readFilters(changed, dates, years), state);
    assert.deepEqual(core.readFilters(core.writeFilters(changed, defaults, defaults), dates, years), defaults);
  }
});

test('CSV contains exactly the selected rows and all seven processed columns', () => {
  const rows = monthly.slice(4, 6);
  const csv = core.serializeMonthlyCsv(rows);
  assert.equal(csv.charCodeAt(0), 0xfeff);
  const [header, ...lines] = csv.slice(1).trimEnd().split('\r\n');
  assert.equal(header, 'date,year,month,total,cannabis,narcotics,psychotropics');
  assert.deepEqual(lines, Array.from(rows, (row) => header.split(',').map((key) => '"' + row[key] + '"').join(',')));
});

test('JSON contains selection metadata and exactly seven processed fields', () => {
  const rows = monthly.slice(4, 6);
  const payload = JSON.parse(core.serializeMonthlyJson(rows));
  assert.equal(payload.schemaVersion, 1);
  assert.deepEqual(payload.period, { start: rows[0].date, end: rows[1].date });
  assert.equal(payload.rowCount, 2);
  assert.deepEqual(payload.fields, ['date', 'year', 'month', 'total', 'cannabis', 'narcotics', 'psychotropics']);
  assert.deepEqual(payload.data, Array.from(rows, (row) => Object.fromEntries(
    payload.fields.map((field) => [field, row[field]])
  )));
  assert.throws(() => core.serializeMonthlyJson([]), /필요합니다/);
});

test('missing or invalid data hides the dashboard and exposes the load error', () => {
  for (const invalid of [
    {}, { DrugTrendCore: core },
    { DrugTrendCore: core, MONTHLY_DATA: [], OFFENSE_DATA: offense },
    { DrugTrendCore: core, MONTHLY_DATA: monthly, OFFENSE_DATA: [{ ...offense[0], total: 0 }] },
  ]) {
    const elements = { dashboardContent: { hidden: false }, loadError: { hidden: true } };
    vm.runInNewContext(read('script.js'), {
      window: invalid, document: { getElementById: (id) => elements[id] }, console: { error() {} },
    });
    assert.equal(elements.dashboardContent.hidden, true);
    assert.equal(elements.loadError.hidden, false);
  }
});
