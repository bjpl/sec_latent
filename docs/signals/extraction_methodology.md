# Signal Extraction Methodology

## Overview
This document details the technical implementation for extracting 150 latent signals from SEC filings.

---

## 1. LINGUISTIC DIMENSION EXTRACTION

### 1.1 Sentiment & Tone Signals (L001-L012)

#### L001: Forward-Looking Statement Sentiment

**Algorithm:**
```python
import re
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

class ForwardLookingSentimentExtractor:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
        self.model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
        self.future_markers = [
            r'\b(will|shall|expect|anticipate|believe|estimate|intend|may|could|should)\b',
            r'\b(forecast|project|plan|outlook|guidance)\b',
            r'\b(going forward|in the future|next year|upcoming)\b'
        ]

    def extract(self, mda_text):
        # Identify forward-looking sentences
        sentences = re.split(r'[.!?]+', mda_text)
        fls = []
        for sent in sentences:
            if any(re.search(pattern, sent, re.I) for pattern in self.future_markers):
                fls.append(sent)

        # Calculate aggregate sentiment
        if not fls:
            return 0.0

        sentiments = []
        for sent in fls:
            inputs = self.tokenizer(sent, return_tensors="pt", truncation=True, max_length=512)
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=1)
            # FinBERT outputs: [positive, negative, neutral]
            score = probs[0][0].item() - probs[0][1].item()  # positive - negative
            sentiments.append(score)

        return sum(sentiments) / len(sentiments)
```

**Dependencies:**
- transformers>=4.30.0
- torch>=2.0.0
- regex patterns for forward-looking language

**Validation:**
- Compare against hand-labeled FLS sentiment corpus
- Expected correlation with future stock returns: 0.15-0.25

---

#### L002: Risk Factor Negativity Score

**Algorithm:**
```python
class RiskFactorNegativityExtractor:
    def __init__(self):
        # Loughran-McDonald negative word list
        self.negative_words = self.load_lm_negative_dict()

    def load_lm_negative_dict(self):
        # Load from https://sraf.nd.edu/loughranmcdonald-master-dictionary/
        return set([
            'adverse', 'adversely', 'bankruptcy', 'breach', 'cease', 'closure',
            'damage', 'default', 'deficit', 'delay', 'delinquency', 'deteriorate',
            'difficulty', 'discontinue', 'dispute', 'fail', 'failure', 'harm',
            'inability', 'inadequate', 'incorrect', 'infringe', 'liability',
            'litigation', 'loss', 'losses', 'materially', 'negative', 'negatively',
            'problem', 'risk', 'risks', 'unable', 'uncertain', 'uncertainty',
            'unfavorable', 'unfavorably', 'unsuccessful', 'volatile', 'volatility'
            # ... (367 total words)
        ])

    def extract(self, risk_factors_text):
        words = re.findall(r'\b\w+\b', risk_factors_text.lower())
        negative_count = sum(1 for w in words if w in self.negative_words)

        # Normalize by section length (per 1000 words)
        word_count = len(words)
        if word_count == 0:
            return 0.0

        return (negative_count / word_count) * 1000
```

**Dependencies:**
- Loughran-McDonald Master Dictionary (2021 version)
- Regular expressions for word tokenization

**Validation:**
- Higher scores should correlate with future stock volatility
- Expected range: 20-80 for most companies

---

#### L003: Management Optimism Bias

**Algorithm:**
```python
class OptimismBiasExtractor:
    def __init__(self):
        self.sentiment_analyzer = ForwardLookingSentimentExtractor()

    def extract(self, mda_text, financial_metrics):
        """
        financial_metrics: dict with keys like 'revenue_growth', 'profit_margin_change'
        """
        # Calculate narrative sentiment
        narrative_sentiment = self.sentiment_analyzer.extract(mda_text)

        # Calculate financial performance score
        perf_score = (
            0.4 * financial_metrics.get('revenue_growth', 0) +
            0.3 * financial_metrics.get('profit_margin_change', 0) +
            0.3 * financial_metrics.get('earnings_growth', 0)
        )

        # Normalize to [-1, 1] range
        perf_score = max(-1, min(1, perf_score / 50))

        # Optimism bias = sentiment - performance
        return narrative_sentiment - perf_score
```

