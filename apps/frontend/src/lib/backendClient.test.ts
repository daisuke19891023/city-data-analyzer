import { describe, expect, it, vi, afterEach } from 'vitest';
import {
    createExperiment,
    fetchDatasets,
    fetchExperimentDetail,
    fetchInsightCandidates
} from './backendClient';

type MinimalResponse = { ok: boolean; json: () => Promise<unknown> };

const stubJsonResponse = (body: unknown, ok = true): MinimalResponse => ({
    ok,
    json: async () => body
});

afterEach(() => {
    vi.restoreAllMocks();
});

describe('backendClient helpers', () => {
    it('falls back to sample datasets when fetch fails', async () => {
        vi.stubGlobal('fetch', vi.fn(() => Promise.reject(new Error('network'))));

        const datasets = await fetchDatasets();

        expect(datasets).toHaveLength(2);
        expect(datasets[0].name).toContain('人口推移');
    });

    it('returns experiment id when creation succeeds', async () => {
        vi.stubGlobal(
            'fetch',
            vi.fn(() => Promise.resolve(stubJsonResponse({ experiment_id: 17 })))
        );

        const id = await createExperiment('goal', [1, 2]);

        expect(id).toBe(17);
    });

    it('propagates experiment detail and insight payloads', async () => {
        vi.stubGlobal(
            'fetch',
            vi
                .fn()
                .mockResolvedValueOnce(
                    stubJsonResponse({ id: 99, goal_description: 'test', status: 'pending' })
                )
                .mockResolvedValueOnce(stubJsonResponse({ insights: [] }))
        );

        const detail = await fetchExperimentDetail(99);
        const insights = await fetchInsightCandidates(99);

        expect(detail?.goal_description).toBe('test');
        expect(insights?.insights).toEqual([]);
    });
});
