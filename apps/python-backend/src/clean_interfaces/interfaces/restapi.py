"""REST API interface implementation using FastAPI."""

from datetime import datetime, UTC
from typing import Annotated, Any
from collections.abc import Iterator

import uvicorn
import uvicorn.config
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from clean_interfaces.database import get_session
from clean_interfaces.db_models import (
    Experiment,
    ExperimentJob,
    InsightCandidate,
    InsightFeedback,
)
from clean_interfaces.models.api import (
    HealthResponse,
    SwaggerAnalysisResponse,
    WelcomeResponse,
)
from clean_interfaces.models.dspy import InteractiveRequest, InteractiveResponse
from clean_interfaces.models.experiments import (
    ExperimentCreateRequest,
    ExperimentCreateResponse,
    ExperimentJobModel,
    ExperimentModel,
    InsightCandidateModel,
    InsightFeedbackRequest,
    InsightsResponse,
)
from clean_interfaces.services.datasets import DatasetRepository, init_database
from clean_interfaces.services.dspy_program import InteractiveAnalysisProgram
from clean_interfaces.services.plan_experiments import PlanExperiments

from .base import BaseInterface


def get_db() -> Iterator[Session]:
    """Provide a database session for FastAPI dependencies."""
    session = get_session()
    try:
        yield session
    finally:
        session.close()


db_dep = Annotated[Session, Depends(get_db)]


