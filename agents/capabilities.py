"""Enterprise capability catalog for the Nexus Data Platform.

This module is the single source of truth for every enterprise-level duty,
responsibility, workflow, governance/operational/architecture/cloud/AI/analytics/
ERP and industry activity the platform supports.

Each top-level category maps to a responsible specialist agent (``CATEGORY_AGENTS``)
and to a set of routing keywords (``DOMAIN_KEYWORDS``) used by the orchestrator to
select agents from a free-text task description.

Nothing here is mocked away: the orchestrator routes work to the owning agent, the
owning agent reports the duties it covers, and the ``/capabilities`` API exposes the
entire catalog so callers can discover every supported duty.
"""

from __future__ import annotations

from typing import Dict, List, Union

# A duty list is either a flat list of duty names, or (for cloud) a mapping of
# provider -> list of services.
DutyList = Union[List[str], Dict[str, List[str]]]

ENTERPRISE_CAPABILITIES: Dict[str, DutyList] = {
    "Program & Portfolio Management": [
        "Portfolio Management",
        "Program Management",
        "Project Management",
        "PMO Governance",
        "Budget Management",
        "Cost Management",
        "Financial Forecasting",
        "Resource Planning",
        "Capacity Planning",
        "Workforce Planning",
        "Vendor Management",
        "Contract Management",
        "Risk Management",
        "Issue Management",
        "Dependency Management",
        "Executive Steering Committees",
        "Governance Boards",
        "Status Reporting",
        "Executive Reporting",
        "Roadmap Planning",
    ],
    "Service Management": [
        "Incident Management",
        "Major Incident Management",
        "Problem Management",
        "Change Management",
        "Release Management",
        "Service Management",
        "SLA Management",
        "OLA Management",
        "Hypercare Support",
        "Production Support",
        "L1 Support",
        "L2 Support",
        "L3 Support",
        "Root Cause Analysis",
        "Post Mortems",
        "Corrective Actions",
        "Preventive Actions",
    ],
    "Data Governance": [
        "Data Stewardship",
        "Data Ownership",
        "Data Classification",
        "Business Glossary",
        "Data Catalog",
        "Metadata Management",
        "Data Lineage",
        "Data Retention",
        "Records Management",
        "Data Lifecycle Management",
        "Reference Data Management",
        "Golden Record Management",
        "Match & Merge",
        "Survivorship Rules",
        "Data Quality Governance",
        "Compliance Governance",
    ],
    "Master Data Management": [
        "Customer Master",
        "Vendor Master",
        "Material Master",
        "Product Master",
        "Business Partner",
        "Hierarchy Management",
        "Reference Data Management",
        "Data Standardization",
        "Duplicate Detection",
        "Duplicate Prevention",
        "Data Validation",
        "Governance Workflows",
    ],
    "Data Engineering": [
        "ETL",
        "ELT",
        "CDC",
        "Streaming",
        "Batch Processing",
        "Data Pipelines",
        "Data Warehouses",
        "Data Lakes",
        "Lakehouses",
        "Data Mesh",
        "Data Fabric",
        "Data Contracts",
        "Data Profiling",
        "Data Cleansing",
        "Data Reconciliation",
        "Data Conversion",
        "Data Migration",
        "Source-to-Target Mapping",
        "Metadata Management",
        "Data Observability",
        "Data Reliability Engineering",
    ],
    "Data Analytics": [
        "KPI Development",
        "Dashboard Development",
        "Executive Dashboards",
        "Operational Dashboards",
        "Financial Dashboards",
        "Regulatory Dashboards",
        "Forecasting",
        "Trend Analysis",
        "Root Cause Analysis",
        "Customer Analytics",
        "Marketing Analytics",
        "Sales Analytics",
        "Revenue Analytics",
        "Churn Analytics",
        "Cohort Analysis",
        "Scenario Planning",
        "What-if Analysis",
        "Data Storytelling",
    ],
    "AI & Data Science": [
        "Machine Learning",
        "Deep Learning",
        "NLP",
        "Computer Vision",
        "Generative AI",
        "Agentic AI",
        "Multi-Agent Systems",
        "RAG",
        "GraphRAG",
        "Reinforcement Learning",
        "Recommendation Systems",
        "Explainable AI",
        "Synthetic Data",
        "AI Governance",
        "AI Risk Management",
        "Model Governance",
        "Prompt Governance",
        "LLMOps",
        "MLOps",
        "AI Observability",
    ],
    "Backend Engineering": [
        "REST APIs",
        "GraphQL APIs",
        "WebSockets",
        "gRPC",
        "Event-Driven Architecture",
        "CQRS",
        "Event Sourcing",
        "Microservices",
        "Service Discovery",
        "API Gateway",
        "API Versioning",
        "Rate Limiting",
        "Distributed Tracing",
        "Multi-Tenant Architecture",
    ],
    "Cloud Engineering": {
        "AWS": [
            "S3",
            "Glue",
            "Athena",
            "Redshift",
            "SageMaker",
            "Lambda",
            "ECS",
            "EKS",
            "EventBridge",
            "Step Functions",
            "Lake Formation",
            "GuardDuty",
            "Security Hub",
            "Macie",
        ],
        "Azure": [
            "Data Factory",
            "Synapse",
            "Databricks",
            "Fabric",
            "Purview",
            "Sentinel",
            "Azure ML",
            "Event Hub",
            "Logic Apps",
        ],
        "GCP": [
            "BigQuery",
            "Dataproc",
            "Dataflow",
            "Composer",
            "Vertex AI",
            "Dataplex",
            "BigLake",
            "Cloud Run",
        ],
    },
    "DevOps & Platform Engineering": [
        "GitOps",
        "CI/CD",
        "Docker",
        "Kubernetes",
        "Helm",
        "Terraform",
        "Pulumi",
        "ArgoCD",
        "FluxCD",
        "Service Mesh",
        "Istio",
        "Linkerd",
        "Vault",
        "Observability",
        "Monitoring",
        "Logging",
        "FinOps",
        "Cost Optimization",
        "Capacity Optimization",
    ],
    "Security": [
        "Zero Trust",
        "IAM",
        "RBAC",
        "ABAC",
        "PAM",
        "Encryption",
        "Tokenization",
        "Data Masking",
        "Secrets Management",
        "DLP",
        "SIEM",
        "Threat Modeling",
        "Vulnerability Management",
        "Security Monitoring",
        "Audit Logging",
    ],
    "Testing & Quality": [
        "Unit Testing",
        "Integration Testing",
        "E2E Testing",
        "API Testing",
        "Performance Testing",
        "Load Testing",
        "Chaos Engineering",
        "Contract Testing",
        "Security Testing",
        "Penetration Testing",
        "Accessibility Testing",
        "AI Testing",
        "LLM Testing",
        "Prompt Testing",
    ],
    "SAP / ERP": [
        "SAP ECC",
        "SAP S/4HANA",
        "SAP MDG",
        "SAP BW",
        "SAP BODS",
        "SAP CPI",
        "SAP Datasphere",
        "SAP SAC",
        "SAP Ariba",
        "SAP IBP",
        "Oracle ERP",
        "Oracle Fusion",
        "Workday",
        "Salesforce",
        "ServiceNow",
        "Dynamics 365",
    ],
    "Industries": [
        "Healthcare",
        "Banking",
        "Financial Services",
        "Insurance",
        "Manufacturing",
        "Retail",
        "E-Commerce",
        "Telecom",
        "Utilities",
        "Energy",
        "Government",
        "Life Sciences",
        "Pharmaceuticals",
        "Logistics",
        "Supply Chain",
        "Transportation",
        "Hospitality",
        "Education",
        "Automotive",
        "Aerospace",
        "Defense",
        "Oil & Gas",
        "Mining",
        "Construction",
        "Real Estate",
        "Media & Entertainment",
        "Consumer Goods",
        "Food & Beverage",
    ],
}

