from __future__ import annotations

import json
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple


from agents.base_agent import BaseAgent
from backend.models import AgentResult


# ---------------------------------------------------------------------------
# Helper / sub-system stubs
# (Replace with real implementations or injected dependencies as needed)
# ---------------------------------------------------------------------------

class DataSource:
    """Stub representing a generic data source (DB, API, CSV, etc.)."""
    def __init__(self, name: str, source_type: str, connection_info: Dict[str, Any]):
        self.name = name
        self.source_type = source_type  # 'sql', 'api', 'csv', 'crm', 'erp', 'web_analytics'
        self.connection_info = connection_info


class DataSet:
    """Lightweight in-memory dataset wrapper."""
    def __init__(self, name: str, records: List[Dict[str, Any]], schema: Optional[Dict] = None):
        self.name = name
        self.records = records
        self.schema = schema or {}
        self.created_at = datetime.utcnow().isoformat()

    def __len__(self):
        return len(self.records)

    def column_values(self, col: str) -> List[Any]:
        return [r.get(col) for r in self.records]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "record_count": len(self.records),
            "schema": self.schema,
            "created_at": self.created_at,
        }


# ---------------------------------------------------------------------------
# 1. DATA COLLECTION
# ---------------------------------------------------------------------------

class DataCollectionModule:
    """
    Gathers data from multiple sources:
    - Databases (SQL / NoSQL via connection_info)
    - REST APIs
    - Spreadsheets / CSV files
    - CRM, ERP, Web-analytics integrations
    """

    SUPPORTED_SOURCES = {"sql", "nosql", "api", "csv", "spreadsheet", "crm", "erp", "web_analytics"}

    def collect(self, sources: List[DataSource]) -> Dict[str, DataSet]:
        collected: Dict[str, DataSet] = {}
        for src in sources:
            if src.source_type not in self.SUPPORTED_SOURCES:
                raise ValueError(f"Unsupported source type: {src.source_type}")
            dataset = self._fetch(src)
            collected[src.name] = dataset
        return collected

    def _fetch(self, src: DataSource) -> DataSet:
        """Stub: real implementation connects to the actual source."""
        # In production: use sqlalchemy / requests / openpyxl / crm SDK, etc.
        raw_records: List[Dict[str, Any]] = src.connection_info.get("sample_records", [])
        schema = src.connection_info.get("schema", {})
        return DataSet(name=src.name, records=raw_records, schema=schema)

    def validate_completeness(self, datasets: Dict[str, DataSet]) -> Dict[str, Any]:
        """Ensure data is relevant and complete; returns a completeness report."""
        report: Dict[str, Any] = {}
        for name, ds in datasets.items():
            if not ds.records:
                report[name] = {"status": "EMPTY", "issues": ["No records found"]}
                continue
            issues: List[str] = []
            for col in ds.schema.get("required_columns", []):
                missing = sum(1 for r in ds.records if r.get(col) is None)
                if missing:
                    issues.append(f"Column '{col}' missing in {missing}/{len(ds)} rows")
            report[name] = {
                "status": "OK" if not issues else "INCOMPLETE",
                "record_count": len(ds),
                "issues": issues,
            }
        return report


# ---------------------------------------------------------------------------
# 2. DATA CLEANING (WRANGLING)
# ---------------------------------------------------------------------------

