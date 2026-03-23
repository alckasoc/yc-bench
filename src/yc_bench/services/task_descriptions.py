"""Template pool for natural language task descriptions.

Each domain has a pool of description templates. The seeded RNG picks one per task.
Templates contain {slots} filled with randomized details to increase diversity.
The agent sees only the description — the underlying domain is hidden.
"""
from __future__ import annotations

# Each template: (description_template, difficulty_hint)
# difficulty_hint is optional flavor text that correlates with qty

RESEARCH_TEMPLATES = [
    "Design a novel {arch} architecture for {application}. Requires literature review, experimentation with different approaches, and rigorous benchmarking against baselines.",
    "Investigate why our {system} performance degrades on {edge_case}. Needs deep analysis of failure modes, hypothesis testing, and development of improved algorithms.",
    "Develop a new {method} approach for {task}. This is exploratory work — we need someone who can review recent papers, prototype ideas, and iterate on promising directions.",
    "Build a proof-of-concept {model_type} for {use_case}. Requires understanding state-of-the-art techniques and adapting them to our specific constraints.",
    "Conduct a systematic evaluation of {tech} approaches for {problem}. Need thorough experimental design, statistical analysis, and clear recommendations.",
    "Create an improved {algorithm} that handles {constraint}. Current solution fails under these conditions. Needs creative problem-solving and mathematical rigor.",
    "Research and prototype a {technique} system for {domain_app}. Must survey existing approaches, identify gaps, and propose novel solutions.",
    "Develop theoretical foundations for our {framework} approach to {challenge}. Needs formal analysis, proofs of convergence, and empirical validation.",
    "Explore {paradigm} methods for {objective}. We've tried conventional approaches without success — looking for fresh research perspectives.",
    "Design experiments to validate our {hypothesis} about {phenomenon}. Requires careful experimental methodology and statistical rigor.",
    "Build a {model_type} that can {capability} in {context}. Needs extensive prototyping and ablation studies to find the right configuration.",
    "Analyze the {property} characteristics of {system_type} systems and propose improvements. Requires deep technical investigation.",
    "Develop a novel optimization objective for {training_objective}. Current approaches produce suboptimal results on {metric}.",
    "Investigate {failure_mode} in our {system} and propose research-backed solutions. Need root cause analysis and experimental fixes.",
    "Create a benchmark suite for evaluating {capability} across different {variable}. Requires careful design and baseline implementations.",
]

TRAINING_TEMPLATES = [
    "Train a production {model_type} on {dataset_desc}. Needs hyperparameter tuning, distributed training setup, and convergence monitoring.",
    "Fine-tune our {base_model} for {downstream_task}. Requires careful data preparation, learning rate scheduling, and evaluation on held-out sets.",
    "Set up an end-to-end {training_type} pipeline for {application}. Must handle data loading, augmentation, training loops, and checkpoint management.",
    "Retrain our {system} using {new_data}. The model has drifted and needs updating. Requires managing training infrastructure and validating improvements.",
    "Optimize training efficiency for our {model_type} — currently takes too long. Need mixed precision, gradient accumulation, and infrastructure tuning.",
    "Build a {training_approach} system that can learn from {data_source}. Requires custom training loops and careful loss function design.",
    "Train and validate a {model_type} ensemble for {use_case}. Need to manage multiple training runs and combine models effectively.",
    "Implement curriculum {training_type} for our {task}. Models struggle with hard examples — need progressive difficulty scaling.",
    "Set up continuous training infrastructure for {system}. Models need regular retraining as {data_source} evolves.",
    "Run a large-scale {experiment_type} sweep to find optimal {hyperparams} for {task}. Requires efficient resource management.",
    "Fine-tune a {base_model} with {technique} to improve {metric}. Current model underperforms on {subset}.",
    "Build a training pipeline that handles {data_challenge}. Need robust data preprocessing and augmentation strategies.",
    "Train a multi-task model that handles both {task_a} and {task_b}. Requires balancing loss functions across objectives.",
    "Develop a distillation pipeline to compress our {large_model} into a deployable {small_model}. Must maintain quality on {benchmark}.",
    "Set up reinforcement learning from {feedback_source} for our {system}. Requires reward modeling and stable training.",
]