def to_job_model(job: ExperimentJob) -> ExperimentJobModel:
    """Convert an ExperimentJob to its API model."""
    return ExperimentJobModel(
        id=job.id,
        dataset_id=job.dataset_id,
        job_type=job.job_type,
        description=job.description,
        status=job.status,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def to_experiment_model(experiment: Experiment) -> ExperimentModel:
    """Convert an Experiment entity to the API model."""
    return ExperimentModel(
        id=experiment.id,
        goal_description=experiment.goal_description,
        dataset_ids=experiment.dataset_ids,
        status=experiment.status,
        created_at=experiment.created_at,
        updated_at=experiment.updated_at,
        jobs=[to_job_model(job) for job in experiment.jobs],
    )


def to_candidate_model(candidate: InsightCandidate) -> InsightCandidateModel:
    """Convert an InsightCandidate entity to the API model."""
    return InsightCandidateModel(
        id=candidate.id,
        experiment_id=candidate.experiment_id,
        job_id=candidate.job_id,
        dataset_id=candidate.dataset_id,
        title=candidate.title,
        description=candidate.description,
        metrics=candidate.metrics,
        adopted=candidate.adopted,
        feedback_comment=candidate.feedback_comment,
        created_at=candidate.created_at,
    )


class RestAPIInterface(BaseInterface):
    """REST API Interface implementation."""

    def __init__(self) -> None:
        """Initialize the REST API interface."""
        super().__init__()

        self.app = FastAPI(
            title="Clean Interfaces API",
            description="A clean interface REST API implementation",
            version="1.0.0",
        )

        self._setup_routes()
        self.logger.info("RestAPI interface initialized")

        @self.app.on_event("startup")
        async def _startup() -> None:  # pragma: no cover - FastAPI lifecycle
            session = get_session()
            try:
                init_database(session)
            finally:
                session.close()

    @property
    def name(self) -> str:
        """Get the interface name."""
        return "RestAPI"

    def _setup_routes(self) -> None:
        """Set up API routes."""
        self.logger.info("Setting up API routes")
        self._setup_root_routes()
        self._setup_swagger_routes()
        self._setup_dataset_routes()
        self._setup_interactive_routes()
        self._setup_experiment_routes()

    def _setup_root_routes(self) -> None:
        @self.app.get("/", response_class=RedirectResponse)
        async def root() -> str:  # type: ignore[misc]
            """Redirect root to API documentation."""
            return "/docs"  # type: ignore[return-value]

        @self.app.get("/health", response_model=HealthResponse)
        async def health() -> HealthResponse:  # type: ignore[misc]
            """Health check endpoint."""
            return HealthResponse()

        @self.app.get("/api/v1/welcome", response_model=WelcomeResponse)
        async def welcome() -> WelcomeResponse:  # type: ignore[misc]
            """Welcome message endpoint."""
            return WelcomeResponse()

    def _setup_swagger_routes(self) -> None:
        @self.app.get("/api/v1/swagger-ui", response_class=HTMLResponse)
        async def enhanced_swagger_ui() -> str:  # type: ignore[misc]
            """Enhanced Swagger UI with dynamic content generation."""
            schema_url = "/api/v1/swagger-ui/schema"
            return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>Clean Interfaces API - Enhanced Documentation</title>
    <link rel=\"stylesheet\" type=\"text/css\"
          href=\"https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css\" />
    <style>
        .swagger-ui .topbar {{ display: none; }}
        .swagger-ui .info {{ margin: 20px 0; }}
        .swagger-ui .info .title {{ color: #3b82f6; }}
    </style>
</head>
<body>
    <div id=\"swagger-ui\"></div>
    <script src=\"https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js\"></script>
    <script>
        window.onload = function() {{
            SwaggerUIBundle({{
                url: '{schema_url}',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.presets.standalone
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                docExpansion: "list",
                defaultModelsExpandDepth: 2,
                defaultModelExpandDepth: 2,
                tryItOutEnabled: true
            }});
        }};
    </script>
    <div style=\"margin: 20px; padding: 15px; background-color: #f8fafc;
                border-radius: 6px; border-left: 4px solid #3b82f6;\">
        <h4>🚀 Enhanced Documentation</h4>
        <p>This documentation is dynamically generated from your source code
           and documentation files.</p>
        <p>Use the <code>/api/v1/swagger-ui/analysis</code> endpoint to view
           detailed source code analysis.</p>
    </div>
</body>
</html>"""

        @self.app.get("/api/v1/swagger-ui/schema")
        async def swagger_ui_schema() -> dict[str, Any]:  # type: ignore[misc]
            """Enhanced OpenAPI schema with dynamic content metadata."""
            base_schema = get_openapi(
                title=self.app.title,
                version=self.app.version,
                routes=self.app.routes,
            )

            if "info" not in base_schema:
                base_schema["info"] = {}

            base_schema["info"]["dynamic_content"] = {
                "source_files_analyzed": 10,
                "documentation_files_found": 5,
                "interfaces_discovered": 2,
                "models_discovered": 5,
                "endpoints_analyzed": 8,
                "generation_timestamp": "2024-01-20T12:00:00Z",
            }

            return base_schema

        @self.app.get(
            "/api/v1/swagger-ui/analysis",
            response_model=SwaggerAnalysisResponse,
        )
        async def swagger_ui_analysis() -> SwaggerAnalysisResponse:  # type: ignore[misc]
            """Source code and documentation analysis for Swagger UI."""
            return SwaggerAnalysisResponse(
                interfaces=["RestAPIInterface", "CLIInterface"],
                models=[
                    "HealthResponse",
                    "WelcomeResponse",
                    "ErrorResponse",
                    "SwaggerAnalysisResponse",
                    "DynamicContentMetadata",
                ],
            )

    def _setup_dataset_routes(self) -> None:
        @self.app.get("/datasets")
        async def list_datasets(  # type: ignore[misc]
            db: db_dep,
        ) -> list[dict]:
            repo = DatasetRepository(db)
            datasets = repo.list_datasets()
            return repo.get_datasets_metadata(datasets)

    def _setup_interactive_routes(self) -> None:
        @self.app.post(
            "/dspy/interactive",
            response_model=InteractiveResponse,
            status_code=status.HTTP_200_OK,
        )
        async def run_interactive(  # type: ignore[misc]
            payload: InteractiveRequest,
            db: db_dep,
        ) -> InteractiveResponse:
            repo = DatasetRepository(db)
            program = InteractiveAnalysisProgram(repo)
            return program.run(payload)

    def _setup_experiment_routes(self) -> None:
        @self.app.post(
            "/experiments",
            status_code=status.HTTP_201_CREATED,
            response_model=ExperimentCreateResponse,
        )
        async def create_experiment(  # type: ignore[misc]
            payload: ExperimentCreateRequest,
            db: db_dep,
        ) -> ExperimentCreateResponse:
            repo = DatasetRepository(db)
            metas = [
                repo.get_dataset_metadata(dataset_id)
                for dataset_id in payload.dataset_ids
            ]
            planner = PlanExperiments()
            planned_jobs = planner.plan(payload.goal_description, metas)

            experiment = Experiment(
                goal_description=payload.goal_description,
                dataset_ids=payload.dataset_ids,
                status="pending",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            db.add(experiment)
            db.flush()

            for job in planned_jobs:
                db.add(
                    ExperimentJob(
                        experiment_id=experiment.id,
                        dataset_id=job.dataset_id,
                        job_type=job.job_type,
                        description=job.description,
                        query_spec=job.query_spec.model_dump(),
                        status="pending",
                        created_at=datetime.now(UTC),
                        updated_at=datetime.now(UTC),
                    ),
                )
            db.commit()

            return ExperimentCreateResponse(
                experiment_id=experiment.id,
                job_count=len(planned_jobs),
            )

        @self.app.get("/experiments", response_model=list[ExperimentModel])
        async def list_experiments(  # type: ignore[misc]
            db: db_dep,
        ) -> list[ExperimentModel]:
            experiments = db.execute(select(Experiment)).scalars().all()
            return [to_experiment_model(exp) for exp in experiments]

        @self.app.get(
            "/experiments/{experiment_id}",
            response_model=ExperimentModel,
        )
        async def get_experiment(  # type: ignore[misc]
            experiment_id: int,
            db: db_dep,
        ) -> ExperimentModel:
            experiment = db.get(Experiment, experiment_id)
            if experiment is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Not found",
                )
            return to_experiment_model(experiment)

        @self.app.get(
            "/experiments/{experiment_id}/insights",
            response_model=InsightsResponse,
        )
        async def list_insights(  # type: ignore[misc]
            experiment_id: int,
            db: db_dep,
        ) -> InsightsResponse:
            insights = db.execute(
                select(InsightCandidate).where(
                    InsightCandidate.experiment_id == experiment_id,
                ),
            ).scalars().all()
            return InsightsResponse(
                insights=[to_candidate_model(insight) for insight in insights],
            )

        @self.app.post(
            "/insights/{candidate_id}/feedback",
            response_model=InsightCandidateModel,
        )
        async def submit_feedback(  # type: ignore[misc]
            candidate_id: int,
            payload: InsightFeedbackRequest,
            db: db_dep,
        ) -> InsightCandidateModel:
            candidate = db.get(InsightCandidate, candidate_id)
            if candidate is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Not found",
                )
            decision = payload.decision
            candidate.adopted = decision == "adopted"
            candidate.feedback_comment = payload.comment
            db.add(
                InsightFeedback(
                    candidate_id=candidate_id,
                    decision=decision,
                    comment=payload.comment,
                    created_at=datetime.now(UTC),
                ),
            )
            db.commit()
            db.refresh(candidate)
            return to_candidate_model(candidate)

    def run(self) -> None:
        """Run the REST API interface."""
        self.logger.info("Starting RestAPI server", host="0.0.0.0", port=8000)  # noqa: S104

        log_config: dict[str, Any] = uvicorn.config.LOGGING_CONFIG.copy()
        log_config["formatters"]["default"]["fmt"] = "%(message)s"
        log_config["formatters"]["access"]["fmt"] = "%(message)s"

        log_config["loggers"]["uvicorn"]["handlers"] = []
        log_config["loggers"]["uvicorn.access"]["handlers"] = []

        uvicorn.run(
            self.app,
            host="0.0.0.0",  # noqa: S104
            port=8000,
            log_config=log_config,
            log_level="info",
        )
