import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ExperimentDetailPage } from './ExperimentDetailPage';
import * as backendClient from '../lib/backendClient';

vi.mock('../lib/backendClient');

const mockedFetchExperimentDetail = vi.mocked(
    backendClient.fetchExperimentDetail
);
const mockedFetchInsightCandidates = vi.mocked(
    backendClient.fetchInsightCandidates
);
const mockedSubmitInsightFeedback = vi.mocked(
    backendClient.submitInsightFeedback
);

describe('ExperimentDetailPage', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('shows jobs and allows adopting an insight with comment', async () => {
        mockedFetchExperimentDetail.mockResolvedValue({
            id: 5,
            goal_description: '街の人口推移から傾向を知る',
            status: 'running',
            dataset_ids: [1],
            jobs: [
                {
                    id: 1,
                    dataset_id: 1,
                    job_type: 'analysis',
                    status: 'pending',
                    description: '人口推移の推計'
                }
            ]
        });
        mockedFetchInsightCandidates
            .mockResolvedValueOnce({
                insights: [
                    {
                        id: 100,
                        title: '人口増加の傾向',
                        description: 'ここ5年で増加',
                        adopted: false,
                        dataset_id: 1
                    }
                ]
            })
            .mockResolvedValueOnce({
                insights: [
                    {
                        id: 100,
                        title: '人口増加の傾向',
                        description: 'ここ5年で増加',
                        adopted: true,
                        dataset_id: 1,
                        feedback_comment: 'これは採用'
                    }
                ]
            });
        mockedSubmitInsightFeedback.mockResolvedValue();

        render(
            <MemoryRouter initialEntries={[`/experiments/5`]}>
                <Routes>
                    <Route
                        path="/experiments/:id"
                        element={<ExperimentDetailPage />}
                    />
                </Routes>
            </MemoryRouter>
        );

        await waitFor(() => {
            expect(screen.getByText('人口増加の傾向')).toBeInTheDocument();
            expect(screen.getByText('人口推移の推計')).toBeInTheDocument();
        });

        const textarea = screen.getByPlaceholderText('コメントを入力');
        fireEvent.change(textarea, { target: { value: 'これは採用' } });
        fireEvent.click(screen.getByRole('button', { name: /採用/ }));

        await waitFor(() => {
            expect(mockedSubmitInsightFeedback).toHaveBeenCalledWith(
                100,
                'adopted',
                'これは採用'
            );
        });

        await waitFor(() => {
            expect(screen.getByText('採用済み')).toBeInTheDocument();
            expect(mockedFetchInsightCandidates).toHaveBeenCalledTimes(2);
        });
    });
});