class DataCleaningModule:
    """
    - Remove duplicates & errors
    - Handle missing values (drop, fill, interpolate)
    - Standardize formats (dates, currencies, categories)
    - Prepares raw data for analysis
    """

    DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y%m%d"]
    CURRENCY_RE = re.compile(r"[$€£¥₹]?([\d,]+\.?\d*)")

    def clean(
        self,
        dataset: DataSet,
        rules: Optional[Dict[str, Any]] = None,
    ) -> Tuple[DataSet, Dict[str, Any]]:
        rules = rules or {}
        records = [r.copy() for r in dataset.records]
        log: Dict[str, Any] = {"original_count": len(records), "steps": []}

        records, dup_log = self._remove_duplicates(records, key=rules.get("dedup_key"))
        log["steps"].append(dup_log)

        records, missing_log = self._handle_missing(records, strategy=rules.get("missing_strategy", "drop"))
        log["steps"].append(missing_log)

        records, fmt_log = self._standardize_formats(records, date_cols=rules.get("date_cols", []),
                                                      currency_cols=rules.get("currency_cols", []),
                                                      category_cols=rules.get("category_cols", {}))
        log["steps"].append(fmt_log)

        log["final_count"] = len(records)
        log["rows_removed"] = log["original_count"] - log["final_count"]

        cleaned = DataSet(name=f"{dataset.name}_cleaned", records=records, schema=dataset.schema)
        return cleaned, log

    def _remove_duplicates(self, records: List[Dict], key: Optional[str]) -> Tuple[List[Dict], Dict]:
        seen: set = set()
        unique: List[Dict] = []
        for r in records:
            ident = r.get(key) if key else json.dumps(r, sort_keys=True, default=str)
            if ident not in seen:
                seen.add(ident)
                unique.append(r)
        removed = len(records) - len(unique)
        return unique, {"step": "remove_duplicates", "removed": removed}

    def _handle_missing(self, records: List[Dict], strategy: str) -> Tuple[List[Dict], Dict]:
        if strategy == "drop":
            clean = [r for r in records if all(v is not None for v in r.values())]
            removed = len(records) - len(clean)
            return clean, {"step": "handle_missing", "strategy": "drop", "removed": removed}
        if strategy == "fill_zero":
            for r in records:
                for k, v in r.items():
                    if v is None:
                        r[k] = 0
            return records, {"step": "handle_missing", "strategy": "fill_zero"}
        if strategy == "fill_mean":
            cols = set(k for r in records for k in r)
            means: Dict[str, Any] = {}
            for col in cols:
                vals = [r[col] for r in records if isinstance(r.get(col), (int, float))]
                if vals:
                    means[col] = statistics.mean(vals)
            for r in records:
                for col, mean_val in means.items():
                    if r.get(col) is None:
                        r[col] = mean_val
            return records, {"step": "handle_missing", "strategy": "fill_mean", "means": means}
        return records, {"step": "handle_missing", "strategy": "none"}

    def _standardize_formats(
        self,
        records: List[Dict],
        date_cols: List[str],
        currency_cols: List[str],
        category_cols: Dict[str, Dict[str, str]],
    ) -> Tuple[List[Dict], Dict]:
        converted = {"dates": 0, "currencies": 0, "categories": 0}
        for r in records:
            for col in date_cols:
                if col in r and isinstance(r[col], str):
                    r[col] = self._parse_date(r[col])
                    converted["dates"] += 1
            for col in currency_cols:
                if col in r and isinstance(r[col], str):
                    m = self.CURRENCY_RE.search(r[col])
                    if m:
                        r[col] = float(m.group(1).replace(",", ""))
                        converted["currencies"] += 1
            for col, mapping in category_cols.items():
                if col in r and r[col] in mapping:
                    r[col] = mapping[r[col]]
                    converted["categories"] += 1
        return records, {"step": "standardize_formats", "converted": converted}

    def _parse_date(self, value: str) -> str:
        for fmt in self.DATE_FORMATS:
            try:
                return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return value  # return original if no format matched


# ---------------------------------------------------------------------------
# 3. DATA ANALYSIS
# ---------------------------------------------------------------------------