**Dependencies:**
- FinBERT sentiment model
- Financial statement parser for metrics

**Validation:**
- High positive bias may predict future disappointment
- Expected correlation with subsequent earnings surprise: -0.10 to -0.20

---

### 1.2 Linguistic Complexity Signals (L013-L020)

#### L013: Fog Index Evolution

**Algorithm:**
```python
import textstat

class FogIndexExtractor:
    def extract(self, current_text, prior_text):
        current_fog = textstat.gunning_fog(current_text)
        prior_fog = textstat.gunning_fog(prior_text) if prior_text else current_fog

        return current_fog - prior_fog
```

**Dependencies:**
- textstat>=0.7.3
- Prior year filing for comparison

**Validation:**
- Sudden increases (>2 points) may indicate obfuscation
- Li (2008): Higher fog index correlates with lower earnings persistence

---

#### L014: Sentence Length Variance

**Algorithm:**
```python
import numpy as np

class SentenceLengthVarianceExtractor:
    def extract(self, text):
        sentences = re.split(r'[.!?]+', text)
        sentence_lengths = [len(s.split()) for s in sentences if s.strip()]

        if len(sentence_lengths) < 2:
            return 0.0

        return np.std(sentence_lengths)
```

**Dependencies:**
- numpy>=1.24.0

**Validation:**
- High variance may indicate inconsistent writing quality
- Expected range: 5-30 for most filings

---

### 1.3 Semantic Pattern Signals (L021-L030)

#### L021: Topic Shift Volatility

**Algorithm:**
```python
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer
from scipy.stats import entropy

class TopicShiftExtractor:
    def __init__(self, n_topics=10):
        self.n_topics = n_topics
        self.vectorizer = CountVectorizer(max_features=5000, stop_words='english')
        self.lda = LatentDirichletAllocation(n_components=n_topics, random_state=42)

    def extract(self, section_texts):
        """
        section_texts: list of strings, each representing a major section
        """
        # Create document-term matrix
        dtm = self.vectorizer.fit_transform(section_texts)

        # Fit LDA model
        topic_distributions = self.lda.fit_transform(dtm)

        # Calculate entropy of topic distribution for each section
        entropies = [entropy(dist) for dist in topic_distributions]

        # Return average entropy (higher = less coherent)
        return np.mean(entropies)
```

**Dependencies:**
- scikit-learn>=1.3.0
- scipy>=1.11.0

**Validation:**
- High entropy may indicate unfocused disclosure
- Compare against industry averages

---

#### L022: MD&A Narrative Consistency

**Algorithm:**
```python
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class NarrativeConsistencyExtractor:
    def __init__(self):
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    def extract(self, current_mda, prior_mda):
        # Generate embeddings
        current_embedding = self.model.encode([current_mda])
        prior_embedding = self.model.encode([prior_mda])

        # Calculate cosine similarity
        similarity = cosine_similarity(current_embedding, prior_embedding)[0][0]

        return float(similarity)
```

**Dependencies:**
- sentence-transformers>=2.2.0
- Prior year MD&A section

**Validation:**
- Very low similarity (<0.4) may indicate business model change
- Expected range: 0.5-0.9 for stable companies

---

## 2. STRUCTURAL DIMENSION EXTRACTION

### 2.1 Document Architecture Signals (S001-S010)

#### S001: Total Document Length Trend

**Algorithm:**
```python
class DocumentLengthTrendExtractor:
    def extract(self, current_filing, prior_filing):
        current_words = len(current_filing.split())
        prior_words = len(prior_filing.split()) if prior_filing else current_words

        if prior_words == 0:
            return 0.0

        pct_change = ((current_words - prior_words) / prior_words) * 100
        return pct_change
```