# Category -> the agent key that owns/executes the category's duties.
CATEGORY_AGENTS: Dict[str, str] = {
    "Program & Portfolio Management": "program_portfolio_manager",
    "Service Management": "service_manager",
    "Data Governance": "data_governance",
    "Master Data Management": "master_data_management",
    "Data Engineering": "data_engineer",
    "Data Analytics": "data_analyst",
    "AI & Data Science": "data_scientist",
    "Backend Engineering": "backend_engineer",
    "Cloud Engineering": "cloud_engineer",
    "DevOps & Platform Engineering": "platform_engineer",
    "Security": "security_engineer",
    "Testing & Quality": "qa_engineer",
    "SAP / ERP": "erp_specialist",
    "Industries": "industry_specialist",
}

# Agent key -> free-text keywords the orchestrator uses to route a task to the agent.
DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    "program_portfolio_manager": [
        "portfolio", "program", "project", "pmo", "budget", "cost management",
        "financial forecast", "resource plan", "capacity plan", "workforce",
        "vendor", "contract", "risk", "issue", "dependency", "steering",
        "governance board", "status report", "executive report", "roadmap",
    ],
    "service_manager": [
        "incident", "major incident", "problem management", "change management",
        "release management", "service management", "sla", "ola", "hypercare",
        "production support", "l1", "l2", "l3", "root cause", "post mortem",
        "postmortem", "corrective action", "preventive action", "itil",
    ],
    "data_governance": [
        "governance", "stewardship", "data ownership", "classification",
        "glossary", "catalog", "lineage", "retention", "records management",
        "lifecycle", "reference data", "golden record", "match & merge",
        "match and merge", "survivorship", "data quality", "compliance",
    ],
    "master_data_management": [
        "master data", "mdm", "customer master", "vendor master",
        "material master", "product master", "business partner", "hierarchy",
        "standardization", "duplicate", "match", "survivorship",
    ],
    "data_scientist": [
        "model", "prediction", "machine learning", "ml", "deep learning",
        "forecast", "classification", "nlp", "computer vision", "generative ai",
        "genai", "agentic", "multi-agent", "rag", "graphrag", "reinforcement",
        "recommendation", "explainable", "synthetic data", "ai governance",
        "model governance", "prompt", "llmops", "mlops", "ai observability",
    ],
    "data_analyst": [
        "dashboard", "report", "kpi", "insight", "analysis", "analytics",
        "visual", "trend", "forecasting", "cohort", "churn", "scenario",
        "what-if", "storytelling",
    ],
    "backend_engineer": [
        "rest", "graphql", "websocket", "grpc", "event-driven", "event driven",
        "cqrs", "event sourcing", "microservice", "service discovery",
        "api gateway", "api version", "rate limit", "distributed tracing",
        "multi-tenant", "multi tenant",
    ],
    "python_developer": [
        "api", "backend", "fastapi", "service", "endpoint", "script",
    ],
    "cloud_engineer": [
        "aws", "azure", "gcp", "cloud", "s3", "glue", "athena", "redshift",
        "sagemaker", "lambda", "ecs", "eks", "eventbridge", "step functions",
        "lake formation", "guardduty", "security hub", "macie", "data factory",
        "synapse", "databricks", "fabric", "purview", "sentinel", "azure ml",
        "event hub", "logic apps", "bigquery", "dataproc", "dataflow",
        "composer", "vertex", "dataplex", "biglake", "cloud run",
    ],
    "platform_engineer": [
        "gitops", "ci/cd", "cicd", "docker", "kubernetes", "k8s", "helm",
        "terraform", "pulumi", "argocd", "fluxcd", "service mesh", "istio",
        "linkerd", "vault", "observability", "monitoring", "logging", "finops",
        "cost optimization", "capacity optimization", "platform engineering",
    ],
    "security_engineer": [
        "security", "zero trust", "iam", "rbac", "abac", "pam", "encryption",
        "tokenization", "masking", "secrets", "dlp", "siem", "threat",
        "vulnerability", "audit",
    ],
    "erp_specialist": [
        "sap", "s/4hana", "s4hana", "ecc", "mdg", " bw", "bods", "cpi",
        "datasphere", "sac", "ariba", "ibp", "oracle", "fusion", "workday",
        "salesforce", "servicenow", "dynamics", "erp",
    ],
    "industry_specialist": [
        "healthcare", "banking", "financial services", "insurance",
        "manufacturing", "retail", "e-commerce", "ecommerce", "telecom",
        "utilities", "energy", "government", "life sciences", "pharma",
        "logistics", "supply chain", "transportation", "hospitality",
        "education", "automotive", "aerospace", "defense", "oil & gas",
        "oil and gas", "mining", "construction", "real estate",
        "media & entertainment", "media and entertainment", "consumer goods",
        "food & beverage", "food and beverage",
    ],
}