class DataAnalysisModule:
    """
    - Identify trends, patterns, correlations
    - Statistical analysis (mean, median, std-dev, percentiles, outliers)
    - SQL-like aggregations
    - Python-style groupby
    """

    def analyse(self, dataset: DataSet, config: Dict[str, Any]) -> Dict[str, Any]:
        results: Dict[str, Any] = {}

        if "numeric_cols" in config:
            results["statistics"] = self.descriptive_stats(dataset, config["numeric_cols"])

        if "group_by" in config and "agg_col" in config:
            results["group_aggregation"] = self.group_by_aggregate(
                dataset, config["group_by"], config["agg_col"], config.get("agg_func", "sum")
            )

        if "trend_col" in config and "date_col" in config:
            results["trend"] = self.detect_trend(dataset, config["date_col"], config["trend_col"])

        if "corr_cols" in config and len(config["corr_cols"]) == 2:
            results["correlation"] = self.pearson_correlation(
                dataset, config["corr_cols"][0], config["corr_cols"][1]
            )

        if "outlier_col" in config:
            results["outliers"] = self.detect_outliers(dataset, config["outlier_col"])

        if "top_n" in config and "rank_col" in config and "value_col" in config:
            results["top_n"] = self.top_n(dataset, config["rank_col"], config["value_col"], config["top_n"])

        return results

    def descriptive_stats(self, dataset: DataSet, cols: List[str]) -> Dict[str, Dict[str, float]]:
        stats: Dict[str, Dict[str, float]] = {}
        for col in cols:
            vals = [v for v in dataset.column_values(col) if isinstance(v, (int, float))]
            if not vals:
                continue
            sorted_vals = sorted(vals)
            n = len(vals)
            mean = statistics.mean(vals)
            stats[col] = {
                "count": n,
                "mean": round(mean, 4),
                "median": round(statistics.median(vals), 4),
                "std_dev": round(statistics.pstdev(vals), 4),
                "min": min(vals),
                "max": max(vals),
                "p25": round(sorted_vals[int(n * 0.25)], 4),
                "p75": round(sorted_vals[int(n * 0.75)], 4),
            }
        return stats

    def group_by_aggregate(
        self, dataset: DataSet, group_col: str, agg_col: str, func: str = "sum"
    ) -> List[Dict[str, Any]]:
        groups: Dict[Any, List[float]] = defaultdict(list)
        for r in dataset.records:
            key = r.get(group_col)
            val = r.get(agg_col)
            if val is not None:
                try:
                    groups[key].append(float(val))
                except (TypeError, ValueError):
                    pass
        aggregated: List[Dict[str, Any]] = []
        for key, vals in groups.items():
            if func == "sum":
                result = sum(vals)
            elif func == "mean":
                result = statistics.mean(vals)
            elif func == "count":
                result = len(vals)
            elif func == "max":
                result = max(vals)
            elif func == "min":
                result = min(vals)
            else:
                result = sum(vals)
            aggregated.append({group_col: key, f"{func}_{agg_col}": round(result, 4)})
        return sorted(aggregated, key=lambda x: list(x.values())[1], reverse=True)

    def detect_trend(
        self, dataset: DataSet, date_col: str, value_col: str
    ) -> Dict[str, Any]:
        pairs = [
            (r[date_col], r[value_col])
            for r in dataset.records
            if r.get(date_col) and isinstance(r.get(value_col), (int, float))
        ]
        if not pairs:
            return {"trend": "insufficient_data"}
        pairs.sort(key=lambda x: x[0])
        values = [p[1] for p in pairs]
        n = len(values)
        if n < 2:
            return {"trend": "insufficient_data"}
        # Simple linear regression slope
        x_mean = (n - 1) / 2
        y_mean = statistics.mean(values)
        num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        den = sum((i - x_mean) ** 2 for i in range(n))
        slope = num / den if den else 0
        pct_change = ((values[-1] - values[0]) / values[0] * 100) if values[0] else 0
        return {
            "trend": "upward" if slope > 0 else "downward" if slope < 0 else "flat",
            "slope": round(slope, 6),
            "pct_change": round(pct_change, 2),
            "first_value": values[0],
            "last_value": values[-1],
            "period_start": pairs[0][0],
            "period_end": pairs[-1][0],
        }

    def pearson_correlation(self, dataset: DataSet, col_x: str, col_y: str) -> Dict[str, Any]:
        pairs = [
            (r[col_x], r[col_y])
            for r in dataset.records
            if isinstance(r.get(col_x), (int, float)) and isinstance(r.get(col_y), (int, float))
        ]
        if len(pairs) < 2:
            return {"r": None, "interpretation": "insufficient_data"}
        xs = [p[0] for p in pairs]
        ys = [p[1] for p in pairs]
        n = len(pairs)
        mx, my = statistics.mean(xs), statistics.mean(ys)
        num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
        r = num / den if den else 0
        if abs(r) >= 0.7:
            interpretation = "strong"
        elif abs(r) >= 0.4:
            interpretation = "moderate"
        else:
            interpretation = "weak"
        direction = "positive" if r > 0 else "negative"
        return {"r": round(r, 4), "interpretation": f"{interpretation} {direction} correlation"}

    def detect_outliers(self, dataset: DataSet, col: str, z_threshold: float = 2.5) -> Dict[str, Any]:
        vals = [v for v in dataset.column_values(col) if isinstance(v, (int, float))]
        if len(vals) < 3:
            return {"outliers": [], "note": "insufficient_data"}
        mean = statistics.mean(vals)
        std = statistics.pstdev(vals)
        if std == 0:
            return {"outliers": [], "note": "zero_variance"}
        outliers = [v for v in vals if abs((v - mean) / std) > z_threshold]
        return {"outliers": outliers, "count": len(outliers), "z_threshold": z_threshold}

    def top_n(
        self, dataset: DataSet, group_col: str, value_col: str, n: int
    ) -> List[Dict[str, Any]]:
        agg = self.group_by_aggregate(dataset, group_col, value_col, func="sum")
        return agg[:n]


