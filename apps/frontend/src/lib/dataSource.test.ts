import { describe, expect, it } from 'vitest';
import { visualizationDatasets } from '../data/visualizationData';
import {
    answerQuestionFromData,
    applyFilters,
    buildCategoryTable,
    buildMonthlySeries,
    deriveChatIntent,
    resolveDataMode,
    summarizeRecords
} from './dataSource';

describe('resolveDataMode', () => {
    it('prefers Vite-provided env values before falling back to dummy', () => {
        expect(resolveDataMode({ VITE_DATA_MODE: 'api' })).toBe('api');
    });

    it('falls back to dummy when no env flag is provided', () => {
        expect(resolveDataMode({})).toBe('dummy');
    });
});

describe('dataSource utilities', () => {
    const dataset = visualizationDatasets['population-trend'];
    const records = dataset.records;

    it('filters records by metric and time range', () => {
        const filtered = applyFilters(records, {
            metric: '転入超過指数',
            timeRange: '12m',
            category: 'all',
            segment: 'all'
        });
        expect(
            filtered.every((record) => record.metric === '転入超過指数')
        ).toBe(true);
        expect(filtered.length).toBeGreaterThan(0);
    });

    it('builds chart and table friendly aggregates', () => {
        const filtered = applyFilters(records, {
            metric: '転入超過指数',
            timeRange: '12m',
            category: '中心市街地',
            segment: '子育て世帯'
        });
        const chart = buildMonthlySeries(filtered);
        const table = buildCategoryTable(filtered, '転入超過指数');
        expect(chart[0].label).toMatch(/2024-0/);
        expect(table[0].key).toContain('中心市街地');
    });

    it('summarizes and answers questions from filtered data', () => {
        const filtered = applyFilters(records, {
            metric: '夜間人口指数',
            timeRange: '24m',
            category: 'all',
            segment: '単身'
        });
        const summary = summarizeRecords(filtered, '夜間人口指数');
        expect(summary.headline).toContain('夜間人口指数');
        const answer = answerQuestionFromData(
            '夜間のピークを教えて',
            dataset,
            filtered
        );
        expect(answer).toContain('夜間人口指数');
    });

    it('derives chat intent for filters based on question', () => {
        const intent = deriveChatIntent(
            '転入超過指数で中心市街地の単身の直近6ヶ月を見せて',
            dataset,
            {
                metric: '夜間人口指数',
                timeRange: '24m',
                category: 'all',
                segment: 'all'
            }
        );

        expect(intent.updatedFilters?.metric).toBe('転入超過指数');
        expect(intent.updatedFilters?.category).toBe('中心市街地');
        expect(intent.updatedFilters?.segment).toBe('単身');
        expect(intent.updatedFilters?.timeRange).toBe('6m');
        expect(intent.notes.length).toBeGreaterThan(0);
    });
});
