"""
Celery Task Queue
Orchestrates parallel processing of SEC filings
"""
import logging
from typing import Dict, Any, List, Optional
from celery import Celery, group, chain, chord
from celery.result import AsyncResult
import asyncio

from config.settings import get_settings
from src.data.sec_edgar_connector import SECEdgarConnector
from src.signals.signal_extractor import SignalExtractionEngine
from src.models.model_router import ModelRouter
from src.data.database_connectors import SupabaseConnector, DuckDBConnector

logger = logging.getLogger(__name__)

# Initialize Celery
settings = get_settings().celery
app = Celery(
    'sec_analysis',
    broker=settings.broker_url,
    backend=settings.result_backend
)

# Configure Celery
app.conf.update(
    task_serializer=settings.task_serializer,
    result_serializer=settings.result_serializer,
    accept_content=settings.accept_content,
    timezone=settings.timezone,
    enable_utc=settings.enable_utc,
    worker_prefetch_multiplier=settings.worker_prefetch_multiplier,
    task_default_rate_limit=settings.task_default_rate_limit
)


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_company_filings_task(
    self,
    cik: str,
    form_type: str = "10-K",
    count: int = 10
) -> List[Dict[str, Any]]:
    """
    Celery task: Fetch company filings

    Args:
        cik: Company CIK
        form_type: Filing type
        count: Number of filings

    Returns:
        List of filing metadata
    """
    try:
        logger.info(f"Fetching {count} {form_type} filings for CIK {cik}")

        # Run async connector in sync context
        async def _fetch():
            async with SECEdgarConnector() as connector:
                return await connector.fetch_company_filings(cik, form_type, count)

        filings = asyncio.run(_fetch())
        logger.info(f"Fetched {len(filings)} filings for CIK {cik}")
        return filings

    except Exception as e:
        logger.error(f"Failed to fetch filings for CIK {cik}: {e}")
        self.retry(exc=e)


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_and_parse_filing_task(
    self,
    document_url: str,
    filing_metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Celery task: Fetch and parse filing content

    Args:
        document_url: URL to filing document
        filing_metadata: Filing metadata

    Returns:
        Parsed filing data
    """
    try:
        logger.info(f"Fetching and parsing {document_url}")

        async def _fetch_and_parse():
            async with SECEdgarConnector() as connector:
                content = await connector.fetch_filing_content(document_url)
                parsed = await connector.parse_filing_content(content)
                # Merge with metadata
                parsed.update(filing_metadata)
                return parsed

        parsed_filing = asyncio.run(_fetch_and_parse())
        logger.info(f"Parsed filing: {len(parsed_filing.get('sections', {}))} sections")
        return parsed_filing

    except Exception as e:
        logger.error(f"Failed to parse filing {document_url}: {e}")
        self.retry(exc=e)


@app.task(bind=True, max_retries=2)
def extract_signals_task(
    self,
    filing_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Celery task: Extract signals from filing

    Args:
        filing_data: Parsed filing data

    Returns:
        Extracted signals with metadata
    """
    try:
        logger.info(f"Extracting signals from filing {filing_data.get('accession_number')}")

        engine = SignalExtractionEngine()
        signals = engine.extract_all_signals(filing_data)

        # Convert signals to serializable format
        serializable_signals = {}
        for category, category_signals in signals.items():
            serializable_signals[category.value] = [
                {
                    "name": signal.name,
                    "category": signal.category.value,
                    "value": signal.value,
                    "confidence": signal.confidence,
                    "metadata": signal.metadata
                }
                for signal in category_signals
            ]

        result = {
            "filing_metadata": {
                "cik": filing_data.get("cik"),
                "form_type": filing_data.get("form_type"),
                "filing_date": filing_data.get("filing_date"),
                "accession_number": filing_data.get("accession_number")
            },
            "signals": serializable_signals,
            "signal_counts": {
                category: len(signals_list)
                for category, signals_list in serializable_signals.items()
            }
        }

        logger.info(f"Extracted {sum(result['signal_counts'].values())} total signals")
        return result

    except Exception as e:
        logger.error(f"Failed to extract signals: {e}")
        self.retry(exc=e)


@app.task(bind=True, max_retries=2)
def analyze_signals_task(
    self,
    filing_data: Dict[str, Any],
    extracted_signals: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Celery task: Analyze signals with Claude model

    Args:
        filing_data: Parsed filing data
        extracted_signals: Extracted signals

    Returns:
        Analysis results
    """
    try:
        logger.info(f"Analyzing signals for {filing_data.get('accession_number')}")

        async def _analyze():
            router = ModelRouter()
            # Reconstruct signals (simplified - would need proper deserialization)
            signals = extracted_signals.get("signals", {})
            return await router.analyze_signals(filing_data, signals)

        analysis = asyncio.run(_analyze())
        logger.info(f"Completed analysis using {analysis.get('model_used')}")
        return analysis

    except Exception as e:
        logger.error(f"Failed to analyze signals: {e}")
        self.retry(exc=e)


@app.task(bind=True, max_retries=3)
def store_results_task(
    self,
    filing_data: Dict[str, Any],
    signals: Dict[str, Any],
    analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Celery task: Store results in databases

    Args:
        filing_data: Filing metadata
        signals: Extracted signals
        analysis: Analysis results

    Returns:
        Storage confirmation
    """
    try:
        logger.info(f"Storing results for {filing_data.get('accession_number')}")

        # Store in both Supabase and DuckDB
        supabase = SupabaseConnector()
        duckdb = DuckDBConnector()

        # Store in Supabase (cloud)
        supabase_id = supabase.store_filing_analysis(
            filing_data=filing_data,
            signals=signals,
            analysis=analysis
        )

        # Store in DuckDB (local)
        duckdb.store_filing_analysis(
            filing_data=filing_data,
            signals=signals,
            analysis=analysis
        )

        logger.info(f"Stored results: Supabase ID {supabase_id}")
        return {
            "supabase_id": supabase_id,
            "duckdb_stored": True,
            "filing": filing_data.get('accession_number')
        }

    except Exception as e:
        logger.error(f"Failed to store results: {e}")
        self.retry(exc=e)


# ========================================
# WORKFLOW ORCHESTRATION
# ========================================

@app.task
def process_single_filing_workflow(
    document_url: str,
    filing_metadata: Dict[str, Any]
) -> str:
    """
    Complete workflow for processing a single filing

    Args:
        document_url: URL to filing
        filing_metadata: Filing metadata

    Returns:
        Task ID for tracking
    """
    # Create task chain
    workflow = chain(
        fetch_and_parse_filing_task.s(document_url, filing_metadata),
        extract_signals_task.s(),
        group(
            analyze_signals_task.s(),
            store_results_task.s()
        )
    )

    result = workflow.apply_async()
    logger.info(f"Started single filing workflow: {result.id}")
    return result.id


@app.task
def process_company_filings_workflow(
    cik: str,
    form_type: str = "10-K",
    count: int = 10
) -> str:
    """
    Complete workflow for processing multiple company filings

    Args:
        cik: Company CIK
        form_type: Filing type
        count: Number of filings to process

    Returns:
        Task ID for tracking
    """
    # Fetch filings first
    filings = fetch_company_filings_task.apply_async(
        args=[cik, form_type, count]
    )

    # Then process each filing in parallel
    def create_filing_workflows(filings_list):
        """Create parallel workflows for each filing"""
        filing_tasks = []
        for filing in filings_list:
            task = process_single_filing_workflow.s(
                filing['document_url'],
                filing
            )
            filing_tasks.append(task)
        return group(filing_tasks)

    # Use callback to process filings after fetch
    workflow = chain(
        filings,
        create_filing_workflows.s()
    )

    result = workflow.apply_async()
    logger.info(f"Started company filings workflow for CIK {cik}: {result.id}")
    return result.id


@app.task
def process_batch_companies_workflow(
    cik_list: List[str],
    form_type: str = "10-K",
    count_per_company: int = 5
) -> str:
    """
    Process multiple companies in parallel

    Args:
        cik_list: List of company CIKs
        form_type: Filing type
        count_per_company: Filings per company

    Returns:
        Task ID for tracking
    """
    # Create parallel company workflows
    company_tasks = group([
        process_company_filings_workflow.s(cik, form_type, count_per_company)
        for cik in cik_list
    ])

    result = company_tasks.apply_async()
    logger.info(f"Started batch processing for {len(cik_list)} companies: {result.id}")
    return result.id


# ========================================
# TASK MONITORING
# ========================================

def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get status of a task

    Args:
        task_id: Celery task ID

    Returns:
        Task status information
    """
    result = AsyncResult(task_id, app=app)

    status_info = {
        "task_id": task_id,
        "state": result.state,
        "ready": result.ready(),
        "successful": result.successful() if result.ready() else None
    }

    if result.ready():
        if result.successful():
            status_info["result"] = result.result
        else:
            status_info["error"] = str(result.info)

    return status_info


def cancel_task(task_id: str) -> bool:
    """
    Cancel a running task

    Args:
        task_id: Celery task ID

    Returns:
        True if cancelled successfully
    """
    result = AsyncResult(task_id, app=app)
    result.revoke(terminate=True)
    logger.info(f"Cancelled task {task_id}")
    return True


# ========================================
# PERIODIC TASKS (Optional)
# ========================================

@app.task
def cleanup_old_tasks():
    """Clean up old task results (can be scheduled)"""
    # Implementation for cleanup
    logger.info("Cleaning up old task results")
    pass


@app.task
def health_check():
    """Periodic health check task"""
    return {
        "status": "healthy",
        "workers": app.control.inspect().active(),
        "timestamp": asyncio.get_event_loop().time()
    }