INFERENCE_TEMPLATES = [
    "Deploy our {model_type} for real-time {application}. Needs latency optimization, batching strategy, and monitoring setup.",
    "Build an inference pipeline that serves {qps} queries per second for {use_case}. Requires model optimization and infrastructure design.",
    "Optimize {model_type} inference to run on {hardware}. Current deployment exceeds latency budgets — need quantization and pruning.",
    "Create a {serving_type} system for {application}. Must handle variable load, graceful degradation, and A/B testing of model versions.",
    "Set up model serving infrastructure for {use_case}. Need containerization, load balancing, and health monitoring.",
    "Implement streaming inference for {real_time_app}. Must process {data_type} continuously with minimal latency.",
    "Build a batch inference pipeline for processing {volume} of {data_type}. Needs efficient resource utilization and error handling.",
    "Optimize our {model_type} for edge deployment on {device}. Requires model compression without significant quality loss.",
    "Design a caching strategy for {model_type} predictions. Many queries are similar — smart caching could reduce compute by {percent}.",
    "Create an inference gateway that routes requests to different {model_type} versions based on {criteria}. Need low-overhead routing logic.",
    "Build a multi-model inference pipeline where {model_a} output feeds into {model_b}. Requires orchestration and error propagation.",
    "Set up shadow inference for comparing {model_v1} against {model_v2} in production. Need side-by-side metrics collection.",
    "Implement speculative decoding for our {model_type} to reduce latency. Requires careful draft model selection.",
    "Deploy {model_type} with automatic scaling based on {metric}. Must handle traffic spikes without dropping requests.",
    "Build an offline inference system for bulk processing {dataset}. Need to maximize throughput within cost constraints.",
]

DATA_ENVIRONMENT_TEMPLATES = [
    "Build a data pipeline that ingests {data_source} and produces {output_format} for downstream models. Need reliable scheduling and monitoring.",
    "Set up a {storage_type} data lake for {data_type}. Requires schema design, access controls, and integration with existing systems.",
    "Create an ETL pipeline that transforms {raw_data} into {features} for model training. Must handle {data_challenge} gracefully.",
    "Design and implement a feature store for {use_case}. Need low-latency serving, versioning, and backfill capabilities.",
    "Build data quality monitoring for our {pipeline}. Need automated anomaly detection, alerting, and data validation rules.",
    "Migrate our {system} from {old_tech} to {new_tech}. Requires careful data migration with zero downtime.",
    "Set up a real-time {streaming_type} pipeline for processing {event_type}. Must handle {throughput} events per second.",
    "Create a data labeling pipeline for {task}. Need integration with labeling tools, quality checks, and active learning.",
    "Build reproducible {experiment_type} infrastructure. Every model run must be traceable to exact data versions and configurations.",
    "Design a {data_type} preprocessing pipeline that handles {edge_cases}. Current system breaks on malformed inputs.",
    "Set up data versioning and lineage tracking for our {pipeline}. Need to trace any prediction back to its training data.",
    "Build an automated data validation framework for {data_source}. Must catch schema changes, distribution shifts, and missing values.",
    "Create a synthetic data generation pipeline for {use_case}. Real data is limited — need realistic augmentation.",
    "Design a data access layer that supports both batch and real-time queries on {dataset}. Need unified API for training and serving.",
    "Set up monitoring and alerting for our {pipeline}. Need to detect failures, data freshness issues, and throughput degradation.",
]

# Slot fillers — randomly combined to diversify descriptions
_ARCHITECTURES = ["transformer", "diffusion", "graph neural network", "attention-based", "variational", "contrastive learning", "mixture-of-experts"]
_APPLICATIONS = ["document understanding", "code generation", "image synthesis", "recommendation", "anomaly detection", "search ranking", "content moderation", "fraud detection", "medical imaging", "speech recognition"]
_SYSTEMS = ["recommendation engine", "search pipeline", "classification model", "generation system", "ranking model", "embedding model", "forecasting system"]
_EDGE_CASES = ["long-tail distributions", "out-of-domain inputs", "adversarial examples", "missing features", "noisy labels", "class imbalance", "multilingual data"]
_METHODS = ["self-supervised", "few-shot learning", "meta-learning", "transfer learning", "active learning", "multi-modal", "zero-shot"]
_TASKS = ["entity extraction", "sentiment analysis", "object detection", "text summarization", "question answering", "time series forecasting", "clustering"]
_MODEL_TYPES = ["language model", "vision model", "embedding model", "classifier", "generative model", "retrieval model", "multi-modal model"]
_USE_CASES = ["customer support automation", "content personalization", "risk assessment", "demand forecasting", "quality inspection", "user segmentation", "price optimization"]
_TECHNIQUES = ["knowledge distillation", "contrastive learning", "prompt engineering", "adapter tuning", "neural architecture search", "feature selection"]
_DATASETS = ["6 months of user interaction logs", "a 10M-record product catalog", "multilingual customer feedback", "real-time sensor streams", "historical transaction data"]
_HARDWARE = ["edge GPUs", "mobile devices", "CPU-only servers", "custom accelerators"]
_DATA_SOURCES = ["customer event streams", "third-party API feeds", "internal databases", "IoT sensor networks", "web scraping pipelines"]
_DATA_TYPES = ["user behavioral data", "financial transactions", "text documents", "image assets", "time series metrics"]
_CHALLENGES = ["schema evolution", "late-arriving data", "duplicate records", "PII redaction", "format inconsistencies"]