**Dependencies:**
- None (basic string operations)

**Validation:**
- Sudden large increases (>30%) may signal complexity or issues
- Guay et al. (2016): Longer 10-Ks correlate with information uncertainty

---

#### S003: Item 1A Risk Factor Expansion

**Algorithm:**
```python
class RiskFactorExpansionExtractor:
    def extract_section(self, filing_text, item_number):
        """Extract specific Item section from 10-K"""
        pattern = rf'item\s+{item_number}[.\s]*(?P<title>[^\n]+)\n(?P<content>.*?)(?=item\s+\d+|$)'
        match = re.search(pattern, filing_text, re.I | re.DOTALL)

        if match:
            return match.group('content')
        return ""

    def extract(self, current_filing, prior_filing):
        current_rf = self.extract_section(current_filing, "1A")
        prior_rf = self.extract_section(prior_filing, "1A")

        current_words = len(current_rf.split())
        prior_words = len(prior_rf.split()) if prior_rf else current_words

        if prior_words == 0:
            return 0.0

        return ((current_words - prior_words) / prior_words) * 100
```

**Dependencies:**
- Regular expressions for section parsing

**Validation:**
- Campbell et al. (2014): Risk factor changes predict future volatility
- Large expansions (>50%) may signal emerging threats

---

### 2.2 Structural Change Signals (S011-S020)

#### S011: Section Reordering Events

**Algorithm:**
```python
from Levenshtein import distance as levenshtein_distance

class SectionReorderingExtractor:
    def extract_section_order(self, filing_text):
        """Extract ordered list of section titles"""
        pattern = r'item\s+(\d+[A-Z]*)[.\s]*([^\n]+)'
        matches = re.findall(pattern, filing_text, re.I)
        return [m[0] for m in matches]

    def extract(self, current_filing, prior_filing):
        current_order = self.extract_section_order(current_filing)
        prior_order = self.extract_section_order(prior_filing)

        # Convert to strings for Levenshtein distance
        current_str = ''.join(current_order)
        prior_str = ''.join(prior_order)

        return levenshtein_distance(current_str, prior_str)
```

**Dependencies:**
- python-Levenshtein>=0.21.0

**Validation:**
- Non-zero values indicate structural changes
- May correlate with management transitions or strategic shifts

---

## 3. NETWORK DIMENSION EXTRACTION

### 3.1 Entity Relationship Signals (N001-N010)

#### N001: Subsidiary Network Complexity

**Algorithm:**
```python
import spacy
from collections import defaultdict

class SubsidiaryNetworkExtractor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")

    def extract(self, exhibit_21_text):
        """
        Exhibit 21: List of Subsidiaries
        """
        doc = self.nlp(exhibit_21_text)

        # Extract entity names (ORG entities)
        subsidiaries = set()
        for ent in doc.ents:
            if ent.label_ == "ORG":
                subsidiaries.add(ent.text)

        # Parse ownership tiers (look for percentage patterns)
        ownership_pattern = r'(\d+)%'
        ownership_mentions = re.findall(ownership_pattern, exhibit_21_text)

        # Estimate tiers based on indentation or numbering
        tier_pattern = r'^\s+' # Indented lines suggest lower-tier subsidiaries
        lines = exhibit_21_text.split('\n')
        max_tier = 1
        for line in lines:
            indent = len(line) - len(line.lstrip())
            if indent > 0:
                tier = (indent // 4) + 1  # Assume 4-space indents
                max_tier = max(max_tier, tier)

        complexity = len(subsidiaries) + (max_tier * 10)
        return complexity
```

**Dependencies:**
- spacy>=3.6.0
- en_core_web_sm model

**Validation:**
- Dyreng & Lindsey (2009): Complex structures correlate with tax avoidance
- High complexity (>100) may indicate conglomerate structure

---

#### N003: Board Interlock Degree

