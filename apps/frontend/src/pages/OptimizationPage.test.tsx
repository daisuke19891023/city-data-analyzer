import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { OptimizationPage } from './OptimizationPage';
import * as backendClient from '../lib/backendClient';

vi.mock('../lib/backendClient');

const mockedStartOptimization = vi.mocked(backendClient.startOptimization);
const mockedListOptimizationJobs = vi.mocked(
    backendClient.listOptimizationJobs
);

describe('OptimizationPage', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('submits optimization form and shows success toast', async () => {
        mockedListOptimizationJobs
            .mockResolvedValueOnce([])
            .mockResolvedValueOnce([
                {
                    id: 'optim-123',
                    provider: 'openai',
                    model: 'gpt-4o-mini',
                    dataset: 'population-trend',
                    trainset: 'train-v1',
                    status: 'running',
                    artifactVersion: null
                }
            ]);
        mockedStartOptimization.mockResolvedValue({ jobId: 'optim-123' });

        render(
            <MemoryRouter>
                <OptimizationPage />
            </MemoryRouter>
        );

        fireEvent.click(screen.getByRole('button', { name: '最適化を開始' }));

        await waitFor(() => {
            expect(mockedStartOptimization).toHaveBeenCalledWith({
                provider: 'openai',
                model: 'gpt-4o-mini',
                dataset: 'population-trend',
                trainset: 'train-v1'
            });
        });

        await waitFor(() => {
            expect(
                screen.getByText('ジョブ optim-123 を開始しました')
            ).toBeInTheDocument();
        });

        await waitFor(() => {
            expect(mockedListOptimizationJobs).toHaveBeenCalledTimes(2);
        });
    });

    it('shows error message when API fails', async () => {
        mockedListOptimizationJobs.mockResolvedValue([]);
        mockedStartOptimization.mockRejectedValue(new Error('network error'));

        render(
            <MemoryRouter>
                <OptimizationPage />
            </MemoryRouter>
        );

        fireEvent.click(screen.getByRole('button', { name: '最適化を開始' }));

        await waitFor(() => {
            expect(
                screen.getByText('最適化リクエストに失敗しました')
            ).toBeInTheDocument();
        });
        expect(mockedStartOptimization).toHaveBeenCalled();
    });
});