def list_categories() -> List[str]:
    """Return all enterprise capability categories."""
    return list(ENTERPRISE_CAPABILITIES.keys())


def duties_for_category(category: str) -> List[str]:
    """Return a flat list of duties for a category.

    Cloud services are flattened to ``"Provider: Service"`` form so every duty is
    a single discoverable string.
    """
    duties = ENTERPRISE_CAPABILITIES.get(category, [])
    if isinstance(duties, dict):
        flat: List[str] = []
        for provider, services in duties.items():
            flat.extend(f"{provider}: {service}" for service in services)
        return flat
    return list(duties)


def total_capability_count() -> int:
    """Total number of distinct duties across every category."""
    return sum(len(duties_for_category(category)) for category in ENTERPRISE_CAPABILITIES)


def agent_for_category(category: str) -> str:
    """Return the agent key responsible for a category."""
    return CATEGORY_AGENTS[category]


def build_capability_catalog() -> List[Dict[str, object]]:
    """Build a serializable catalog describing every supported duty."""
    catalog: List[Dict[str, object]] = []
    for category, duties in ENTERPRISE_CAPABILITIES.items():
        entry: Dict[str, object] = {
            "category": category,
            "responsible_agent": CATEGORY_AGENTS[category],
            "duty_count": len(duties_for_category(category)),
            "duties": duties_for_category(category),
        }
        if isinstance(duties, dict):
            entry["duties_by_group"] = duties
        catalog.append(entry)
    return catalog