**Algorithm:**
```python
import pandas as pd

class BoardInterlockExtractor:
    def __init__(self, director_database):
        """
        director_database: DataFrame with columns ['director_name', 'company_cik', 'company_name']
        Source: ISS Governance, BoardEx, or manual Form DEF 14A parsing
        """
        self.db = director_database

    def extract(self, company_cik, director_list):
        """
        director_list: list of director names from current company
        """
        interlocks = 0

        for director in director_list:
            # Find other companies where this director serves
            other_boards = self.db[
                (self.db['director_name'] == director) &
                (self.db['company_cik'] != company_cik)
            ]
            interlocks += len(other_boards)

        return interlocks
```

**Dependencies:**
- pandas>=2.0.0
- External director database (ISS, BoardEx, or custom)

**Validation:**
- Fracassi & Tate (2012): High interlocks correlate with agency costs
- Expected range: 0-20 for typical boards

---

### 3.2 Executive Network Signals (N011-N020)

#### N011: CEO Prior Company Count

**Algorithm:**
```python
class CEOExperienceExtractor:
    def extract(self, ceo_bio_text):
        """
        Parse CEO biography from proxy statement (DEF 14A)
        """
        # Look for patterns like "previously served at", "former [title] at"
        patterns = [
            r'(?:previously|formerly|prior to)\s+(?:served|worked|employed)\s+(?:as|at)\s+([A-Z][^\.,;]+)',
            r'(?:former|previous)\s+\w+\s+(?:of|at)\s+([A-Z][^\.,;]+)',
            r'(?:before joining|prior to)\s+(?:\w+\s+){0,3}([A-Z][^\.,;]+)'
        ]

        companies = set()
        for pattern in patterns:
            matches = re.findall(pattern, ceo_bio_text)
            companies.update(m.strip() for m in matches)

        # Filter out generic terms
        generic_terms = {'Board', 'Company', 'Corporation', 'Inc', 'LLC', 'Group'}
        companies = {c for c in companies if not any(g in c for g in generic_terms)}

        return len(companies)
```

**Dependencies:**
- Regular expressions

**Validation:**
- Custodio et al. (2013): Generalist CEOs command higher pay
- Expected range: 0-10 for most executives

---

## 4. TEMPORAL DIMENSION EXTRACTION

### 4.1 Time Series Pattern Signals (T001-T010)

#### T001: Filing Delay Duration

**Algorithm:**
```python
from datetime import datetime

class FilingDelayExtractor:
    def extract(self, fiscal_year_end, filing_date):
        """
        fiscal_year_end: str in format "YYYY-MM-DD"
        filing_date: str in format "YYYY-MM-DD"
        """
        fye = datetime.strptime(fiscal_year_end, "%Y-%m-%d")
        filed = datetime.strptime(filing_date, "%Y-%m-%d")

        delay = (filed - fye).days
        return delay
```

**Dependencies:**
- datetime (standard library)

**Validation:**
- Alford et al. (1994): Longer delays correlate with bad news
- Normal range: 45-75 days for large filers (60-day deadline)

---

#### T002: Filing Time of Day

**Algorithm:**
```python
class FilingTimeExtractor:
    def extract(self, filing_timestamp):
        """
        filing_timestamp: str like "2024-03-15 16:45:00"
        """
        dt = datetime.strptime(filing_timestamp, "%Y-%m-%d %H:%M:%S")
        hour = dt.hour

        # Negative signal if after-hours (4pm-8am EST)
        if hour >= 16 or hour < 8:
            return hour + 100  # Flag as after-hours

        return hour
```

**Dependencies:**
- datetime (standard library)

**Validation:**
- deHaan et al. (2015): After-hours filings contain more negative news
- After-hours indicator should predict negative returns

---

### 4.2 Trend Evolution Signals (T011-T020)

#### T011: Revenue Growth Acceleration

