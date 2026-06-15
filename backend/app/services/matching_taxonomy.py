from collections.abc import Iterable

CONCEPT_ALIASES: dict[str, set[str]] = {
    # Software Engineering
    "api_development": {
        "api",
        "apis",
        "api development",
        "rest api",
        "restful api",
        "web service",
    },
    "frontend_development": {"frontend", "front end", "react", "angular", "vue"},
    "backend_development": {"backend", "back end", "server side"},
    "databases": {
        "database",
        "databases",
        "sql",
        "postgresql",
        "mysql",
        "mongodb",
    },
    "software_testing": {
        "software testing",
        "testing",
        "unit test",
        "integration test",
        "qa",
    },
    "cloud": {"cloud", "aws", "azure", "gcp", "google cloud"},
    "devops": {"devops", "ci cd", "docker", "kubernetes", "terraform"},
    # AI / Machine Learning
    "machine_learning": {"machine learning", "ml", "predictive model"},
    "deep_learning": {"deep learning", "neural network"},
    "nlp": {"natural language processing", "nlp", "language model"},
    "computer_vision": {"computer vision", "image recognition"},
    "generative_ai": {
        "generative ai",
        "aigc",
        "diffusion model",
        "image generation",
        "generated images",
    },
    "model_evaluation": {"model evaluation", "model validation", "cross validation"},
    "pytorch": {"pytorch"},
    "tensorflow": {"tensorflow", "keras"},
    # Data / Analytics
    "sql": {"sql", "structured query language"},
    "excel": {"excel", "spreadsheet", "pivot table"},
    "statistics": {"statistics", "statistical analysis", "hypothesis testing"},
    "dashboards": {"dashboard", "tableau", "power bi", "looker"},
    "data_visualization": {"data visualization", "visualisation", "data viz"},
    "data_cleaning": {"data cleaning", "data cleansing", "data quality"},
    "data_analysis": {"data analysis", "business analysis"},
    # Finance / Accounting
    "financial_modeling": {"financial modeling", "financial model", "dcf model"},
    "accounting": {"accounting", "general ledger", "gaap", "ifrs"},
    "auditing": {"audit", "auditing", "internal controls"},
    "budgeting": {"budgeting", "budget", "forecasting"},
    "valuation": {"valuation", "discounted cash flow", "dcf"},
    "risk_analysis": {"risk analysis", "risk assessment", "financial risk"},
    # Marketing
    "seo": {"seo", "search engine optimization"},
    "content_marketing": {"content marketing", "content strategy"},
    "social_media": {"social media", "social campaign"},
    "marketing_analytics": {"marketing analytics", "campaign analytics"},
    "campaign_management": {"campaign management", "marketing campaign"},
    # Product
    "user_research": {"user research", "customer research", "user interview"},
    "product_strategy": {"product strategy", "product vision"},
    "roadmapping": {"roadmap", "roadmapping", "product roadmap"},
    "product_metrics": {"product metrics", "kpi", "key performance indicator"},
    "experimentation": {"experimentation", "a b testing", "ab testing"},
    # Design
    "ui_ux": {"ui ux", "ux", "user experience", "user interface"},
    "prototyping": {"prototype", "prototyping", "wireframe"},
    "figma": {"figma"},
    "visual_design": {"visual design", "graphic design"},
    # Operations
    "logistics": {"logistics", "supply chain", "inventory"},
    "process_improvement": {"process improvement", "continuous improvement"},
    "stakeholder_coordination": {
        "stakeholder coordination",
        "cross functional coordination",
        "vendor coordination",
    },
    # Healthcare
    "patient_care": {"patient care", "clinical care"},
    "clinical_operations": {"clinical operations", "clinic operations"},
    "medical_terminology": {"medical terminology"},
    "healthcare_data": {"healthcare data", "clinical data"},
    # Research
    "literature_review": {"literature review", "systematic review"},
    "experimental_design": {"experimental design", "study design"},
    "publications": {"publication", "peer reviewed", "research paper"},
    # Education
    "teaching": {"teaching", "instruction", "educator"},
    "curriculum": {"curriculum", "lesson planning"},
    "tutoring": {"tutoring", "tutor", "academic support"},
    "classroom_management": {"classroom management"},
    # Sales / Customer Success
    "crm": {"crm", "salesforce", "hubspot"},
    "client_communication": {"client communication", "customer communication"},
    "account_management": {"account management", "client relationship"},
    "customer_support": {"customer support", "technical support"},
    # Human Resources
    "recruiting": {"recruiting", "recruitment", "talent acquisition"},
    "onboarding": {"onboarding", "new hire orientation"},
    "employee_relations": {"employee relations", "labor relations"},
    # Legal / Compliance
    "compliance": {"compliance", "regulatory compliance"},
    "contracts": {"contract review", "contract drafting", "contracts"},
    "policy": {"policy", "policy analysis", "policy development"},
    "risk_controls": {"risk controls", "control framework", "governance controls"},
}

TRANSFERABLE_CONCEPTS: dict[str, set[str]] = {
    "stakeholder_coordination": {
        "client_communication",
        "account_management",
        "project_management",
    },
    "client_communication": {"stakeholder_coordination", "customer_support"},
    "data_analysis": {
        "marketing_analytics",
        "risk_analysis",
        "healthcare_data",
    },
    "marketing_analytics": {"data_analysis", "product_metrics"},
    "risk_analysis": {"data_analysis", "risk_controls"},
    "user_research": {"client_communication", "product_strategy"},
    "experimental_design": {"experimentation", "model_evaluation"},
    "process_improvement": {"clinical_operations", "logistics"},
    "teaching": {"tutoring", "client_communication"},
    "accounting": {"auditing", "budgeting"},
    "auditing": {"accounting", "risk_controls", "compliance"},
    "compliance": {"risk_controls", "policy", "auditing"},
}


def extract_concepts(normalized_text: str) -> frozenset[str]:
    concepts = {
        concept
        for concept, aliases in CONCEPT_ALIASES.items()
        if any(_phrase_present(alias, normalized_text) for alias in aliases)
    }
    return frozenset(concepts)


def has_transferable_relationship(
    requirement_concepts: Iterable[str],
    evidence_concepts: Iterable[str],
) -> bool:
    evidence_set = set(evidence_concepts)
    return any(
        TRANSFERABLE_CONCEPTS.get(concept, set()) & evidence_set
        for concept in requirement_concepts
    )


def _phrase_present(phrase: str, text: str) -> bool:
    return f" {phrase} " in f" {text} "
