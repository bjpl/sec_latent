# Ensemble Coordination Strategy

## Overview

This document defines the coordination strategy for the 5-model ensemble used in high-materiality SEC filing analysis, including voting mechanisms, disagreement resolution, and consensus building.

## Ensemble Architecture

### Model Composition

```
┌─────────────────────────────────────────────────────────────────┐
│                     ENSEMBLE COORDINATOR                         │
│                   (Orchestration Layer)                          │
└────────┬────────────┬────────────┬────────────┬─────────────────┘
         │            │            │            │
         ▼            ▼            ▼            ▼            ▼
┌─────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│  Financial  │ │   Risk   │ │Corporate │ │  Market  │ │Governance│
│   Metrics   │ │  Event   │ │ Actions  │ │  Impact  │ │ Analyzer │
│  Analyzer   │ │ Detector │ │Classifier│ │Predictor │ │          │
├─────────────┤ ├──────────┤ ├──────────┤ ├──────────┤ ├──────────┤
│ Phi3-Medium │ │Mistral-7B│ │ Gemma-9B │ │Qwen-14B  │ │Phi3-Mini │
│    14B      │ │          │ │          │ │          │ │   3.8B   │
│  Weight:25% │ │Weight:20%│ │Weight:20%│ │Weight:20%│ │Weight:15%│
└─────────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘
         │            │            │            │            │
         └────────────┴────────────┴────────────┴────────────┘
                                   │
                                   ▼
                        ┌─────────────────────┐
                        │  Consensus Builder   │
                        │  (Voting & Fusion)   │
                        └─────────────────────┘
```

## Model Specifications

### Model 1: Financial Metrics Analyzer
```yaml
model: microsoft/Phi-3-medium-4k-instruct
parameters: 14B
quantization: 4-bit Q4_K_M
context_length: 4096
memory_required: 8.5GB
specialty: Financial statement analysis
focus_sections:
  - Balance Sheet
  - Income Statement
  - Cash Flow Statement
  - Financial Ratios
  - Trend Analysis
ensemble_weight: 0.25
confidence_threshold: 0.85
```

**Strengths**:
- Superior financial calculation accuracy
- Excellent ratio interpretation
- Strong trend detection
- Efficient inference (3-4s)

**Weaknesses**:
- Limited context window
- Less effective on qualitative analysis
- Requires structured data format

### Model 2: Risk Event Detector
```yaml
model: mistralai/Mistral-7B-Instruct-v0.3
parameters: 7.3B
quantization: 4-bit Q4_K_M
context_length: 32768
memory_required: 4.5GB
specialty: Risk factor identification and sentiment analysis
focus_sections:
  - Risk Factors
  - Management Discussion & Analysis
  - Legal Proceedings
  - Contingencies
  - Footnotes
ensemble_weight: 0.20
confidence_threshold: 0.82
```

**Strengths**:
- Fast inference (2-3s)
- Large context window
- Good sentiment analysis
- Effective risk categorization

**Weaknesses**:
- Sometimes over-weights negative signals
- Less precise on quantitative risk metrics

### Model 3: Corporate Actions Classifier
```yaml
model: google/gemma-2-9b-it
parameters: 9.2B
quantization: 4-bit Q4_K_M
context_length: 8192
memory_required: 5.5GB
specialty: M&A, restructuring, leadership changes
focus_sections:
  - Material Events (8-K)
  - Business Changes
  - Significant Transactions
  - Executive Changes
  - Press Releases
ensemble_weight: 0.20
confidence_threshold: 0.88
```

**Strengths**:
- Excellent classification accuracy
- Strong entity relationship understanding
- Good at detecting corporate structure changes
- Fast inference (2.5-3.5s)

**Weaknesses**:
- Smaller context window
- Less effective on technical financial details

### Model 4: Market Impact Predictor
```yaml
model: Qwen/Qwen2.5-14B-Instruct
parameters: 14.7B
quantization: 4-bit Q4_K_M
context_length: 32768
memory_required: 9.0GB
specialty: Market reaction prediction, volatility estimation
focus_sections:
  - Forward-Looking Statements
  - Guidance
  - Material Events
  - Risk Factors
  - Strategic Initiatives
ensemble_weight: 0.20
confidence_threshold: 0.80
```

**Strengths**:
- Strong reasoning capabilities
- Good at market sentiment analysis
- Effective forward-looking prediction
- Large context window

**Weaknesses**:
- Slower inference (4-5s)
- Can be overly cautious in predictions