**Algorithm:**
```python
class RevenueAccelerationExtractor:
    def extract(self, revenue_series):
        """
        revenue_series: list of annual revenues [year -2, year -1, year 0]
        """
        if len(revenue_series) < 3:
            return 0.0

        # Calculate YoY growth rates
        growth_1 = ((revenue_series[-1] - revenue_series[-2]) / revenue_series[-2]) * 100
        growth_2 = ((revenue_series[-2] - revenue_series[-3]) / revenue_series[-3]) * 100

        # Acceleration = change in growth rate
        acceleration = growth_1 - growth_2
        return acceleration
```

**Dependencies:**
- None (basic arithmetic)

**Validation:**
- Chan et al. (2003): Revenue momentum predicts future returns
- Positive acceleration (>5%) is bullish signal

---

## 5. VISUAL DIMENSION EXTRACTION

### 5.1 Chart & Graph Analysis Signals (V001-V010)

#### V001: Chart Quantity Index

**Algorithm:**
```python
from PIL import Image
import io
import PyPDF2

class ChartQuantityExtractor:
    def extract_images_from_pdf(self, pdf_path):
        """Extract embedded images from PDF filing"""
        pdf_file = open(pdf_path, 'rb')
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        images = []
        for page in pdf_reader.pages:
            if '/XObject' in page['/Resources']:
                xObject = page['/Resources']['/XObject'].get_object()
                for obj in xObject:
                    if xObject[obj]['/Subtype'] == '/Image':
                        images.append(xObject[obj])

        return len(images)

    def extract_charts_from_html(self, html_content):
        """Extract chart elements from HTML filing"""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Look for chart indicators
        chart_tags = soup.find_all(['img', 'canvas', 'svg'])
        chart_count = len([t for t in chart_tags if 'chart' in str(t).lower() or 'graph' in str(t).lower()])

        return chart_count
```

**Dependencies:**
- PyPDF2>=3.0.0
- Pillow>=10.0.0
- beautifulsoup4>=4.12.0

**Validation:**
- Beattie & Jones (2001): More charts correlate with better presentation
- Expected range: 5-30 for typical 10-K

---

#### V006: Y-Axis Truncation Frequency

**Algorithm:**
```python
import cv2
import numpy as np
from PIL import Image
import pytesseract

class YAxisTruncationExtractor:
    def analyze_chart(self, image_path):
        """
        Detect if Y-axis starts at non-zero value
        """
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # OCR to find axis labels
        text = pytesseract.image_to_string(Image.open(image_path))

        # Look for Y-axis minimum value
        # Pattern: look for numbers at left edge of chart
        numbers = re.findall(r'\b(\d+(?:\.\d+)?)\b', text)

        if numbers:
            min_value = float(min(numbers))
            if min_value > 0:
                return 1  # Truncated

        return 0  # Not truncated
```

**Dependencies:**
- opencv-python>=4.8.0
- pytesseract>=0.3.10
- Tesseract OCR installed

**Validation:**
- Beattie & Jones (2002): Truncation used to exaggerate trends
- Manual verification on sample charts

---

## Signal Storage Schema

### PostgreSQL Tables

```sql
CREATE TABLE filings (
    filing_id SERIAL PRIMARY KEY,
    cik VARCHAR(10) NOT NULL,
    form_type VARCHAR(10) NOT NULL,
    filing_date DATE NOT NULL,
    fiscal_year_end DATE,
    file_path TEXT,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE linguistic_signals (
    filing_id INT REFERENCES filings(filing_id),
    signal_code VARCHAR(10) NOT NULL,
    signal_value FLOAT,
    extraction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (filing_id, signal_code)
);

CREATE TABLE structural_signals (
    filing_id INT REFERENCES filings(filing_id),
    signal_code VARCHAR(10) NOT NULL,
    signal_value FLOAT,
    extraction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (filing_id, signal_code)
);

-- Similar tables for network_signals, temporal_signals, visual_signals

CREATE INDEX idx_filing_date ON filings(filing_date);
CREATE INDEX idx_cik ON filings(cik);
```

### Vector Database (ChromaDB)

