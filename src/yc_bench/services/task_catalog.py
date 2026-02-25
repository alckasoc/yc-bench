"""Realistic AI-startup task titles and descriptions, keyed by domain.

Each domain has a pool of (title, description) tuples. The generator picks
from these deterministically using the seeded RNG, cycling if the pool is
exhausted.
"""
from __future__ import annotations

from ..db.models.company import Domain

TASK_POOL: dict[Domain, list[tuple[str, str]]] = {
    Domain.SYSTEM: [
        (
            "Set Up GPU-Aware K8s Cluster with Auto-Scaling",
            "Deploy a Kubernetes cluster with NVIDIA GPU operator, node auto-scaling based on inference queue depth, and spot instance fallback for training workloads.",
        ),
        (
            "Build CI/CD Pipeline for ML Model Registry",
            "Create a CI pipeline that runs training validation, pushes versioned model artifacts to a registry, and auto-deploys to a staging inference endpoint.",
        ),
        (
            "Implement Blue-Green Deployment for LLM Serving",
            "Set up zero-downtime model swaps for a vLLM serving cluster with automated rollback triggered by latency and error-rate thresholds.",
        ),
        (
            "Deploy Observability Stack for AI Workloads",
            "Stand up Grafana, Prometheus, and OpenTelemetry with custom dashboards tracking GPU utilization, token throughput, time-to-first-token, and per-request cost.",
        ),
        (
            "Terraform Multi-Region Inference Infrastructure",
            "Write IaC modules to provision inference endpoints across 3+ regions with global load balancing, failover routing, and centralized logging.",
        ),
        (
            "Container Image Optimization for ML Serving",
            "Reduce Docker image sizes for PyTorch/CUDA serving containers from 15 GB to under 4 GB using multi-stage builds and distroless bases to cut cold-start times.",
        ),
        (
            "Implement Secret Rotation and API Key Management",
            "Build an automated secret rotation system for API keys, database credentials, and model provider tokens across staging and production environments.",
        ),
        (
            "Set Up Cost Monitoring and GPU Budget Alerts",
            "Integrate cloud billing APIs with a dashboard showing per-team GPU spend, cost-per-inference breakdowns, and automated alerts when daily spend exceeds thresholds.",
        ),
        (
            "Build Canary Release Pipeline for Embedding Models",
            "Implement a canary deployment system that gradually shifts traffic to new embedding model versions, comparing retrieval quality metrics in real time.",
        ),
        (
            "Migrate Inference Workloads to Serverless GPU",
            "Evaluate and migrate bursty inference workloads to serverless GPU providers, benchmarking cold-start latency against always-on instances.",
        ),
        (
            "Implement Disaster Recovery for Training Checkpoints",
            "Design a cross-region checkpoint backup system with automated integrity verification, ensuring training runs can resume within 15 minutes of any single-region failure.",
        ),
        (
            "Build Internal Developer Platform for ML Engineers",
            "Create a self-service portal where ML engineers can request GPU instances, spin up Jupyter environments, and launch training jobs without touching infrastructure.",
        ),
    ],
    Domain.RESEARCH: [
        (
            "Design Benchmark for Legal Document QA",
            "Create a benchmark suite of 2,000+ annotated legal questions across contract law and compliance, with human-expert baselines and an automated evaluation harness.",
        ),
        (
            "Investigate MoE Routing for Multilingual Models",
            "Research and prototype alternative Mixture-of-Experts routing strategies that improve expert utilization for low-resource languages without degrading high-resource performance.",
        ),
        (
            "Reproduce and Extend Speculative Decoding Results",
            "Replicate speculative decoding paper results on Llama-3 class models, then test novel draft model architectures that improve acceptance rates on code generation.",
        ),
        (
            "Develop RAG Hallucination Detection Framework",
            "Build a systematic evaluation pipeline measuring faithfulness, relevance, and attribution accuracy for retrieval-augmented generation systems.",
        ),
        (
            "Prototype LoRA Merging for Multi-Tenant Serving",
            "Research methods for dynamically composing multiple LoRA adapters at inference time, measuring quality degradation versus serving separate fine-tuned models.",
        ),
        (
            "Benchmark Long-Context Retrieval Across 128K Models",
            "Systematically evaluate needle-in-a-haystack and multi-hop reasoning performance across frontier models at various context lengths with reproducible results.",
        ),
        (
            "Investigate Synthetic Data Quality for Code Generation",
            "Develop automated quality scoring methods for synthetically generated code training data, correlating filter thresholds with downstream model performance.",
        ),
        (
            "Research KV-Cache Compression Techniques",
            "Prototype and benchmark KV-cache eviction and quantization strategies for long-running conversational agents under fixed memory budgets.",
        ),
        (
            "Build Ablation Study Framework for Prompt Engineering",
            "Create an experimentation harness for testing prompt variations across multiple models and tasks with statistical significance testing and cost tracking.",
        ),
        (
            "Explore Constitutional AI for Domain-Specific Safety",
            "Adapt constitutional AI methods to create a self-improving safety filter for a healthcare chatbot, defining domain-specific principles and measuring accuracy.",
        ),
        (
            "Develop Novel Chunking Strategies for Technical RAG",
            "Research and benchmark alternative document chunking methods—semantic, AST-aware, sliding window—specifically for API documentation and code repositories.",
        ),
        (
            "Prototype Test-Time Compute Scaling for Math Reasoning",
            "Implement best-of-N sampling, tree search, and self-verification approaches for math reasoning, measuring the compute-accuracy Pareto frontier.",
        ),
    ],
    Domain.DATA: [
        (
            "Build Web Scraping Pipeline for Industry News Corpus",
            "Design a pipeline that crawls 50+ AI/tech news sources daily, deduplicates articles, extracts structured metadata, and loads clean text into a vector store.",
        ),
        (
            "Create Annotation Platform for Dialogue Quality",
            "Build an annotation workflow where human raters score LLM conversation logs on helpfulness, accuracy, and safety, with inter-rater agreement tracking.",
        ),
        (
            "Implement PII Detection and Redaction Pipeline",
            "Deploy a pipeline to detect and redact personally identifiable information from training data, with audit logging and configurable redaction strategies.",
        ),
        (
            "Curate Instruction-Tuning Dataset from Internal Docs",
            "Extract, clean, and convert 10,000+ pages of internal documentation into high-quality instruction-response pairs suitable for fine-tuning.",
        ),
        (
            "Build Data Quality Monitoring for Feature Store",
            "Implement data validation checks on streaming feature pipelines, alerting on schema drift, null-rate spikes, and distribution shifts before they affect models.",
        ),
        (
            "Design ETL Pipeline for Multi-Modal Training Data",
            "Build a DAG pipeline that ingests images, PDFs, and structured data, applies OCR and layout detection, and produces unified records for vision-language training.",
        ),
        (
            "Implement Deduplication for Large Text Corpora",
            "Deploy MinHash LSH-based near-deduplication at scale for 100M+ documents with configurable similarity thresholds and a review UI for borderline cases.",
        ),
        (
            "Build Synthetic Data Pipeline for Rare Edge Cases",
            "Create a system that uses frontier LLMs to generate realistic synthetic examples for underrepresented categories in a classification dataset.",
        ),
        (
            "Create Data Versioning and Lineage Tracking System",
            "Set up data versioning integrated with the ML training pipeline so every model checkpoint can be traced back to the exact dataset snapshot used.",
        ),
        (
            "Build Customer Feedback Loop into Training Pipeline",
            "Implement a system where end-user thumbs-up/down signals are routed, reviewed, and selectively incorporated into fine-tuning datasets with human approval.",
        ),
        (
            "Migrate Legacy Warehouse to ML-Ready Lakehouse",
            "Transform and migrate 5 years of product analytics data from a legacy SQL warehouse into a Parquet-based lakehouse optimized for feature engineering.",
        ),
    ],
    Domain.FRONTEND: [
        (
            "Build Interactive LLM Playground with Streaming",
            "Create a web app where users test multiple LLM providers side-by-side with streaming output, adjustable parameters, and conversation history persistence.",
        ),
        (
            "Design Admin Dashboard for AI Agent Monitoring",
            "Build a dashboard showing real-time agent execution traces, tool call sequences, token usage graphs, and cost breakdowns with drill-down filtering.",
        ),
        (
            "Create Document Chat Interface for RAG Product",
            "Implement a drag-and-drop document upload UI with a conversational interface showing source citations, confidence indicators, and reference highlighting.",
        ),
        (
            "Build Annotation Review and Approval Interface",
            "Design a UI for data team leads to review annotator work, resolve disagreements, view agreement stats, and approve batches for training inclusion.",
        ),
        (
            "Implement Prompt Management Studio",
            "Build a collaborative app where teams version, test, and A/B deploy prompt templates with visual diffs, rollback, and per-version performance analytics.",
        ),
        (
            "Create Customer-Facing AI Usage Analytics Dashboard",
            "Build an embeddable dashboard showing API call volumes, latency percentiles, token consumption, and cost trends for enterprise customers.",
        ),
        (
            "Build Visual Pipeline Editor for No-Code AI Workflows",
            "Create a node-based drag-and-drop editor where non-technical users chain data sources, LLM calls, and output actions into automated AI workflows.",
        ),
        (
            "Design Chat Widget for Website Embedding",
            "Build a lightweight, brandable chat widget under 50 KB that customers embed on their sites, with streaming responses and escalation-to-human capability.",
        ),
        (
            "Build Model Comparison Results Viewer",
            "Create a web interface displaying benchmark results across models in interactive tables and charts with filtering by task type and model size.",
        ),
        (
            "Implement Real-Time Collaboration for AI Writing Tool",
            "Add multiplayer editing to an AI writing tool using CRDTs, with per-user cursors, AI suggestion tracking, and version history.",
        ),
        (
            "Create Enterprise RAG Onboarding Wizard",
            "Build a step-by-step setup wizard guiding enterprise customers through connecting data sources, configuring chunking, testing retrieval, and deploying their endpoint.",
        ),
    ],
    Domain.BACKEND: [
        (
            "Build Multi-Tenant LLM Gateway with Rate Limiting",
            "Implement an API gateway that proxies requests to multiple LLM providers, enforces per-tenant rate limits, tracks usage, and handles automatic failover.",
        ),
        (
            "Implement OAuth2 + SAML SSO for Enterprise Platform",
            "Add enterprise authentication supporting SAML 2.0, OIDC, and SCIM provisioning for customers integrating with their identity provider.",
        ),
        (
            "Design Webhook System for Async AI Job Completion",
            "Build a reliable webhook delivery system with exponential backoff, signature verification, dead letter queue, and a webhook management API.",
        ),
        (
            "Create Unified Embedding API with Caching Layer",
            "Build a microservice abstracting over multiple embedding providers with a Redis-backed cache, batch processing, and automatic model version migration.",
        ),
        (
            "Build Conversation Memory Service for Multi-Session Agents",
            "Implement a service that stores, summarizes, and retrieves conversation history across sessions using structured storage and semantic vector search.",
        ),
        (
            "Implement Usage-Based Billing with Stripe Integration",
            "Build a metering system that tracks token consumption per customer, aggregates monthly invoices, and syncs with Stripe for automated usage-based charging.",
        ),
        (
            "Create Plugin Marketplace Backend",
            "Design the API and data model for a marketplace where third-party developers register, version, and distribute plugins for the AI platform.",
        ),
        (
            "Build RAG Ingestion Service with Chunking and Indexing",
            "Implement an async document processing service that accepts PDFs, DOCX, and HTML, chunks them, generates embeddings, and upserts into a vector store.",
        ),
        (
            "Implement Audit Logging and Compliance API",
            "Build a tamper-evident audit log system recording all AI interactions and admin actions, with an API for compliance queries and SOC 2 / HIPAA exports.",
        ),
        (
            "Design Multi-Model Routing and Fallback Service",
            "Create a smart routing layer directing requests to the optimal model based on task complexity, latency requirements, and cost, with provider failover.",
        ),
        (
            "Build File Processing Service for Vision-Language Models",
            "Implement an async service that accepts images and documents, runs them through vision-language models for extraction, and returns structured JSON output.",
        ),
        (
            "Implement Streaming API with Server-Sent Events",
            "Build an SSE-based streaming endpoint for LLM responses with connection resumption, partial response caching, and graceful degradation.",
        ),
    ],
    Domain.TRAINING: [
        (
            "Fine-Tune Llama-3 8B for Domain-Specific Support",
            "Run supervised fine-tuning on 50K curated customer support conversations using QLoRA, targeting 15% accuracy improvement over the base model.",
        ),
        (
            "Implement RLHF Pipeline for Code Generation Model",
            "Build an end-to-end RLHF pipeline with a reward model trained on human preference data and PPO training loop evaluated against HumanEval.",
        ),
        (
            "Distill GPT-4 Class Model into Efficient 3B Model",
            "Use knowledge distillation with synthetic data to create a compact model retaining 90%+ teacher performance on targeted tasks at 10x lower inference cost.",
        ),
        (
            "Train Custom Embedding Model for Vertical Search",
            "Fine-tune a sentence-transformers model on domain-specific query-document pairs with contrastive learning, hard negative mining, and retrieval benchmarks.",
        ),
        (
            "Build Hyperparameter Search for Fine-Tuning Jobs",
            "Implement an Optuna-based HPO system searching over learning rate, LoRA rank, batch size, and data mixing ratios with early stopping.",
        ),
        (
            "Run Continued Pre-Training on Proprietary Corpus",
            "Execute continued pre-training of a 7B base model on 10B tokens of domain-specific text with careful learning rate scheduling to avoid catastrophic forgetting.",
        ),
        (
            "Train Reward Model from Preference Annotations",
            "Collect and process 20K pairwise preference annotations, train a Bradley-Terry reward model, and validate calibration against held-out human judgments.",
        ),
        (
            "Build Multi-GPU Training Infra with DeepSpeed",
            "Set up distributed training using DeepSpeed ZeRO Stage 3 across an 8-node GPU cluster with checkpoint sharding and fault-tolerant resumption.",
        ),
        (
            "Implement DPO Fine-Tuning Pipeline",
            "Build a Direct Preference Optimization pipeline as a simpler RLHF alternative, comparing quality and training stability on the same preference dataset.",
        ),
        (
            "Train Vision-Language Adapter for Document Understanding",
            "Fine-tune a LoRA adapter on a VLM for extracting structured data from invoices, receipts, and forms with 95%+ field-level accuracy.",
        ),
        (
            "Build Eval-Driven Training Loop with Auto Checkpointing",
            "Implement a training harness that runs benchmarks every N steps, auto-saves the best checkpoint, detects instability, and alerts on loss spikes.",
        ),
        (
            "Fine-Tune Whisper for Industry-Specific Transcription",
            "Adapt Whisper-large for medical dictation using 500 hours of labeled audio, targeting 30% WER reduction on domain-specific terminology.",
        ),
    ],
    Domain.HARDWARE: [
        (
            "Optimize LLM Inference Latency with TensorRT-LLM",
            "Convert a 70B model to TensorRT-LLM with INT8/FP8 quantization, continuous batching, and paged attention, targeting sub-200ms time-to-first-token.",
        ),
        (
            "Deploy On-Device ML Model for Mobile Classification",
            "Convert a PyTorch vision model to Core ML and TFLite, optimize with quantization-aware training, and benchmark on iPhone and Pixel hardware.",
        ),
        (
            "Build GPU Cluster Scheduling with Fair-Share Queuing",
            "Implement a scheduler for a shared GPU cluster enforcing per-team quotas, priority queuing, preemption policies, and utilization-based chargeback.",
        ),
        (
            "Implement Quantization Pipeline (GPTQ/AWQ/GGUF)",
            "Build an automated pipeline that takes any model, produces GPTQ, AWQ, and GGUF quantized variants, runs quality regression, and publishes passing models.",
        ),
        (
            "Deploy Edge Inference for Real-Time Video Analytics",
            "Set up an NVIDIA Jetson-based inference node running YOLO and a lightweight LLM for on-premises real-time camera analysis with local data processing.",
        ),
        (
            "Optimize vLLM Serving for Production Workload",
            "Profile and tune vLLM parameters—max batch size, KV cache, swap space, tensor parallelism—for target throughput at P99 latency SLA.",
        ),
        (
            "Build Multi-GPU Inference with Tensor Parallelism",
            "Configure and benchmark a 70B+ model serving across 4-8 GPUs with tensor and pipeline parallelism, optimizing throughput versus latency tradeoffs.",
        ),
        (
            "Implement Dynamic Batching for Inference Requests",
            "Build a request batching layer that groups incoming requests by sequence length and priority, maximizing GPU utilization within per-request latency SLAs.",
        ),
        (
            "Design Hybrid CPU/GPU Inference Architecture",
            "Architect a system routing lightweight requests to CPU inference and complex requests to GPU instances, reducing overall compute cost by 40%.",
        ),
        (
            "Set Up Triton Inference Server for Multi-Model Serving",
            "Deploy NVIDIA Triton to serve embedding, reranking, and generation models on shared GPU infrastructure with dynamic batching and concurrency control.",
        ),
        (
            "Build GPU Health Monitoring and Failover System",
            "Implement a daemon detecting GPU memory errors, thermal throttling, and NVLink degradation, automatically draining affected nodes and redistributing workloads.",
        ),
        (
            "Benchmark Specialized AI Accelerators vs H100",
            "Evaluate Groq, Cerebras, and custom ASICs against H100 GPUs, producing a cost-per-token and latency comparison with a migration recommendation.",
        ),
        (
            "Implement Speculative Decoding in Production Stack",
            "Integrate speculative decoding with a small draft model into the existing serving infrastructure, measuring real-world throughput improvement.",
        ),
    ],
}


def pick_task_text(rng, domain: Domain) -> tuple[str, str]:
    """Deterministically pick a (title, description) for *domain* using *rng*."""
    pool = TASK_POOL[domain]
    idx = rng.randint(0, len(pool) - 1)
    return pool[idx]
