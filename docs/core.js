(function exposeDrugTrendCore(root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.DrugTrendCore = api;
  }
})(typeof window === 'undefined' ? null : window, function createDrugTrendCore() {
  'use strict';

  const SERIES_KEYS = Object.freeze([
    'total',
    'cannabis',
    'narcotics',
    'psychotropics',
  ]);
  const OFFENSE_KEYS = Object.freeze([
    'manufacture',
    'smuggling',
    'dealing',
    'illegal_cultivation',
    'use',
    'possession',
    'other',
  ]);
  const MONTH_PATTERN = /^(\d{4})-(\d{2})$/;

  function parseMonthIndex(value) {
    const match = typeof value === 'string' && MONTH_PATTERN.exec(value);
    if (!match) {
      throw new Error(`월 형식은 YYYY-MM이어야 합니다: ${value}`);
    }
    const year = Number(match[1]);
    const month = Number(match[2]);
    if (month < 1 || month > 12) {
      throw new Error(`월은 01~12 범위여야 합니다: ${value}`);
    }
    return year * 12 + month - 1;
  }

  function isNonNegativeInteger(value) {
    return Number.isSafeInteger(value) && value >= 0;
  }

  function validateMonthlyData(data, { minimumRows = 1 } = {}) {
    if (!Array.isArray(data)) {
      throw new Error('월별 데이터가 배열이 아닙니다.');
    }
    if (!Number.isSafeInteger(minimumRows) || minimumRows < 1) {
      throw new Error('minimumRows는 1 이상의 정수여야 합니다.');
    }
    if (data.length < minimumRows) {
      throw new Error(`월별 데이터는 최소 ${minimumRows}건이 필요합니다.`);
    }

    const seen = new Set();
    let previousMonth = null;
    data.forEach((row, index) => {
      if (!row || typeof row !== 'object') {
        throw new Error(`${index + 1}번째 월별 데이터가 객체가 아닙니다.`);
      }
      const currentMonth = parseMonthIndex(row.date);
      const expectedYear = Math.floor(currentMonth / 12);
      const expectedMonth = (currentMonth % 12) + 1;
      if (row.year !== expectedYear || row.month !== expectedMonth) {
        throw new Error(`${row.date}의 year/month가 날짜와 일치하지 않습니다.`);
      }
      if (seen.has(row.date)) {
        throw new Error(`중복 월이 있습니다: ${row.date}`);
      }
      seen.add(row.date);

      for (const key of SERIES_KEYS) {
        if (!isNonNegativeInteger(row[key])) {
          throw new Error(`${row.date}의 ${key}는 0 이상의 정수여야 합니다.`);
        }
      }
      if (row.cannabis + row.narcotics + row.psychotropics !== row.total) {
        throw new Error(`${row.date}의 종류별 합계와 전체가 다릅니다.`);
      }
      if (previousMonth !== null && currentMonth !== previousMonth + 1) {
        throw new Error(`${row.date} 앞에 월 누락 또는 정렬 오류가 있습니다.`);
      }
      previousMonth = currentMonth;
    });
    return data;
  }

  function validateOffenseData(data) {
    if (!Array.isArray(data) || data.length === 0) {
      throw new Error('범죄 유형 데이터가 비어 있습니다.');
    }
    const seenYears = new Set();
    data.forEach((row) => {
      if (!row || !Number.isSafeInteger(row.year) || !isNonNegativeInteger(row.total)) {
        throw new Error('범죄 유형 데이터의 연도 또는 합계가 올바르지 않습니다.');
      }
      if (seenYears.has(row.year)) {
        throw new Error(`중복 범죄 유형 연도가 있습니다: ${row.year}`);
      }
      seenYears.add(row.year);
      const values = OFFENSE_KEYS.map((key) => row[key]);
      const hasBreakdown = values.every(isNonNegativeInteger);
      const hasNoBreakdown = values.every((value) => value === null);
      if (!hasBreakdown && !hasNoBreakdown) {
        throw new Error(`${row.year}년 범죄 유형 세부 값 구성이 올바르지 않습니다.`);
      }
      if (hasBreakdown && values.reduce((sum, value) => sum + value, 0) !== row.total) {
        throw new Error(`${row.year}년 범죄 유형 합계가 전체와 다릅니다.`);
      }
    });
    return data;
  }

  function mean(values) {
    if (!Array.isArray(values) || values.length === 0) {
      return null;
    }
    return values.reduce((sum, value) => sum + value, 0) / values.length;
  }

  function movingAverage(values, windowSize = 12) {
    if (!Number.isSafeInteger(windowSize) || windowSize < 1) {
      throw new Error('이동평균 기간은 1 이상의 정수여야 합니다.');
    }
    if (!Array.isArray(values) || values.some((value) => !Number.isFinite(value))) {
      throw new Error('이동평균 입력은 유한한 숫자 배열이어야 합니다.');
    }
    return values.map((_, index) => {
      if (index < windowSize - 1) {
        return null;
      }
      return mean(values.slice(index - windowSize + 1, index + 1));
    });
  }

  function normalizeRange(dates, startValue, endValue) {
    const startIndex = dates.indexOf(startValue);
    const endIndex = dates.indexOf(endValue);
    if (startIndex < 0 || endIndex < 0) {
      throw new Error('선택한 시작 월 또는 종료 월이 데이터에 없습니다.');
    }
    const swapped = startIndex > endIndex;
    return {
      start: swapped ? endValue : startValue,
      end: swapped ? startValue : endValue,
      startIndex: Math.min(startIndex, endIndex),
      endIndex: Math.max(startIndex, endIndex),
      swapped,
    };
  }

  function calendarMonthAverages(rows, key) {
    if (!SERIES_KEYS.includes(key)) {
      throw new Error(`지원하지 않는 분석 지표입니다: ${key}`);
    }
    return Array.from({ length: 12 }, (_, index) => {
      const month = index + 1;
      const values = rows.filter((row) => row.month === month).map((row) => row[key]);
      return { month, count: values.length, value: mean(values) };
    });
  }

  function presetRanges(dates) {
    const ranges = {
      all: [dates[0], dates.at(-1)],
      pre: ['2017-01', '2019-12'],
      covid: ['2020-01', '2022-12'],
      post: ['2023-01', '2025-12'],
    };
    return Object.fromEntries(Object.entries(ranges).filter(
      ([, [start, end]]) => dates.includes(start) && dates.includes(end)
    ));
  }

  function matchingPreset(ranges, start, end) {
    return Object.keys(ranges).find(
      (name) => ranges[name][0] === start && ranges[name][1] === end
    ) || 'custom';
  }

  function readFilters(url, dates, years) {
    const params = url.protocol === 'file:' && url.hash.startsWith('#filters?')
      ? new URLSearchParams(url.hash.slice('#filters?'.length))
      : url.searchParams;
    const ranges = presetRanges(dates);
    const preset = params.get('preset');
    const fallback = Object.hasOwn(ranges, preset) ? ranges[preset] : ranges.all;
    const from = params.get('start');
    const to = params.get('end');
    const { start, end } = normalizeRange(dates,
      dates.includes(from) ? from : fallback[0],
      dates.includes(to) ? to : fallback[1]);
    const key = params.get('type');
    const year = Number(params.get('year'));
    return {
      start, end,
      type: SERIES_KEYS.includes(key) ? key : 'total',
      ma: params.get('ma') !== '0',
      year: years.includes(year) ? year : years.at(-1),
    };
  }

  function writeFilters(url, state, defaults) {
    const next = new URL(url);
    // Local file history entries can change their fragment but not their query.
    const local = next.protocol === 'file:';
    const params = local ? new URLSearchParams() : next.searchParams;
    params.delete('preset');
    for (const key of ['start', 'end', 'type', 'ma', 'year']) {
      if (state[key] === defaults[key]) {
        params.delete(key);
      } else {
        params.set(key, key === 'ma' ? Number(state.ma) : state[key]);
      }
    }
    if (local) {
      const hasOriginalFilters = ['start', 'end', 'type', 'ma', 'year', 'preset']
        .some((key) => next.searchParams.has(key));
      if (params.size || hasOriginalFilters) {
        next.hash = 'filters?' + params;
      } else if (next.hash.startsWith('#filters?')) {
        next.hash = '';
      }
    }
    return next;
  }

  function summarizeOffense(data, year) {
    const row = data.find((item) => item.year === Number(year));
    if (!row) {
      return {
        available: false,
        message: '선택한 연도의 범죄 유형 자료가 없습니다.',
        row: null,
      };
    }
    if (row.manufacture === null) {
      return {
        available: false,
        message:
          `${row.year}년 합계 ${row.total.toLocaleString('ko-KR')}명 · ` +
          '원자료 불일치로 유형별 세부 값은 사용하지 않습니다.',
        row,
      };
    }
    return {
      available: true,
      message: `${row.year}년 합계 ${row.total.toLocaleString('ko-KR')}명 기준`,
      row,
    };
  }

  function escapeCsvCell(value) {
    let text = String(value ?? '');
    if (/^[\s]*[=+\-@]/.test(text)) {
      text = `'${text}`;
    }
    return `"${text.replace(/"/g, '""')}"`;
  }

  function serializeMonthlyCsv(rows) {
    const fields = ['date', 'year', 'month', ...SERIES_KEYS];
    const lines = [fields.join(',')];
    for (const row of rows) {
      lines.push(fields.map((field) => escapeCsvCell(row[field])).join(','));
    }
    return `\uFEFF${lines.join('\r\n')}\r\n`;
  }

  return Object.freeze({
    OFFENSE_KEYS,
    SERIES_KEYS,
    calendarMonthAverages,
    mean,
    movingAverage,
    normalizeRange,
    parseMonthIndex,
    presetRanges,
    matchingPreset,
    readFilters,
    serializeMonthlyCsv,
    summarizeOffense,
    validateMonthlyData,
    validateOffenseData,
    writeFilters,
  });
});