```python
import chromadb

# Store document embeddings for semantic search
client = chromadb.Client()
collection = client.create_collection(name="sec_filings")

collection.add(
    documents=[mda_text],
    metadatas=[{"cik": "0000789019", "filing_date": "2024-02-06"}],
    ids=["filing_001"]
)
```

---

## Batch Processing Pipeline

```python
class SignalExtractionPipeline:
    def __init__(self):
        self.linguistic_extractors = [
            ForwardLookingSentimentExtractor(),
            RiskFactorNegativityExtractor(),
            # ... all linguistic extractors
        ]
        self.structural_extractors = [
            DocumentLengthTrendExtractor(),
            RiskFactorExpansionExtractor(),
            # ... all structural extractors
        ]
        # ... other dimension extractors

    def process_filing(self, filing_path, cik):
        """Process single filing and extract all signals"""
        signals = {}

        # Load filing
        with open(filing_path, 'r') as f:
            filing_text = f.read()

        # Extract sections
        sections = self.parse_sections(filing_text)

        # Run all extractors
        for extractor in self.linguistic_extractors:
            signal_code = extractor.__class__.__name__.replace('Extractor', '')
            signals[signal_code] = extractor.extract(sections)

        # ... repeat for other dimensions

        return signals

    def batch_process(self, filing_list):
        """Process multiple filings in parallel"""
        from multiprocessing import Pool

        with Pool(processes=8) as pool:
            results = pool.map(self.process_filing, filing_list)

        return results
```

---

## Quality Assurance

### Unit Tests

```python
import pytest

def test_forward_looking_sentiment():
    extractor = ForwardLookingSentimentExtractor()

    # Positive FLS
    positive_text = "We expect significant revenue growth and improved margins."
    assert extractor.extract(positive_text) > 0.5

    # Negative FLS
    negative_text = "We anticipate challenges and may face adverse conditions."
    assert extractor.extract(negative_text) < -0.3
```

### Integration Tests

```python
def test_full_pipeline():
    pipeline = SignalExtractionPipeline()
    test_filing = "path/to/test_10k.html"

    signals = pipeline.process_filing(test_filing, "0000789019")

    # Verify all expected signals extracted
    assert len(signals) == 150
    assert all(isinstance(v, (int, float)) for v in signals.values())
```

---

## Performance Optimization

### Caching Strategy
- Cache parsed sections to avoid re-parsing
- Store intermediate embeddings in Redis
- Use memoization for expensive NLP operations

### Parallel Processing
- Process filings in parallel (multiprocessing)
- GPU acceleration for BERT models (CUDA)
- Batch inference for transformer models

### Monitoring
- Track extraction time per signal
- Alert on extraction failures
- Log data quality metrics

---

## API Specification

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class SignalRequest(BaseModel):
    cik: str
    form_type: str
    filing_date: str

@app.post("/extract_signals")
async def extract_signals(request: SignalRequest):
    """Extract all 150 signals from specified filing"""
    pipeline = SignalExtractionPipeline()
    signals = pipeline.process_filing(
        filing_path=fetch_filing(request.cik, request.form_type, request.filing_date),
        cik=request.cik
    )
    return {"signals": signals}

@app.get("/signals/{cik}/{signal_code}")
async def get_signal_history(cik: str, signal_code: str):
    """Get historical values for specific signal"""
    # Query database for time series
    return {"history": [...]}
```

---

## Next Implementation Steps

1. **Phase 1 (Weeks 1-2)**: Implement linguistic dimension extractors (L001-L040)
2. **Phase 2 (Weeks 3-4)**: Implement structural dimension extractors (S001-S030)
3. **Phase 3 (Weeks 5-6)**: Implement network dimension extractors (N001-N030)
4. **Phase 4 (Weeks 7-8)**: Implement temporal dimension extractors (T001-T030)
5. **Phase 5 (Weeks 9-10)**: Implement visual dimension extractors (V001-V020)
6. **Phase 6 (Week 11)**: Integration testing and validation
7. **Phase 7 (Week 12)**: API deployment and documentation
