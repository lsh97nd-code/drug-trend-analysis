(function dashboard() {
  'use strict';

  const find = (id) => document.getElementById(id);
  const core = window.DrugTrendCore;
  let data, offense;
  try {
    data = core.validateMonthlyData(window.MONTHLY_DATA);
    offense = core.validateOffenseData(window.OFFENSE_DATA);
  } catch (error) {
    find('dashboardContent').hidden = true;
    find('loadError').hidden = false;
    console.error('대시보드 데이터 로드 실패', error);
    return;
  }

  const dates = data.map((row) => row.date);
  const years = offense.map((row) => row.year).sort((a, b) => a - b);
  const ranges = core.presetRanges(dates);
  const defaults = {
    start: dates[0], end: dates.at(-1), type: 'total', ma: true, year: years.at(-1),
  };
  const labels = {
    total: '전체 단속인원', psychotropics: '향정신성의약품', cannabis: '대마', narcotics: '마약',
  };
  const offenseLabels = ['밀조', '밀수', '밀매', '밀경', '투약', '소지', '기타'];
  const number = new Intl.NumberFormat('ko-KR', { maximumFractionDigits: 1 });
  const format = (value) => number.format(value);
  const start = find('start'), end = find('end'), preset = find('preset');
  const series = find('series'), maToggle = find('maToggle'), offenseYear = find('offenseYear');
  const tooltip = find('tooltip');
  const themeToggle = find('themeToggle');

  function applyTheme(theme, persist = false) {
    const next = theme === 'dark' ? 'dark' : 'light';
    document.documentElement.dataset.theme = next;
    themeToggle.setAttribute('aria-pressed', String(next === 'dark'));
    themeToggle.setAttribute('aria-label', `${next === 'dark' ? '라이트' : '다크'} 모드로 전환`);
    themeToggle.textContent = `${next === 'dark' ? '라이트' : '다크'} 모드`;
    if (persist) {
      try {
        localStorage.setItem('drug-trend-theme', next);
      } catch (_) {}
    }
  }

  applyTheme(document.documentElement.dataset.theme);
  themeToggle.addEventListener('click', () => {
    applyTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark', true);
  });

  const displayMonth = (value) => value.replace('-', '.');
  find('dataCoverage').textContent =
    `${displayMonth(dates[0])}~${displayMonth(dates.at(-1))} · ` +
    '대검찰청 월별 통계 기반 · 기간과 지표를 바꿔가며 탐색';
  find('recordBadge').textContent = `${dates.length}개월`;
  find('recordBadge').title = `최신 월별 데이터: ${dates.at(-1)}`;

  for (const date of dates) {
    start.add(new Option(date, date));
    end.add(new Option(date, date));
  }
  for (const year of years) offenseYear.add(new Option(year, year));
  for (const option of preset.options) {
    const range = ranges[option.value];
    option.disabled = !range;
    if (range) option.textContent = core.presetLabel(option.value, range);
  }

  function hideTip() {
    tooltip.hidden = true;
  }

  function showTip(mark, x, y) {
    tooltip.textContent = mark.getAttribute('aria-label');
    tooltip.hidden = false;
    tooltip.style.left = `${Math.max(0, Math.min(x + 10, innerWidth - tooltip.offsetWidth - 4))}px`;
    tooltip.style.top = `${Math.max(0, Math.min(y + 10, innerHeight - tooltip.offsetHeight - 4))}px`;
  }

  // Each chart occupies one tab stop. Arrow keys move through its individual observations.
  function mountChart(container, title, width, height, content) {
    container.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="group" aria-label="${title}">${content}</svg>`;
    const marks = [...container.querySelectorAll('[data-tip]')];
    for (const [index, mark] of marks.entries()) {
      mark.setAttribute('tabindex', index === 0 ? '0' : '-1');
      mark.addEventListener('pointermove', (event) => showTip(mark, event.clientX, event.clientY));
      mark.addEventListener('pointerleave', hideTip);
      mark.addEventListener('focus', () => {
        for (const point of marks) point.setAttribute('tabindex', point === mark ? '0' : '-1');
        const box = mark.getBoundingClientRect();
        showTip(mark, box.x + box.width / 2, box.y + box.height / 2);
      });
      mark.addEventListener('blur', hideTip);
      mark.addEventListener('keydown', (event) => {
        const targets = {
          ArrowLeft: Math.max(0, index - 1), ArrowRight: Math.min(index + 1, marks.length - 1),
          Home: 0, End: marks.length - 1,
        };
        if (Object.hasOwn(targets, event.key)) {
          event.preventDefault();
          marks[targets[event.key]].focus();
        }
      });
    }
  }

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') hideTip();
  });

  function markAttributes(tip) {
    // Labels consist of validated dates, formatted numbers and fixed Korean terms.
    return `data-tip="" role="img" aria-label="${tip}"`;
  }

  function lineChart(rows, key) {
    const width = 900, height = 360, left = 58, right = 24, top = 18, bottom = 44;
    const values = rows.map((row) => row[key]);
    const averages = core.movingAverage(values);
    const max = Math.max(1, ...values) * 1.08;
    const plotWidth = width - right - left, plotHeight = height - bottom - top;
    const x = (i) => rows.length > 1 ? left + i * plotWidth / (rows.length - 1) : left + plotWidth / 2;
    const y = (value) => top + (1 - value / max) * plotHeight;
    const chart = [];
    for (let i = 0; i <= 4; i++) {
      const yy = top + i * plotHeight / 4;
      chart.push(`<line class="grid" x1="${left}" y1="${yy}" x2="${width - right}" y2="${yy}"/>
        <text class="label" x="${left - 8}" y="${yy + 4}" text-anchor="end">${format(Math.round(max * (1 - i / 4)))}</text>`);
    }
    const points = values.map((value, i) => `${x(i)},${y(value)}`).join(' ');
    chart.push(`<polyline class="line-main" points="${points}"/>`);
    if (maToggle.checked) {
      const points = averages.flatMap((value, i) => value === null ? [] : [`${x(i)},${y(value)}`]);
      if (points.length === 1) {
        chart.push(`<circle class="line-ma" cx="${x(11)}" cy="${y(averages[11])}" r="3"/>`);
      } else if (points.length > 1) {
        chart.push(`<polyline class="line-ma" points="${points.join(' ')}"/>`);
      }
    }
    for (const i of new Set([0, Math.floor((rows.length - 1) / 2), rows.length - 1])) {
      chart.push(`<text class="label" x="${x(i)}" y="${height - 12}" text-anchor="middle">${rows[i].date}</text>`);
    }
    values.forEach((value, i) => {
      const tip = `${rows[i].date} · ${labels[key]} ${format(value)}명`;
      chart.push(`<circle class="dot hover-dot" ${markAttributes(tip)} cx="${x(i)}" cy="${y(value)}" r="${rows.length === 1 ? 5 : 3}"/>`);
    });
    mountChart(find('lineChart'), `${labels[key]} 월별 추이`, width, height, chart.join(''));
  }

  function monthChart(rows, key) {
    const months = core.calendarMonthAverages(rows, key);
    const width = 620, height = 310, left = 42, right = 14, bottom = 48, top = 18;
    const slot = (width - left - right) / 12, barWidth = slot * 0.7;
    const max = Math.max(1, ...months.map((item) => item.value ?? 0)) * 1.12;
    const baseline = height - bottom, plotHeight = baseline - top;
    const chart = [];
    for (let i = 0; i <= 4; i++) {
      const y = top + i * plotHeight / 4;
      chart.push(`<line class="grid" x1="${left}" y1="${y}" x2="${width - right}" y2="${y}"/>`);
    }
    months.forEach(({ month, value, count }, i) => {
      const center = left + (i + 0.5) * slot;
      const label = `${month}월`;
      const tip = count ? `${label} 평균 ${format(value)}명 · 관측 ${count}개월` : `${label} · 관측 없음`;
      const h = (value ?? 0) / max * plotHeight;
      const bar = count
        ? `<rect class="bar monthbar" x="${center - barWidth / 2}" y="${baseline - h}" width="${barWidth}" height="${h}" rx="3"/>`
        : '';
      const missingOrZero = !value
        ? `<text class="value-label" x="${center}" y="${baseline - 4}" text-anchor="middle">${count ? '0' : '자료 없음'}</text>` : '';
      chart.push(`<g ${markAttributes(tip)}><rect fill="transparent" x="${center - slot / 2}" y="${top}" width="${slot}" height="${plotHeight + 30}"/>
        ${bar}${missingOrZero}<text class="label" x="${center}" y="${height - 24}" text-anchor="middle">${label}</text></g>`);
    });
    mountChart(find('monthChart'), `${labels[key]} 달력 월별 평균`, width, height, chart.join(''));
  }

  function yoyChart(startDate, endDate, key) {
    const points = core.yearOverYear(data, key, { start: startDate, end: endDate });
    const valid = points.filter((point) => point.changePct !== null);
    const container = find('yoyChart');
    find('yoyDesc').textContent = `${labels[key]} · ${startDate}~${endDate}의 각 월을 12개월 전 같은 달과 비교`;

    const missingCount = points.filter((point) => point.reason === 'missing-base').length;
    const zeroCount = points.filter((point) => point.reason === 'zero-base').length;
    const exclusions = [];
    if (missingCount) exclusions.push(`전년 자료가 없는 ${missingCount}개월`);
    if (zeroCount) exclusions.push(`전년 값이 0인 ${zeroCount}개월`);
    find('yoyNote').textContent = exclusions.length
      ? `${exclusions.join(', ')}은 증감률 계산에서 제외했습니다.`
      : '선택한 모든 월에 비교 가능한 전년 동월 자료가 있습니다.';

    if (valid.length === 0) {
      container.innerHTML = '<p class="empty-chart">비교 가능한 전년 동월 자료가 없습니다. 2018년 이후 월을 포함해 보세요.</p>';
      return;
    }

    const width = 900, height = 310, left = 58, right = 24, top = 22, bottom = 46;
    const plotWidth = width - left - right, plotHeight = height - top - bottom;
    const baseline = top + plotHeight / 2;
    const maxAbs = Math.max(1, ...valid.map((point) => Math.abs(point.changePct))) * 1.08;
    const slot = plotWidth / points.length;
    const barWidth = Math.max(2, Math.min(18, slot * 0.72));
    const chart = [];

    for (const [rate, y] of [[maxAbs, top], [0, baseline], [-maxAbs, top + plotHeight]]) {
      chart.push(`<line class="${rate === 0 ? 'axis' : 'grid'}" x1="${left}" y1="${y}" x2="${width - right}" y2="${y}"/>
        <text class="label" x="${left - 8}" y="${y + 4}" text-anchor="end">${rate.toFixed(1)}%</text>`);
    }

    points.forEach((point, index) => {
      if (point.changePct === null) return;
      const center = left + (index + 0.5) * slot;
      const rawHeight = Math.abs(point.changePct) / maxAbs * (plotHeight / 2);
      const barHeight = Math.max(2, rawHeight);
      const y = point.changePct >= 0 ? baseline - barHeight : baseline;
      const signedRate = `${point.changePct >= 0 ? '+' : ''}${point.changePct.toFixed(1)}%`;
      const tip = `${point.date} · 전년 동월 대비 ${signedRate} (${format(point.previous)}명 → ${format(point.current)}명)`;
      chart.push(`<rect class="yoy-bar ${point.changePct >= 0 ? 'positive' : 'negative'}" ${markAttributes(tip)}
        x="${center - barWidth / 2}" y="${y}" width="${barWidth}" height="${barHeight}" rx="2"/>`);
    });

    for (const index of new Set([0, Math.floor((points.length - 1) / 2), points.length - 1])) {
      const center = left + (index + 0.5) * slot;
      chart.push(`<text class="label" x="${center}" y="${height - 14}" text-anchor="middle">${points[index].date}</text>`);
    }
    mountChart(container, `${labels[key]} 전년 동월 대비 증감률`, width, height, chart.join(''));
  }

  function renderOffense(year) {
    const { available, row, message } = core.summarizeOffense(offense, year);
    const container = find('offenseChart');
    find('offenseNote').textContent = message;
    if (!available || row.total === 0) {
      container.textContent = available ? '합계가 0명이어서 구성비를 계산할 수 없습니다.' : '유형별 자료 없음';
      return;
    }
    const chart = [];
    let x = 20;
    core.OFFENSE_KEYS.forEach((key, i) => {
      const value = row[key], share = value / row.total, segmentWidth = share * 600;
      const color = `hsl(${210 + i * 23} 65% ${48 + i * 3}%)`;
      const label = offenseLabels[i], percent = `${(share * 100).toFixed(1)}%`;
      const tip = `${label} ${format(value)}명 · ${percent}`;
      const legendX = 25 + (i % 4) * 150, legendY = 188 + Math.floor(i / 4) * 27;
      chart.push(`<g ${markAttributes(tip)}>
        <rect class="segment" x="${x}" y="75" width="${segmentWidth}" height="70" fill="${color}"/>
        <rect x="${legendX}" y="${legendY - 10}" width="12" height="12" fill="${color}"/>
        <text class="label" x="${legendX + 18}" y="${legendY}">${label} ${percent}</text></g>`);
      x += segmentWidth;
    });
    mountChart(container, `${year}년 범죄 유형 구성비`, 640, 260, chart.join(''));
  }

  function renderMonthly(rows, key) {
    const values = rows.map((row) => row[key]);
    const average = format(core.mean(values));
    const top = [...rows].sort((a, b) => b[key] - a[key]).slice(0, 5);
    const peak = top[0];
    find('kPeriod').textContent = `${rows[0].date} ~ ${rows.at(-1).date}`;
    find('kCount').textContent = `${rows.length}개월`;
    find('kAvg').textContent = `${average}명`;
    find('kMax').textContent = `${peak.date} · ${format(peak[key])}명`;
    find('seriesDesc').textContent = `${labels[key]} · 선택 기간 ${rows.length}개월`;
    lineChart(rows, key);
    monthChart(rows, key);
    yoyChart(rows[0].date, rows.at(-1).date, key);
    const tableRows = top.map((row, i) => `<tr><td>${i + 1}</td><td>${row.date}</td><td>${format(row[key])}명</td></tr>`);
    find('topTable').innerHTML = `<table class="table"><thead><tr><th scope="col">순위</th><th scope="col">월</th><th scope="col">${labels[key]}</th></tr></thead><tbody>${tableRows.join('')}</tbody></table>`;
    let change = '시작 월 값이 0명이어서 증감률을 계산할 수 없습니다.';
    if (rows.length === 1) {
      change = '한 달을 선택했습니다.';
    } else if (values[0] > 0) {
      const pct = 100 * (values.at(-1) - values[0]) / values[0];
      change = `시작 월 대비 종료 월은 ${pct >= 0 ? '+' : ''}${pct.toFixed(1)}%입니다.`;
    }
    find('interpretation').textContent = `현재 선택 구간의 ${labels[key]} 월평균은 ${average}명입니다. ${change} 최고 월은 ${peak.date}입니다. 이 변화는 관찰값이며 특정 사건이나 정책의 직접 효과로 단정하지 않습니다.`;
  }

  function render(state) {
    const range = core.normalizeRange(dates, state.start, state.end);
    start.value = range.start;
    end.value = range.end;
    preset.value = core.matchingPreset(ranges, range.start, range.end);
    series.value = state.type;
    maToggle.checked = state.ma;
    offenseYear.value = state.year;
    hideTip();
    renderMonthly(data.slice(range.startIndex, range.endIndex + 1), state.type);
    renderOffense(state.year);
    window.DrugTrendComparison.render(data, state.type, labels[state.type]);

    const url = core.writeFilters(location.href, { ...state, start: range.start, end: range.end }, defaults);
    if (url.href !== location.href) history.replaceState(history.state, '', url);
  }

  function renderControls() {
    render({ start: start.value, end: end.value, type: series.value, ma: maToggle.checked, year: Number(offenseYear.value) });
  }

  preset.addEventListener('change', () => {
    [start.value, end.value] = ranges[preset.value];
    renderControls();
  });
  [start, end, series, maToggle, offenseYear].forEach((el) => el.addEventListener('change', renderControls));
  find('reset').addEventListener('click', () => render(defaults));
  function downloadText(content, type, filename) {
    const href = URL.createObjectURL(new Blob([content], { type }));
    const link = document.createElement('a');
    link.href = href;
    link.download = filename;
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(href), 1000);
  }

  function selectedRows() {
    const range = core.normalizeRange(dates, start.value, end.value);
    return { range, rows: data.slice(range.startIndex, range.endIndex + 1) };
  }

  find('downloadCsv').addEventListener('click', () => {
    const { range, rows } = selectedRows();
    downloadText(
      core.serializeMonthlyCsv(rows),
      'text/csv;charset=utf-8',
      `monthly_drug_offenders_${range.start}_${range.end}.csv`,
    );
  });
  find('downloadJson').addEventListener('click', () => {
    const { range, rows } = selectedRows();
    downloadText(
      core.serializeMonthlyJson(rows),
      'application/json;charset=utf-8',
      `monthly_drug_offenders_${range.start}_${range.end}.json`,
    );
  });

  const renderUrl = () => render(core.readFilters(new URL(location.href), dates, years));
  window.addEventListener('popstate', renderUrl);
  renderUrl();
})();