### Model 5: Governance Analyzer
```yaml
model: microsoft/Phi-3-mini-4k-instruct
parameters: 3.8B
quantization: 4-bit Q4_K_M
context_length: 4096
memory_required: 2.4GB
specialty: Corporate governance, compliance, internal controls
focus_sections:
  - Executive Compensation
  - Board Structure
  - Internal Controls (SOX)
  - Related Party Transactions
  - Audit Committee Reports
ensemble_weight: 0.15
confidence_threshold: 0.86
```

**Strengths**:
- Very fast inference (1.5-2s)
- Low memory footprint
- Good at structured governance analysis
- Efficient resource usage

**Weaknesses**:
- Limited context window
- Less effective on complex governance issues

## Voting Mechanisms

### 1. Weighted Confidence Voting

Primary voting mechanism that combines model weights with prediction confidence.

```python
def weighted_confidence_vote(predictions: List[ModelPrediction]) -> ConsensusResult:
    """
    Combines static model weights with dynamic confidence scores
    """
    total_weighted_confidence = 0
    weighted_scores = defaultdict(float)

    for pred in predictions:
        # Dynamic weight = base_weight * confidence
        dynamic_weight = MODEL_WEIGHTS[pred.model_id] * pred.confidence
        total_weighted_confidence += dynamic_weight

        # Accumulate weighted scores
        for key, score in pred.scores.items():
            weighted_scores[key] += score * dynamic_weight

    # Normalize by total weighted confidence
    consensus_scores = {
        k: v / total_weighted_confidence
        for k, v in weighted_scores.items()
    }

    return ConsensusResult(
        scores=consensus_scores,
        voting_method="weighted_confidence",
        total_weight=total_weighted_confidence
    )
```

**Use Cases**:
- Default voting mechanism
- All models have reasonable confidence (>0.70)
- Normal filing analysis

### 2. Majority Voting with Confidence Threshold

Used when disagreement is moderate and quick consensus is needed.

```python
def majority_vote_with_threshold(
    predictions: List[ModelPrediction],
    confidence_threshold: float = 0.75
) -> ConsensusResult:
    """
    Majority voting among high-confidence predictions
    """
    # Filter to high-confidence predictions
    high_conf_preds = [p for p in predictions if p.confidence >= confidence_threshold]

    if len(high_conf_preds) < 3:
        # Fallback to weighted voting if not enough confident predictions
        return weighted_confidence_vote(predictions)

    # Count votes for each category/score
    vote_counts = defaultdict(lambda: defaultdict(int))
    for pred in high_conf_preds:
        for key, value in pred.categorical_outputs.items():
            vote_counts[key][value] += 1

    # Select majority winner for each category
    consensus = {}
    for key, votes in vote_counts.items():
        winner = max(votes.items(), key=lambda x: x[1])
        consensus[key] = winner[0]

    return ConsensusResult(
        categories=consensus,
        voting_method="majority_threshold",
        voter_count=len(high_conf_preds)
    )
```

**Use Cases**:
- Medium disagreement (σ = 0.15-0.25)
- Categorical outputs (risk level, market impact)
- Time-sensitive analysis

### 3. Bayesian Model Averaging

Advanced fusion for continuous scores with uncertainty quantification.

```python
def bayesian_model_averaging(predictions: List[ModelPrediction]) -> ConsensusResult:
    """
    Bayesian fusion of model predictions with uncertainty
    """
    # Prior: Equal weight to each model
    prior_weights = np.array([MODEL_WEIGHTS[p.model_id] for p in predictions])
    prior_weights = prior_weights / prior_weights.sum()

    # Likelihood: Based on historical accuracy
    likelihoods = np.array([
        MODEL_HISTORICAL_ACCURACY[p.model_id] * p.confidence
        for p in predictions
    ])

    # Posterior: Bayesian update
    posterior_weights = prior_weights * likelihoods
    posterior_weights = posterior_weights / posterior_weights.sum()

    # Compute weighted average with uncertainty
    scores = np.array([p.score_vector for p in predictions])
    consensus_mean = np.average(scores, axis=0, weights=posterior_weights)
    consensus_std = np.sqrt(
        np.average((scores - consensus_mean)**2, axis=0, weights=posterior_weights)
    )

    return ConsensusResult(
        mean=consensus_mean,
        std=consensus_std,
        posterior_weights=posterior_weights,
        voting_method="bayesian_averaging"
    )
```

