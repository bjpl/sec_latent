"""
Database Connectors
Supabase (cloud) and DuckDB (local) connectors
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import duckdb
from supabase import create_client, Client
import json

from config.settings import get_settings

logger = logging.getLogger(__name__)


class SupabaseConnector:
    """
    Supabase cloud database connector
    For persistent storage and real-time features
    """

    def __init__(self):
        settings = get_settings().database
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_key
        )
        logger.info("Initialized Supabase connector")

    def store_filing_analysis(
        self,
        filing_data: Dict[str, Any],
        signals: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> str:
        """
        Store complete filing analysis

        Args:
            filing_data: Filing metadata
            signals: Extracted signals
            analysis: Analysis results

        Returns:
            Record ID
        """
        try:
            # Prepare record
            record = {
                "cik": filing_data.get("cik"),
                "form_type": filing_data.get("form_type"),
                "filing_date": filing_data.get("filing_date"),
                "accession_number": filing_data.get("accession_number"),
                "document_url": filing_data.get("document_url"),
                "signals": json.dumps(signals),
                "analysis": json.dumps(analysis),
                "created_at": datetime.utcnow().isoformat(),
                "signal_count": sum(len(s) for s in signals.values()) if signals else 0,
                "model_used": analysis.get("model_used") if analysis else None
            }

            # Insert into filings table
            result = self.client.table("filings").insert(record).execute()

            record_id = result.data[0]["id"]
            logger.info(f"Stored filing analysis in Supabase: {record_id}")
            return record_id

        except Exception as e:
            logger.error(f"Failed to store in Supabase: {e}")
            raise

    def get_filing_analysis(self, accession_number: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve filing analysis by accession number

        Args:
            accession_number: SEC accession number

        Returns:
            Filing analysis or None
        """
        try:
            result = self.client.table("filings").select("*").eq(
                "accession_number", accession_number
            ).execute()

            if result.data:
                record = result.data[0]
                # Parse JSON fields
                record["signals"] = json.loads(record["signals"])
                record["analysis"] = json.loads(record["analysis"])
                return record

            return None

        except Exception as e:
            logger.error(f"Failed to retrieve from Supabase: {e}")
            raise

    def search_filings(
        self,
        cik: Optional[str] = None,
        form_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search filings with filters

        Args:
            cik: Company CIK
            form_type: Filing form type
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            limit: Maximum results

        Returns:
            List of matching filings
        """
        try:
            query = self.client.table("filings").select("*")

            if cik:
                query = query.eq("cik", cik)
            if form_type:
                query = query.eq("form_type", form_type)
            if start_date:
                query = query.gte("filing_date", start_date)
            if end_date:
                query = query.lte("filing_date", end_date)

            query = query.limit(limit)
            result = query.execute()

            # Parse JSON fields
            filings = []
            for record in result.data:
                record["signals"] = json.loads(record["signals"])
                record["analysis"] = json.loads(record["analysis"])
                filings.append(record)

            logger.info(f"Found {len(filings)} filings matching criteria")
            return filings

        except Exception as e:
            logger.error(f"Failed to search Supabase: {e}")
            raise

    def get_company_signals_summary(self, cik: str) -> Dict[str, Any]:
        """
        Get aggregated signals summary for a company

        Args:
            cik: Company CIK

        Returns:
            Signals summary
        """
        try:
            # Get all filings for company
            filings = self.search_filings(cik=cik, limit=1000)

            # Aggregate signals
            total_filings = len(filings)
            signal_trends = {}

            for filing in filings:
                signals = filing.get("signals", {})
                for category, category_signals in signals.items():
                    if category not in signal_trends:
                        signal_trends[category] = []
                    signal_trends[category].append({
                        "date": filing["filing_date"],
                        "count": len(category_signals)
                    })

            return {
                "cik": cik,
                "total_filings": total_filings,
                "signal_trends": signal_trends,
                "date_range": {
                    "start": min(f["filing_date"] for f in filings) if filings else None,
                    "end": max(f["filing_date"] for f in filings) if filings else None
                }
            }

        except Exception as e:
            logger.error(f"Failed to get company summary: {e}")
            raise


class DuckDBConnector:
    """
    DuckDB local database connector
    For fast analytical queries and local storage
    """

    def __init__(self):
        settings = get_settings().database
        self.db_path = settings.duckdb_path
        self.connection = None
        self._initialize_db()
        logger.info(f"Initialized DuckDB connector at {self.db_path}")

    def _initialize_db(self):
        """Initialize DuckDB database and schema"""
        self.connection = duckdb.connect(self.db_path)

        # Set memory limit
        settings = get_settings().database
        self.connection.execute(f"SET memory_limit='{settings.duckdb_memory_limit}'")

        # Create tables
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS filings (
                id INTEGER PRIMARY KEY,
                cik VARCHAR,
                form_type VARCHAR,
                filing_date DATE,
                accession_number VARCHAR UNIQUE,
                document_url VARCHAR,
                signals JSON,
                analysis JSON,
                signal_count INTEGER,
                model_used VARCHAR,
                created_at TIMESTAMP,
                INDEX idx_cik (cik),
                INDEX idx_filing_date (filing_date),
                INDEX idx_form_type (form_type)
            )
        """)

        # Create signals table for efficient querying
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY,
                filing_id INTEGER,
                signal_name VARCHAR,
                signal_category VARCHAR,
                signal_value VARCHAR,
                confidence FLOAT,
                metadata JSON,
                INDEX idx_filing_id (filing_id),
                INDEX idx_signal_name (signal_name),
                INDEX idx_category (signal_category)
            )
        """)

        logger.info("DuckDB schema initialized")

    def store_filing_analysis(
        self,
        filing_data: Dict[str, Any],
        signals: Dict[str, Any],
        analysis: Dict[str, Any]
    ):
        """
        Store filing analysis in DuckDB

        Args:
            filing_data: Filing metadata
            signals: Extracted signals
            analysis: Analysis results
        """
        try:
            # Insert filing
            self.connection.execute("""
                INSERT OR REPLACE INTO filings (
                    cik, form_type, filing_date, accession_number,
                    document_url, signals, analysis, signal_count,
                    model_used, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                filing_data.get("cik"),
                filing_data.get("form_type"),
                filing_data.get("filing_date"),
                filing_data.get("accession_number"),
                filing_data.get("document_url"),
                json.dumps(signals),
                json.dumps(analysis),
                sum(len(s) for s in signals.values()) if signals else 0,
                analysis.get("model_used") if analysis else None,
                datetime.utcnow().isoformat()
            ])

            # Get filing ID
            filing_id = self.connection.execute(
                "SELECT id FROM filings WHERE accession_number = ?",
                [filing_data.get("accession_number")]
            ).fetchone()[0]

            # Insert individual signals for querying
            for category, category_signals in signals.items():
                for signal in category_signals:
                    self.connection.execute("""
                        INSERT INTO signals (
                            filing_id, signal_name, signal_category,
                            signal_value, confidence, metadata
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, [
                        filing_id,
                        signal.get("name"),
                        category,
                        str(signal.get("value")),
                        signal.get("confidence", 1.0),
                        json.dumps(signal.get("metadata", {}))
                    ])

            logger.info(f"Stored filing analysis in DuckDB: {filing_data.get('accession_number')}")

        except Exception as e:
            logger.error(f"Failed to store in DuckDB: {e}")
            raise

    def query_signals(
        self,
        signal_name: Optional[str] = None,
        category: Optional[str] = None,
        cik: Optional[str] = None,
        min_confidence: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Query signals with filters

        Args:
            signal_name: Filter by signal name
            category: Filter by category
            cik: Filter by company CIK
            min_confidence: Minimum confidence threshold

        Returns:
            List of matching signals
        """
        query = """
            SELECT
                s.signal_name,
                s.signal_category,
                s.signal_value,
                s.confidence,
                s.metadata,
                f.cik,
                f.form_type,
                f.filing_date
            FROM signals s
            JOIN filings f ON s.filing_id = f.id
            WHERE s.confidence >= ?
        """
        params = [min_confidence]

        if signal_name:
            query += " AND s.signal_name = ?"
            params.append(signal_name)
        if category:
            query += " AND s.signal_category = ?"
            params.append(category)
        if cik:
            query += " AND f.cik = ?"
            params.append(cik)

        result = self.connection.execute(query, params).fetchall()

        # Convert to dictionaries
        columns = ["signal_name", "signal_category", "signal_value",
                   "confidence", "metadata", "cik", "form_type", "filing_date"]

        return [dict(zip(columns, row)) for row in result]

    def analyze_signal_trends(
        self,
        signal_name: str,
        cik: Optional[str] = None,
        lookback_months: int = 12
    ) -> Dict[str, Any]:
        """
        Analyze trends for a specific signal

        Args:
            signal_name: Signal to analyze
            cik: Optional company filter
            lookback_months: Months to look back

        Returns:
            Trend analysis
        """
        query = """
            SELECT
                f.filing_date,
                s.signal_value,
                s.confidence,
                f.cik,
                f.form_type
            FROM signals s
            JOIN filings f ON s.filing_id = f.id
            WHERE s.signal_name = ?
            AND f.filing_date >= date_sub(current_date, INTERVAL ? MONTH)
        """
        params = [signal_name, lookback_months]

        if cik:
            query += " AND f.cik = ?"
            params.append(cik)

        query += " ORDER BY f.filing_date"

        result = self.connection.execute(query, params).fetchall()

        return {
            "signal_name": signal_name,
            "data_points": len(result),
            "values": [
                {
                    "date": row[0],
                    "value": row[1],
                    "confidence": row[2],
                    "cik": row[3],
                    "form_type": row[4]
                }
                for row in result
            ]
        }

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Closed DuckDB connection")
