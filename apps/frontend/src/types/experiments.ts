export type DatasetSummary = {
    id: number;
    name: string;
    description?: string | null;
    year?: number | null;
};

export type ExperimentSummary = {
    id: number;
    goal_description: string;
    status: string;
    dataset_ids: number[];
};

export type ExperimentJob = {
    id: number;
    dataset_id: number;
    job_type: string;
    status: string;
    description?: string | null;
    error_message?: string | null;
};

export type ExperimentDetail = ExperimentSummary & {
    jobs: ExperimentJob[];
    created_at?: string;
};

export type InsightCandidate = {
    id: number;
    experiment_id: number;
    job_id?: number | null;
    dataset_id: number;
    title: string;
    description: string;
    metrics?: Record<string, unknown> | null;
    adopted: boolean;
    feedback_comment?: string | null;
};