**Use Cases**:
- Continuous scores (financial metrics, risk scores)
- High-stakes decisions
- Uncertainty quantification required

### 4. Expert Panel with Specialization Boost

Boost weights for models in their domain of expertise.

```python
def expert_panel_vote(
    predictions: List[ModelPrediction],
    section_type: str
) -> ConsensusResult:
    """
    Boosts weight of expert models for specific sections
    """
    # Expertise boosting factors
    EXPERTISE_BOOST = {
        'financial_metrics': {'financial_analyzer': 1.5},
        'risk_factors': {'risk_detector': 1.5},
        'corporate_actions': {'actions_classifier': 1.5},
        'market_impact': {'impact_predictor': 1.5},
        'governance': {'governance_analyzer': 1.5}
    }

    boosted_weights = {}
    for pred in predictions:
        base_weight = MODEL_WEIGHTS[pred.model_id]
        boost = EXPERTISE_BOOST.get(section_type, {}).get(pred.model_id, 1.0)
        boosted_weights[pred.model_id] = base_weight * boost * pred.confidence

    # Normalize
    total_weight = sum(boosted_weights.values())
    normalized_weights = {k: v/total_weight for k, v in boosted_weights.items()}

    # Weighted average with boosted weights
    consensus = compute_weighted_average(predictions, normalized_weights)

    return ConsensusResult(
        scores=consensus,
        weights=normalized_weights,
        voting_method="expert_panel"
    )
```

**Use Cases**:
- Section-specific analysis
- Leveraging model specializations
- Improving domain-specific accuracy

## Disagreement Detection & Resolution

### Disagreement Metrics

#### 1. Standard Deviation of Predictions
```python
def calculate_prediction_disagreement(predictions: List[ModelPrediction]) -> float:
    """
    Calculate normalized standard deviation across predictions
    """
    scores = np.array([p.normalized_score_vector for p in predictions])
    std_dev = np.std(scores, axis=0)
    mean_std = np.mean(std_dev)
    return mean_std
```

#### 2. Pairwise Agreement Score
```python
def pairwise_agreement(predictions: List[ModelPrediction]) -> float:
    """
    Calculate average pairwise agreement (cosine similarity)
    """
    n = len(predictions)
    total_similarity = 0

    for i in range(n):
        for j in range(i+1, n):
            sim = cosine_similarity(
                predictions[i].score_vector,
                predictions[j].score_vector
            )
            total_similarity += sim

    avg_similarity = total_similarity / (n * (n-1) / 2)
    return avg_similarity
```

#### 3. Confidence Spread
```python
def confidence_spread(predictions: List[ModelPrediction]) -> float:
    """
    Measure spread in confidence levels
    """
    confidences = [p.confidence for p in predictions]
    return max(confidences) - min(confidences)
```

### Disagreement Categories

#### Low Disagreement (σ < 0.15)
```yaml
characteristics:
  - Standard deviation < 0.15
  - Pairwise agreement > 0.85
  - Confidence spread < 0.20

resolution:
  - Use weighted_confidence_vote
  - No additional review
  - High confidence in consensus

output_quality: 0.97
consensus_time: <1s
```

#### Medium Disagreement (0.15 ≤ σ < 0.30)
```yaml
characteristics:
  - Standard deviation 0.15-0.30
  - Pairwise agreement 0.70-0.85
  - Confidence spread 0.20-0.35

resolution:
  - Use majority_vote_with_threshold
  - Flag for quality review
  - Include dissenting opinions

output_quality: 0.93
consensus_time: 1-2s
```

#### High Disagreement (σ ≥ 0.30)
```yaml
characteristics:
  - Standard deviation ≥ 0.30
  - Pairwise agreement < 0.70
  - Confidence spread > 0.35

resolution:
  - Escalate to human review
  - Provide all model predictions
  - Highlight points of contention
  - Use bayesian_averaging with uncertainty

output_quality: 0.85 (needs review)
consensus_time: 2-3s + human review
```

### Resolution Strategies

#### Strategy 1: Confidence-Based Tie-Breaking
When 2-3 models agree, use their combined confidence vs. dissenting models.

```python
def confidence_tie_break(predictions: List[ModelPrediction]) -> ConsensusResult:
    """
    Break ties by comparing total confidence of agreeing groups
    """
    # Group predictions by similarity
    groups = cluster_similar_predictions(predictions, threshold=0.15)

    # Calculate total confidence per group
    group_confidences = [
        sum(p.confidence for p in group)
        for group in groups
    ]

    # Select group with highest total confidence
    winner_idx = np.argmax(group_confidences)
    winning_group = groups[winner_idx]

    # Return consensus from winning group
    return weighted_confidence_vote(winning_group)
```