SLOT_FILLERS = {
    "arch": _ARCHITECTURES, "application": _APPLICATIONS, "system": _SYSTEMS,
    "edge_case": _EDGE_CASES, "method": _METHODS, "task": _TASKS,
    "model_type": _MODEL_TYPES, "use_case": _USE_CASES, "technique": _TECHNIQUES,
    "domain_app": _APPLICATIONS, "paradigm": _METHODS, "objective": _TASKS,
    "hypothesis": _METHODS, "phenomenon": _EDGE_CASES, "capability": _TASKS,
    "context": _USE_CASES, "property": _EDGE_CASES, "system_type": _SYSTEMS,
    "training_objective": _TASKS, "metric": _EDGE_CASES, "failure_mode": _EDGE_CASES,
    "pipeline": _SYSTEMS, "variable": _EDGE_CASES, "constraint": _EDGE_CASES,
    "algorithm": _TECHNIQUES, "framework": _METHODS, "challenge": _TASKS,
    "base_model": _MODEL_TYPES, "downstream_task": _TASKS,
    "dataset_desc": _DATASETS, "training_type": _METHODS, "new_data": _DATASETS,
    "training_approach": _METHODS, "data_source": _DATA_SOURCES,
    "experiment_type": _METHODS, "hyperparams": _TECHNIQUES,
    "task_a": _TASKS, "task_b": _TASKS, "large_model": _MODEL_TYPES,
    "small_model": _MODEL_TYPES, "benchmark": _APPLICATIONS,
    "feedback_source": _DATA_SOURCES, "subset": _EDGE_CASES,
    "data_challenge": _CHALLENGES, "technique": _TECHNIQUES,
    "qps": ["100", "1000", "10000", "50000"],
    "hardware": _HARDWARE, "serving_type": _TECHNIQUES,
    "real_time_app": _APPLICATIONS, "data_type": _DATA_TYPES,
    "volume": ["1M records", "10M documents", "100K images", "1B events"],
    "percent": ["50%", "70%", "80%"],
    "device": _HARDWARE, "criteria": _EDGE_CASES,
    "model_a": _MODEL_TYPES, "model_b": _MODEL_TYPES,
    "model_v1": _MODEL_TYPES, "model_v2": _MODEL_TYPES,
    "dataset": _DATASETS,
    "storage_type": ["columnar", "document-based", "graph", "time-series"],
    "raw_data": _DATA_SOURCES, "features": _DATA_TYPES,
    "output_format": _DATA_TYPES, "old_tech": _DATA_SOURCES,
    "new_tech": _DATA_SOURCES, "streaming_type": _TECHNIQUES,
    "event_type": _DATA_TYPES, "throughput": ["1K", "10K", "100K", "1M"],
    "edge_cases": _CHALLENGES, "experiment_type": _METHODS,
}

DOMAIN_TEMPLATES = {
    "research": RESEARCH_TEMPLATES,
    "training": TRAINING_TEMPLATES,
    "inference": INFERENCE_TEMPLATES,
    "data_environment": DATA_ENVIRONMENT_TEMPLATES,
}


# Complexity hints appended to descriptions based on qty range
_COMPLEXITY_LOW = [  # qty 400-700
    "This is a focused, well-scoped piece of work.",
    "Expect a quick turnaround on this one — limited scope.",
    "Relatively contained effort — the requirements are narrow and well-defined.",
    "Small-scale project with a tight, clear scope.",
    "Lightweight engagement — should be straightforward to deliver.",
    "Compact scope with clear boundaries. No major unknowns.",
]
_COMPLEXITY_MED = [  # qty 700-1100
    "Moderate scope and complexity — plan for a standard development cycle.",
    "This involves a reasonable amount of work across the described areas.",
    "Mid-sized project with some moving parts but nothing unusual.",
    "Expect a typical engagement timeline. The scope is manageable but not trivial.",
    "Standard-complexity project. Should be achievable with a capable team.",
    "A solid body of work — not a quick fix, but not a marathon either.",
]
_COMPLEXITY_HIGH = [  # qty 1100-1500
    "This is a substantial undertaking — expect significant time and resources.",
    "Large-scale effort requiring deep investment from the team.",
    "Comprehensive project with broad scope. Plan for extended timelines.",
    "Major initiative — this will require sustained focus over an extended period.",
    "Significant body of work. Budget extra time for the breadth of requirements.",
    "This is one of our larger projects. Expect complexity across multiple dimensions.",
]


def generate_task_description(rng, domain: str, qty: float = 800) -> str:
    """Generate a natural language description for a task in the given domain."""
    templates = DOMAIN_TEMPLATES.get(domain, RESEARCH_TEMPLATES)
    template = rng.choice(templates)

    # Fill slots
    import re
    def fill_slot(match):
        slot_name = match.group(1)
        fillers = SLOT_FILLERS.get(slot_name)
        if fillers:
            return rng.choice(fillers)
        return match.group(0)

    desc = re.sub(r"\{(\w+)\}", fill_slot, template)

    # Append complexity hint based on qty
    if qty <= 700:
        hint = rng.choice(_COMPLEXITY_LOW)
    elif qty <= 1100:
        hint = rng.choice(_COMPLEXITY_MED)
    else:
        hint = rng.choice(_COMPLEXITY_HIGH)

    return f"{desc} {hint}"
