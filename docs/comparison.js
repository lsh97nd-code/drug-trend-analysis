(function () {
  'use strict';

  // Each window contains every calendar month once. April 2023 spans the launch.
  function summarize(rows, key) {
    const before = rows.filter(row => row.date >= '2022-04' && row.date <= '2023-03');
    const after = rows.filter(row => row.date >= '2023-05' && row.date <= '2024-04');
    if (before.length !== 12 || after.length !== 12) return null;
    const mean = period => period.reduce((sum, row) => sum + row[key], 0) / period.length;
    const change = (a, b) => a === 0 ? null : (b - a) / a * 100;
    const exceptJulyAugust = period => period.filter(row => row.month !== 7 && row.month !== 8);
    const pre = mean(before);
    const post = mean(after);
    return {
      beforeMean: pre,
      afterMean: post,
      changeRate: change(pre, post),
      withoutSummerRate: change(mean(exceptJulyAugust(before)), mean(exceptJulyAugust(after))),
    };
  }

  function render(rows, key, label) {
    const get = id => document.getElementById(id);
    const stats = summarize(rows, key);
    get('comparisonValues').hidden = !stats;
    get('comparisonMetric').textContent = stats
      ? `${label} · 월평균`
      : '두 비교 기간의 월별 자료가 모두 있어야 전후 차이를 계산할 수 있습니다.';
    if (!stats) {
      get('summerComparison').textContent = '';
      return;
    }
    const fmt = value => value.toLocaleString('ko-KR', { maximumFractionDigits: 1 });
    const pct = value => `${value > 0 ? '+' : ''}${fmt(value)}%`;
    get('beforeMean').textContent = `${fmt(stats.beforeMean)}명`;
    get('afterMean').textContent = `${fmt(stats.afterMean)}명`;
    get('changeRate').textContent = stats.changeRate === null ? '기준값 0명' : pct(stats.changeRate);
    get('summerComparison').textContent = stats.withoutSummerRate === null
      ? '7·8월을 양쪽에서 빼면 출범 전 월평균이 0명이어서 증감률을 계산할 수 없습니다.'
      : `7·8월을 양쪽에서 빼면 나머지 10개월의 월평균 증감률은 ${pct(stats.withoutSummerRate)}입니다.`;
  }

  const api = Object.freeze({ summarize, render });
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (typeof window !== 'undefined') window.DrugTrendComparison = api;
})();