#### Strategy 2: Evidence-Based Adjudication
When models disagree, extract supporting evidence and compare strength.

```python
def evidence_based_resolution(
    predictions: List[ModelPrediction],
    filing_text: str
) -> ConsensusResult:
    """
    Resolve disagreement by examining cited evidence
    """
    evidence_scores = []

    for pred in predictions:
        # Score quality of cited evidence
        score = evaluate_evidence_quality(
            pred.cited_passages,
            filing_text,
            pred.claim
        )
        evidence_scores.append(score)

    # Weight predictions by evidence quality
    evidence_weights = np.array(evidence_scores)
    evidence_weights = evidence_weights / evidence_weights.sum()

    consensus = compute_weighted_average(predictions, evidence_weights)

    return ConsensusResult(
        scores=consensus,
        evidence_weights=evidence_weights,
        resolution_method="evidence_based"
    )
```

#### Strategy 3: Cascading Consensus
Try multiple voting methods in order until consensus is reached.

```python
def cascading_consensus(predictions: List[ModelPrediction]) -> ConsensusResult:
    """
    Try increasingly sophisticated voting methods
    """
    # Level 1: Simple weighted vote
    result = weighted_confidence_vote(predictions)
    if result.confidence > 0.90:
        return result

    # Level 2: Majority with threshold
    result = majority_vote_with_threshold(predictions)
    if result.confidence > 0.85:
        return result

    # Level 3: Expert panel (if section identified)
    if hasattr(predictions[0], 'section_type'):
        result = expert_panel_vote(predictions, predictions[0].section_type)
        if result.confidence > 0.80:
            return result

    # Level 4: Bayesian averaging with uncertainty
    result = bayesian_model_averaging(predictions)

    # Level 5: Flag for human review if still uncertain
    if result.confidence < 0.75:
        result.needs_human_review = True

    return result
```

## Coordination Protocol

### Parallel Execution
All 5 models run in parallel to minimize latency.

```python
async def run_ensemble(filing: Filing) -> ConsensusResult:
    """
    Execute all models in parallel
    """
    # Launch all models concurrently
    tasks = [
        run_financial_analyzer(filing),
        run_risk_detector(filing),
        run_corporate_actions(filing),
        run_market_predictor(filing),
        run_governance_analyzer(filing)
    ]

    # Wait for all with timeout
    predictions = await asyncio.gather(*tasks, timeout=20.0)

    # Build consensus
    consensus = cascading_consensus(predictions)

    return consensus
```

### Resource Management
Ensure models don't compete for GPU resources.

```python
class EnsembleResourceManager:
    def __init__(self):
        self.gpu_semaphore = asyncio.Semaphore(2)  # Max 2 models on GPU at once
        self.memory_limit = 26 * 1024**3  # 26GB

    async def run_with_resource_control(self, model_fn, *args):
        """
        Run model with resource constraints
        """
        async with self.gpu_semaphore:
            return await model_fn(*args)
```

## Quality Assurance

### Ensemble Health Metrics
```yaml
# Model availability
all_models_responsive: >0.99
partial_ensemble_fallback: <0.02

# Prediction quality
consensus_confidence_avg: >0.90
high_disagreement_rate: <0.12
human_review_rate: <0.15

# Performance
ensemble_latency_p95: <21s
individual_model_timeout_rate: <0.01
```

### Calibration Monitoring
```python
def monitor_ensemble_calibration():
    """
    Track if ensemble confidence matches actual accuracy
    """
    # Bucket predictions by confidence
    buckets = {
        '0.90-1.00': [],
        '0.80-0.90': [],
        '0.70-0.80': [],
        '<0.70': []
    }

    # Check actual accuracy in each bucket
    for pred, actual in prediction_history:
        bucket = get_confidence_bucket(pred.confidence)
        buckets[bucket].append(pred.score == actual)

    # Alert if accuracy < confidence
    for bucket, results in buckets.items():
        accuracy = np.mean(results)
        expected_conf = get_bucket_midpoint(bucket)

        if accuracy < expected_conf - 0.05:
            alert(f"Ensemble miscalibrated in bucket {bucket}")
```

---

**Document Version**: 1.0
**Last Updated**: 2025-10-18
**Owner**: Model Orchestration Analyst
**Review Cycle**: Monthly
