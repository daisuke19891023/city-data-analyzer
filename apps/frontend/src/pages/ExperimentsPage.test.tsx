import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ExperimentsPage } from './ExperimentsPage';
import * as backendClient from '../lib/backendClient';

vi.mock('../lib/backendClient');

const mockedFetchDatasets = vi.mocked(backendClient.fetchDatasets);
const mockedCreateExperiment = vi.mocked(backendClient.createExperiment);
const mockedListExperiments = vi.mocked(backendClient.listExperiments);

describe('ExperimentsPage', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders dataset checkboxes and updates status after creation', async () => {
        mockedFetchDatasets.mockResolvedValue([
            {
                id: 1,
                name: '人口推移データセット',
                description: null,
                year: 2023
            },
            { id: 2, name: '交通量データセット', description: null, year: 2022 }
        ]);
        mockedListExperiments
            .mockResolvedValueOnce([])
            .mockResolvedValue([
                {
                    id: 11,
                    goal_description: 'goal',
                    status: 'pending',
                    dataset_ids: [1]
                }
            ]);
        mockedCreateExperiment.mockResolvedValue(42);

        render(
            <MemoryRouter>
                <ExperimentsPage />
            </MemoryRouter>
        );

        await waitFor(() => {
            expect(
                screen.getByText('人口推移データセット')
            ).toBeInTheDocument();
            expect(screen.getByText('交通量データセット')).toBeInTheDocument();
        });

        fireEvent.click(screen.getByRole('button', { name: '実験を作成' }));

        await waitFor(() => {
            expect(mockedCreateExperiment).toHaveBeenCalledWith(
                expect.stringContaining('街の人口推移'),
                [1]
            );
            expect(screen.getByText(/実験 #42/)).toBeInTheDocument();
        });

        await waitFor(() => {
            expect(mockedListExperiments).toHaveBeenCalledTimes(2);
            expect(screen.getByText('pending')).toBeInTheDocument();
        });
    });
});