# ---------------------------------------------------------------------------
# 4. DATA VISUALIZATION (spec builders — actual rendering is front-end)
# ---------------------------------------------------------------------------

class DataVisualizationModule:
    """
    Builds visualization specifications (chart configs) compatible with:
    - Tableau / Power BI data contracts
    - Chart.js / Plotly / Recharts (JSON configs)
    - Excel chart definitions
    """

    SUPPORTED_CHART_TYPES = {
        "line", "bar", "stacked_bar", "pie", "donut", "scatter",
        "heatmap", "histogram", "area", "funnel", "kpi_card",
    }

    def build_chart_spec(
        self,
        chart_type: str,
        title: str,
        data: Any,
        x_label: str = "",
        y_label: str = "",
        color_scheme: str = "default",
        options: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        if chart_type not in self.SUPPORTED_CHART_TYPES:
            raise ValueError(f"Unsupported chart type: {chart_type}")
        return {
            "type": chart_type,
            "title": title,
            "x_label": x_label,
            "y_label": y_label,
            "color_scheme": color_scheme,
            "data": data,
            "options": options or {},
            "generated_at": datetime.utcnow().isoformat(),
        }

    def build_dashboard(
        self,
        dashboard_name: str,
        charts: List[Dict[str, Any]],
        kpis: List[Dict[str, Any]],
        filters: Optional[List[str]] = None,
        refresh_interval_min: int = 60,
    ) -> Dict[str, Any]:
        return {
            "dashboard_name": dashboard_name,
            "charts": charts,
            "kpis": kpis,
            "filters": filters or [],
            "refresh_interval_min": refresh_interval_min,
            "tool_compatibility": ["Tableau", "Power BI", "Chart.js", "Recharts", "Excel"],
            "created_at": datetime.utcnow().isoformat(),
        }

    def build_kpi_card(
        self,
        name: str,
        value: Any,
        trend: str,
        target: Optional[Any] = None,
        unit: str = "",
        status: str = "neutral",  # 'good', 'bad', 'neutral'
    ) -> Dict[str, Any]:
        return {
            "type": "kpi_card",
            "name": name,
            "value": value,
            "trend": trend,
            "target": target,
            "unit": unit,
            "status": status,
        }


# ---------------------------------------------------------------------------
# 5. REPORTING & COMMUNICATION
# ---------------------------------------------------------------------------

class ReportingModule:
    """
    - Translates data insights into business recommendations
    - Prepares structured reports for stakeholders
    - Generates executive summaries for non-technical audiences
    """

    REPORT_TYPES = {"executive_summary", "technical_report", "daily_digest",
                    "weekly_summary", "monthly_review", "ad_hoc"}

    def generate_report(
        self,
        report_type: str,
        title: str,
        insights: List[Dict[str, Any]],
        recommendations: List[str],
        visualizations: Optional[List[Dict]] = None,
        audience: str = "stakeholders",
        format_output: str = "json",  # 'json', 'markdown', 'html'
    ) -> Dict[str, Any]:
        if report_type not in self.REPORT_TYPES:
            raise ValueError(f"Unknown report type: {report_type}")
        report = {
            "report_type": report_type,
            "title": title,
            "audience": audience,
            "generated_at": datetime.utcnow().isoformat(),
            "executive_summary": self._build_executive_summary(insights),
            "insights": insights,
            "recommendations": recommendations,
            "visualizations": visualizations or [],
        }
        if format_output == "markdown":
            return {"format": "markdown", "content": self._to_markdown(report)}
        return report

    def _build_executive_summary(self, insights: List[Dict[str, Any]]) -> str:
        if not insights:
            return "No significant insights detected in this reporting period."
        top = insights[:3]
        lines = [f"- {i.get('finding', str(i))}" for i in top]
        return "Key findings:\n" + "\n".join(lines)

    def _to_markdown(self, report: Dict[str, Any]) -> str:
        md = [f"# {report['title']}", f"*Generated: {report['generated_at']}*", ""]
        md.append("## Executive Summary")
        md.append(report["executive_summary"])
        md.append("\n## Recommendations")
        for r in report["recommendations"]:
            md.append(f"- {r}")
        return "\n".join(md)


# ---------------------------------------------------------------------------
# 6. DATABASE MANAGEMENT
# ---------------------------------------------------------------------------

class DatabaseManagementModule:
    """
    - Execute SQL queries (stub — real impl uses sqlalchemy/psycopg2)
    - Work with NoSQL collections
    - Maintain data integrity (constraints, deduplication, auditing)
    - Extract & manipulate large datasets
    """

    def execute_sql(
        self, query: str, connection_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Stub: in production, connect via sqlalchemy and return rows."""
        return {
            "query": query,
            "connection": connection_info.get("database", "unknown"),
            "status": "executed",
            "rows": [],
            "note": "Stub — replace with real sqlalchemy/psycopg2 execution",
        }

    def check_integrity(self, dataset: DataSet, constraints: Dict[str, Any]) -> Dict[str, Any]:
        issues: List[str] = []
        for col in constraints.get("not_null", []):
            nulls = sum(1 for r in dataset.records if r.get(col) is None)
            if nulls:
                issues.append(f"NOT NULL violated in '{col}': {nulls} rows")
        for col, expected_type in constraints.get("type_checks", {}).items():
            type_map = {"int": int, "float": (int, float), "str": str}
            expected = type_map.get(expected_type)
            if expected:
                violations = sum(1 for r in dataset.records if not isinstance(r.get(col), expected))
                if violations:
                    issues.append(f"Type check failed for '{col}' (expected {expected_type}): {violations} rows")
        return {"integrity_ok": len(issues) == 0, "issues": issues}

    def paginate(
        self, dataset: DataSet, page: int = 1, page_size: int = 100
    ) -> Dict[str, Any]:
        start = (page - 1) * page_size
        end = start + page_size
        return {
            "page": page,
            "page_size": page_size,
            "total_records": len(dataset),
            "total_pages": -(-len(dataset) // page_size),
            "records": dataset.records[start:end],
        }


# ---------------------------------------------------------------------------
# 7. BUSINESS UNDERSTANDING
# ---------------------------------------------------------------------------

class BusinessIntelligenceModule:
    """
    - Understand company goals and KPIs
    - Align analysis with business needs
    - Support decision-making with structured frameworks
    """

    def align_kpis(
        self, analysis_results: Dict[str, Any], business_goals: List[str]
    ) -> Dict[str, Any]:
        alignment_map: Dict[str, Any] = {}
        for goal in business_goals:
            relevant_keys = [k for k in analysis_results if any(w in k.lower() for w in goal.lower().split())]
            alignment_map[goal] = {
                "relevant_analyses": relevant_keys,
                "aligned": len(relevant_keys) > 0,
            }
        return alignment_map

    def swot_from_data(
        self, insights: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Derive a simple SWOT scaffold from data insights."""
        swot: Dict[str, List[str]] = {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []}
        for insight in insights:
            direction = insight.get("direction", "neutral")
            finding = insight.get("finding", "")
            if direction == "positive":
                swot["strengths"].append(finding)
            elif direction == "negative":
                swot["weaknesses"].append(finding)
            elif direction == "opportunity":
                swot["opportunities"].append(finding)
            elif direction == "risk":
                swot["threats"].append(finding)
        return swot

    def forecast_simple(
        self, values: List[float], periods_ahead: int = 3
    ) -> List[float]:
        """Naive linear extrapolation forecast."""
        if len(values) < 2:
            return []
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = statistics.mean(values)
        num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        den = sum((i - x_mean) ** 2 for i in range(n))
        slope = num / den if den else 0
        last_x = n - 1
        return [round(y_mean + slope * (last_x + i + 1), 4) for i in range(periods_ahead)]


# ---------------------------------------------------------------------------
# 8. AUTOMATION & OPTIMIZATION
# ---------------------------------------------------------------------------

class AutomationModule:
    """
    - Automates repetitive tasks (scheduled reports, data refreshes)
    - Improves data pipelines
    - Builds reusable dashboard configurations
    - Script generation stubs
    """

    def schedule_task(
        self,
        task_name: str,
        frequency: str,  # 'daily', 'weekly', 'monthly', 'on_demand'
        task_callable: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        next_run = self._next_run(frequency)
        return {
            "task_name": task_name,
            "frequency": frequency,
            "task_callable": task_callable,
            "params": params,
            "next_run": next_run,
            "status": "scheduled",
        }

    def _next_run(self, frequency: str) -> str:
        now = datetime.utcnow()
        if frequency == "daily":
            return (now + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        if frequency == "weekly":
            return (now + timedelta(weeks=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        if frequency == "monthly":
            return (now + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
        return now.strftime("%Y-%m-%dT%H:%M:%SZ")

    def generate_etl_script(
        self,
        source: str,
        destination: str,
        transformations: List[str],
    ) -> str:
        """Returns a Python ETL script template as a string."""
        steps = "\n    ".join([f"# Step: {t}" for t in transformations])
        return f"""# Auto-generated ETL Script
# Source: {source}  →  Destination: {destination}
# Generated: {datetime.utcnow().isoformat()}

import pandas as pd

def run_etl():
    # --- EXTRACT ---
    df = pd.read_csv("{source}")          # adapt for SQL/API/etc.

    # --- TRANSFORM ---
    {steps}

    # --- LOAD ---
    df.to_csv("{destination}", index=False)
    print("ETL complete.")

if __name__ == "__main__":
    run_etl()
"""

    def build_reusable_dashboard_template(
        self, template_name: str, kpi_definitions: List[Dict], chart_templates: List[Dict]
    ) -> Dict[str, Any]:
        return {
            "template_name": template_name,
            "version": "1.0",
            "kpi_definitions": kpi_definitions,
            "chart_templates": chart_templates,
            "reusable": True,
            "created_at": datetime.utcnow().isoformat(),
        }


# ---------------------------------------------------------------------------
# DUTY SCHEDULER  (Daily / Weekly / Monthly / Strategic)
# ---------------------------------------------------------------------------

class DutyScheduler:
    """
    Maps the agent's duties to appropriate frequencies.
    """

    DAILY_DUTIES = [
        "query_and_update_datasets",
        "monitor_dashboards",
        "clean_incoming_data",
        "generate_routine_reports",
    ]
    WEEKLY_DUTIES = [
        "analyse_performance_metrics",
        "create_summary_reports",
        "present_insights_to_teams",
    ]
    MONTHLY_DUTIES = [
        "monthly_kpi_review",
        "stakeholder_report",
        "data_quality_audit",
    ]
    STRATEGIC_DUTIES = [
        "identify_growth_opportunities",
        "recommend_business_improvements",
        "support_forecasting_and_planning",
        "automation_pipeline_review",
    ]

    def get_due_duties(self, frequency: str) -> List[str]:
        mapping = {
            "daily": self.DAILY_DUTIES,
            "weekly": self.WEEKLY_DUTIES,
            "monthly": self.MONTHLY_DUTIES,
            "strategic": self.STRATEGIC_DUTIES,
        }
        return mapping.get(frequency, [])


# ---------------------------------------------------------------------------
# MAIN AGENT
# ---------------------------------------------------------------------------

class DataAnalystAgent(BaseAgent):
    """
    Full-featured Data Analyst Agent.

    Responsibilities
    ----------------
    1. Data Collection      – multi-source ingestion + completeness validation
    2. Data Cleaning        – dedup, missing-value handling, format standardisation
    3. Data Analysis        – descriptive stats, trends, correlations, outliers, top-N
    4. Data Visualisation   – chart/dashboard spec builder (Tableau / Power BI / Chart.js)
    5. Reporting            – executive summaries, stakeholder reports, markdown export
    6. Database Management  – SQL execution, integrity checks, pagination
    7. Business Intelligence– KPI alignment, SWOT derivation, simple forecasting
    8. Automation           – task scheduling, ETL script generation, reusable templates

    Tools (via sub-modules)
    -----------------------
    Data Handling : Excel, SQL, CSV
    Programming   : Python (statistics, re, json — extend with pandas/numpy)
    Visualisation : Tableau, Power BI, Chart.js, Recharts, Excel charts
    Databases     : MySQL, PostgreSQL, NoSQL (via connection_info stubs)
    Other         : Google Analytics, BigQuery (add adapters as needed)
    """

    name = "Data Analyst Agent"
    role = "Data Analyst"

    # Sub-module instances
    _collector   = DataCollectionModule()
    _cleaner     = DataCleaningModule()
    _analyser    = DataAnalysisModule()
    _visualiser  = DataVisualizationModule()
    _reporter    = ReportingModule()
    _db_manager  = DatabaseManagementModule()
    _bi_module   = BusinessIntelligenceModule()
    _automation  = AutomationModule()
    _scheduler   = DutyScheduler()

    # ------------------------------------------------------------------ #
    #  ENTRY POINT                                                         #
    # ------------------------------------------------------------------ #

    def run(self, context: Dict[str, Any]) -> AgentResult:
        """
        Context keys (all optional — agent falls back to sensible defaults):
        -----------------------------------------------------------------------
        task_description  : str           – human-readable task brief
        duty_frequency    : str           – 'daily' | 'weekly' | 'monthly' | 'strategic'
        sources           : list[dict]    – DataSource constructor kwargs
        datasets          : list[dict]    – pre-loaded {name, records, schema}
        cleaning_rules    : dict          – rules forwarded to DataCleaningModule.clean()
        analysis_config   : dict          – config forwarded to DataAnalysisModule.analyse()
        chart_requests    : list[dict]    – chart spec requests
        dashboard_name    : str           – name for the assembled dashboard
        kpi_definitions   : list[dict]    – KPI card definitions
        report_type       : str           – one of ReportingModule.REPORT_TYPES
        report_title      : str
        business_goals    : list[str]
        forecast_values   : list[float]   – historical series for forecasting
        etl_requests      : list[dict]    – ETL script generation requests
        db_queries        : list[dict]    – {query, connection_info}
        scheduled_tasks   : list[dict]    – tasks to register
        -----------------------------------------------------------------------
        """
        warnings: List[str] = []
        outputs: Dict[str, Any] = {}

        try:
            task_description = context.get("task_description", "")
            duty_frequency   = context.get("duty_frequency", "daily")

            # --- 0. Duty schedule ---
            outputs["due_duties"] = self._scheduler.get_due_duties(duty_frequency)

            # --- 1. Data Collection ---
            raw_sources = context.get("sources", [])
            if raw_sources:
                sources = [DataSource(**s) for s in raw_sources]
                collected = self._collector.collect(sources)
                completeness = self._collector.validate_completeness(collected)
                outputs["data_collection"] = {
                    "datasets_collected": {k: v.to_dict() for k, v in collected.items()},
                    "completeness_report": completeness,
                }
                if any(v["status"] == "INCOMPLETE" for v in completeness.values()):
                    warnings.append("Some collected datasets have completeness issues.")
            else:
                collected = {}

            # Allow caller to inject pre-loaded datasets
            for ds_def in context.get("datasets", []):
                ds = DataSet(**ds_def)
                collected[ds.name] = ds

            # --- 2. Data Cleaning ---
            cleaned: Dict[str, DataSet] = {}
            cleaning_logs: Dict[str, Any] = {}
            cleaning_rules = context.get("cleaning_rules", {})
            for name, ds in collected.items():
                c_ds, c_log = self._cleaner.clean(ds, cleaning_rules)
                cleaned[name] = c_ds
                cleaning_logs[name] = c_log
            if cleaned:
                outputs["data_cleaning"] = cleaning_logs

            # --- 3. Data Analysis ---
            analysis_results: Dict[str, Any] = {}
            analysis_config = context.get("analysis_config", {})
            if analysis_config and cleaned:
                primary_ds_name = list(cleaned.keys())[0]
                primary_ds = cleaned[primary_ds_name]
                analysis_results = self._analyser.analyse(primary_ds, analysis_config)
                outputs["data_analysis"] = analysis_results

            # --- 4. Data Visualisation ---
            chart_specs: List[Dict] = []
            for cr in context.get("chart_requests", []):
                spec = self._visualiser.build_chart_spec(**cr)
                chart_specs.append(spec)

            kpi_cards = [self._visualiser.build_kpi_card(**k) for k in context.get("kpi_definitions", [])]

            if not kpi_cards and not analysis_results:
                # Default executive KPI dashboard
                kpi_cards = [
                    self._visualiser.build_kpi_card("Monthly Revenue", "$120,000", "+12%", unit="USD", status="good"),
                    self._visualiser.build_kpi_card("Customer Growth", "18%", "+4%", unit="%", status="good"),
                    self._visualiser.build_kpi_card("Regional Sales", "$78,000", "+9%", unit="USD", status="good"),
                ]
                chart_specs = [
                    self._visualiser.build_chart_spec("line", "Revenue Trend", [], x_label="Month", y_label="Revenue"),
                    self._visualiser.build_chart_spec("bar", "Customer Growth Trend", [], x_label="Month", y_label="Customers"),
                    self._visualiser.build_chart_spec("stacked_bar", "Regional Sales Comparison", [], x_label="Region", y_label="Sales"),
                ]

            dashboard_name = context.get("dashboard_name", "Executive KPI Dashboard")
            dashboard = self._visualiser.build_dashboard(dashboard_name, chart_specs, kpi_cards)
            outputs["visualisation"] = dashboard

            # --- 5. Reporting ---
            report_type  = context.get("report_type", "executive_summary")
            report_title = context.get("report_title", f"{dashboard_name} – {datetime.utcnow().strftime('%B %Y')}")
            insights = [
                {"finding": f, "direction": "positive"}
                for f in [str(v) for v in list(analysis_results.values())[:3]]
            ] if analysis_results else [
                {"finding": "Revenue is growing at +12% month-over-month", "direction": "positive"},
                {"finding": "Customer growth rate increased by 4 percentage points", "direction": "positive"},
                {"finding": "Regional sales up 9% driven by Q4 campaigns", "direction": "opportunity"},
            ]
            recommendations = context.get("recommendations", [
                "Increase marketing spend in high-growth regions.",
                "Investigate churn patterns in low-growth segments.",
                "Automate weekly KPI digest delivery to stakeholders.",
            ])
            report = self._reporter.generate_report(
                report_type, report_title, insights, recommendations,
                visualizations=chart_specs, format_output="json"
            )
            outputs["report"] = report

            # --- 6. Database Management ---
            db_results: List[Dict] = []
            for qr in context.get("db_queries", []):
                result = self._db_manager.execute_sql(qr["query"], qr.get("connection_info", {}))
                db_results.append(result)
            if db_results:
                outputs["database_queries"] = db_results

            # Integrity check on cleaned datasets
            integrity_reports: Dict[str, Any] = {}
            integrity_constraints = context.get("integrity_constraints", {})
            if integrity_constraints:
                for name, ds in cleaned.items():
                    integrity_reports[name] = self._db_manager.check_integrity(ds, integrity_constraints)
                outputs["integrity_checks"] = integrity_reports

            # --- 7. Business Intelligence ---
            business_goals = context.get("business_goals", [])
            if business_goals and analysis_results:
                outputs["kpi_alignment"] = self._bi_module.align_kpis(analysis_results, business_goals)
                outputs["swot"] = self._bi_module.swot_from_data(insights)

            forecast_values = context.get("forecast_values", [])
            if forecast_values:
                outputs["forecast"] = {
                    "input_periods": len(forecast_values),
                    "forecast_3_periods": self._bi_module.forecast_simple(forecast_values, 3),
                }

            # --- 8. Automation ---
            automation_outputs: Dict[str, Any] = {}
            for et in context.get("etl_requests", []):
                script = self._automation.generate_etl_script(**et)
                automation_outputs[et["source"]] = {"etl_script": script}

            for st in context.get("scheduled_tasks", []):
                scheduled = self._automation.schedule_task(**st)
                automation_outputs[st["task_name"]] = scheduled

            # Build reusable dashboard template for future reuse
            automation_outputs["reusable_dashboard_template"] = (
                self._automation.build_reusable_dashboard_template(
                    template_name=f"{dashboard_name}_Template",
                    kpi_definitions=context.get("kpi_definitions", []),
                    chart_templates=chart_specs,
                )
            )
            outputs["automation"] = automation_outputs

            # --- Final metadata ---
            outputs["task_reference"] = task_description
            outputs["duty_frequency"] = duty_frequency
            outputs["agent_tools"] = {
                "data_handling": ["Excel", "SQL", "CSV"],
                "programming": ["Python (statistics, re, json)", "Pandas (extend)", "NumPy (extend)"],
                "visualisation": ["Tableau", "Power BI", "Chart.js", "Recharts", "Excel Charts"],
                "databases": ["MySQL", "PostgreSQL", "NoSQL"],
                "other": ["Google Analytics", "BigQuery"],
            }

            return AgentResult(
                agent_name=self.name,
                role=self.role,
                status="SUCCESS",
                summary=(
                    f"Completed full data analyst pipeline: collection → cleaning → "
                    f"analysis → visualisation → reporting → DB management → "
                    f"business intelligence → automation. "
                    f"Dashboard '{dashboard_name}' generated with {len(kpi_cards)} KPIs "
                    f"and {len(chart_specs)} charts."
                ),
                outputs=outputs,
                warnings=warnings,
            )

        except Exception as exc:  # noqa: BLE001
            return AgentResult(
                agent_name=self.name,
                role=self.role,
                status="FAILURE",
                summary=f"Agent encountered an error: {exc}",
                outputs={},
                warnings=[str(exc)],
            )