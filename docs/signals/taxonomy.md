# SEC Filing Latent Signal Taxonomy

## Overview
This taxonomy catalogs 150 latent signals extracted from SEC filings across five analytical dimensions. Each signal is designed to capture subtle patterns that may predict market movements, regulatory issues, or corporate health.

---

## 1. LINGUISTIC DIMENSION (40 Signals)

### 1.1 Sentiment & Tone Analysis (12 signals)

**L001: Forward-Looking Statement Sentiment**
- **Description**: Sentiment polarity of forward-looking statements (MD&A section)
- **Extraction**: VADER/FinBERT sentiment on sentences containing future-tense verbs and forward-looking disclaimers
- **Range**: [-1.0, 1.0]
- **Research**: Loughran & McDonald (2011) financial sentiment dictionary

**L002: Risk Factor Negativity Score**
- **Description**: Intensity of negative language in Risk Factors section
- **Extraction**: Negative word frequency weighted by section length
- **Range**: [0, 100]
- **Research**: Kravet & Muslu (2013) - risk disclosure informativeness

**L003: Management Optimism Bias**
- **Description**: Divergence between MD&A tone and financial performance
- **Extraction**: Sentiment delta between management narrative and actual results
- **Range**: [-2.0, 2.0]
- **Research**: Davis et al. (2015) - managerial tone management

**L004: Legal Proceeding Urgency**
- **Description**: Linguistic markers of litigation severity
- **Extraction**: Frequency of urgent terms ("immediate," "substantial," "adverse")
- **Range**: [0, 10]
- **Research**: Hopkins (1996) - litigation risk disclosure

**L005: Competitive Threat Language**
- **Description**: Intensity of competitive pressure mentions
- **Extraction**: Competitive keyword density in business description
- **Range**: [0, 100]
- **Research**: Li (2008) - textual analysis in corporate disclosures

**L006: Innovation Signal Strength**
- **Description**: R&D and innovation-related language intensity
- **Extraction**: Patent, research, development keyword clustering
- **Range**: [0, 100]
- **Research**: Kogan et al. (2017) - technological innovation and asset prices

**L007: Regulatory Concern Intensity**
- **Description**: Regulatory risk language frequency
- **Extraction**: Government, regulation, compliance keyword analysis
- **Range**: [0, 100]
- **Research**: Durnev & Kim (2005) - regulatory environment effects

**L008: Customer Concentration Warning**
- **Description**: Dependency language around major customers
- **Extraction**: Customer dependency phrases, revenue concentration terms
- **Range**: [0, 10]
- **Research**: Patatoukas (2012) - customer-base concentration

**L009: Supply Chain Vulnerability**
- **Description**: Supply disruption risk language
- **Extraction**: Supplier dependency, shortage, disruption terms
- **Range**: [0, 10]
- **Research**: Barrot & Sauvagnat (2016) - input specificity

**L010: ESG Commitment Authenticity**
- **Description**: Genuine vs. performative ESG language
- **Extraction**: Concrete action verbs vs. aspirational statements ratio
- **Range**: [0, 1]
- **Research**: Eccles & Serafeim (2013) - corporate sustainability

**L011: Accounting Estimate Confidence**
- **Description**: Certainty language around critical accounting estimates
- **Extraction**: Hedge words vs. certainty markers in accounting policy notes
- **Range**: [0, 1]
- **Research**: Guay et al. (2016) - estimate uncertainty

**L012: Executive Departure Tone**
- **Description**: Sentiment around officer/director changes
- **Extraction**: Sentiment analysis of Item 5.02 disclosures
- **Range**: [-1.0, 1.0]
- **Research**: Fee & Hadlock (2003) - management turnover

### 1.2 Linguistic Complexity (8 signals)

**L013: Fog Index Evolution**
- **Description**: Document readability complexity trend
- **Extraction**: Gunning Fog Index year-over-year change
- **Range**: [0, 30]
- **Research**: Li (2008) - readability and earnings management

**L014: Sentence Length Variance**
- **Description**: Sentence structure inconsistency
- **Extraction**: Standard deviation of sentence lengths
- **Range**: [0, 100]
- **Research**: Lehavy et al. (2011) - linguistic complexity

**L015: Passive Voice Density**
- **Description**: Responsibility obfuscation through passive constructions
- **Extraction**: Passive verb phrase frequency
- **Range**: [0, 100]
- **Research**: Merkl-Davies & Brennan (2007) - impression management

**L016: Jargon Saturation**
- **Description**: Industry-specific terminology density
- **Extraction**: Technical term frequency vs. plain language ratio
- **Range**: [0, 1]
- **Research**: Bloomfield (2008) - communication complexity

**L017: Acronym Proliferation**
- **Description**: Unexplained acronym frequency
- **Extraction**: Uppercase abbreviation count without prior definition
- **Range**: [0, 100]
- **Research**: Miller (2010) - disclosure obfuscation

**L018: Syntactic Complexity Score**
- **Description**: Parse tree depth and clause nesting
- **Extraction**: Average dependency parse tree depth
- **Range**: [0, 20]
- **Research**: Cazier & Pfeiffer (2016) - syntactic complexity

**L019: Lexical Diversity Index**
- **Description**: Vocabulary richness (type-token ratio)
- **Extraction**: Unique words / total words (moving average)
- **Range**: [0, 1]
- **Research**: Bushee et al. (2018) - linguistic characteristics

**L020: Modal Verb Hedging**
- **Description**: Uncertainty expression through modal verbs
- **Extraction**: "May," "might," "could," "would" frequency
- **Range**: [0, 100]
- **Research**: Schrand & Zechman (2012) - executive overconfidence

### 1.3 Semantic Patterns (10 signals)

**L021: Topic Shift Volatility**
- **Description**: Semantic coherence across sections
- **Extraction**: LDA topic distribution entropy
- **Range**: [0, 10]
- **Research**: Bao & Datta (2014) - topic modeling

**L022: MD&A Narrative Consistency**
- **Description**: Year-over-year semantic similarity
- **Extraction**: Cosine similarity of section embeddings (BERT)
- **Range**: [0, 1]
- **Research**: Brown & Tucker (2011) - MD&A comparability

**L023: Forward-Looking Statement Density**
- **Description**: Future-oriented language frequency
- **Extraction**: Future tense verbs and temporal markers per 1000 words
- **Range**: [0, 100]
- **Research**: Muslu et al. (2015) - forward-looking disclosures

**L024: Boilerplate Language Ratio**
- **Description**: Templated vs. customized disclosure
- **Extraction**: N-gram overlap with industry peers
- **Range**: [0, 1]
- **Research**: Lang & Stice-Lawrence (2015) - disclosure commonality

**L025: Causality Chain Length**
- **Description**: Causal reasoning complexity
- **Extraction**: Average causal relationship depth (because/therefore/thus)
- **Range**: [0, 10]
- **Research**: Tan et al. (2015) - causal explanations

**L026: Negative Framing Frequency**
- **Description**: Loss vs. gain framing prevalence
- **Extraction**: Loss-frame language ("avoid," "prevent") vs. gain-frame ratio
- **Range**: [0, 1]
- **Research**: Leary & Altman (2013) - framing effects

**L027: Quantitative Reference Density**
- **Description**: Numerical specificity in narratives
- **Extraction**: Number mentions per paragraph
- **Range**: [0, 50]
- **Research**: Blankespoor (2019) - quantitative disclosure

**L028: Comparative Statement Intensity**
- **Description**: Frequency of comparative language
- **Extraction**: "Better," "worse," "improve," "decline" per section
- **Range**: [0, 100]
- **Research**: Huang et al. (2014) - tone consistency

**L029: Action Verb to Noun Ratio**
- **Description**: Dynamic vs. static language balance
- **Extraction**: Verb/noun ratio in key sections
- **Range**: [0, 3]
- **Research**: Demers & Vega (2010) - linguistic style

**L030: Metaphor Density**
- **Description**: Abstract conceptualization frequency
- **Extraction**: Figurative language detection (ML classifier)
- **Range**: [0, 50]
- **Research**: Charteris-Black & Ennis (2001) - business metaphors

### 1.4 Linguistic Anomalies (10 signals)

**L031: Sudden Readability Drop**
- **Description**: Abrupt complexity increase
- **Extraction**: Year-over-year Flesch-Kincaid grade level change > 2
- **Binary**: [0, 1]
- **Research**: Asay et al. (2018) - readability changes

**L032: Disclaimers Proliferation**
- **Description**: Legal disclaimer expansion
- **Extraction**: Safe harbor statement length change %
- **Range**: [-100, 500]
- **Research**: Baginski et al. (2002) - forward-looking statements

**L033: Sentiment Inconsistency**
- **Description**: Misalignment between sections
- **Extraction**: Sentiment variance across MD&A, Risk Factors, Business
- **Range**: [0, 2]
- **Research**: Feldman et al. (2010) - sentiment consistency

**L034: Unusual Word Choice**
- **Description**: Atypical vocabulary for company/industry
- **Extraction**: TF-IDF anomaly score
- **Range**: [0, 100]
- **Research**: Hoberg & Phillips (2016) - text-based networks

**L035: Repetition Anomaly**
- **Description**: Unusual phrase repetition patterns
- **Extraction**: High-frequency n-gram z-score
- **Range**: [0, 10]
- **Research**: Zhou (2014) - linguistic deception

**L036: Pronoun Shift Pattern**
- **Description**: Change in personal pronoun usage (we/I)
- **Extraction**: First-person plural vs. singular ratio change
- **Range**: [-5, 5]
- **Research**: Pennebaker (2011) - psychological text analysis

**L037: Temporal Reference Bias**
- **Description**: Past vs. future orientation imbalance
- **Extraction**: Past tense / future tense verb ratio
- **Range**: [0, 10]
- **Research**: Henry (2008) - temporal framing

**L038: Negation Density Spike**
- **Description**: Unusual negative construction frequency
- **Extraction**: "Not," "no," "never" z-score vs. historical average
- **Range**: [0, 10]
- **Research**: Loughran & McDonald (2016) - negativity

**L039: Question Frequency Anomaly**
- **Description**: Rhetorical question usage change
- **Extraction**: Question marks per 1000 words delta
- **Range**: [-10, 10]
- **Research**: Li (2010) - linguistic features

**L040: Subordinate Clause Explosion**
- **Description**: Sudden increase in sentence complexity
- **Extraction**: Average clauses per sentence delta
- **Range**: [-5, 5]
- **Research**: Dyer et al. (2017) - linguistic complexity

---

## 2. STRUCTURAL DIMENSION (30 Signals)

### 2.1 Document Architecture (10 signals)

**S001: Total Document Length Trend**
- **Description**: Filing length evolution over time
- **Extraction**: Total word count year-over-year % change
- **Range**: [-50, 200]
- **Research**: Guay et al. (2016) - disclosure length

**S002: Section Length Imbalance**
- **Description**: Disproportionate section sizes
- **Extraction**: Gini coefficient of section lengths
- **Range**: [0, 1]
- **Research**: Li (2008) - disclosure structure

**S003: Item 1A Risk Factor Expansion**
- **Description**: Risk disclosure growth rate
- **Extraction**: Risk Factors section length % change
- **Range**: [-50, 300]
- **Research**: Campbell et al. (2014) - risk disclosure

**S004: MD&A Narrative Depth**
- **Description**: Management discussion comprehensiveness
- **Extraction**: MD&A word count / revenue ratio
- **Range**: [0, 100]
- **Research**: Cole & Jones (2005) - MD&A quality

**S005: Footnote Proliferation Rate**
- **Description**: Financial statement note expansion
- **Extraction**: Footnote count year-over-year change
- **Range**: [-20, 100]
- **Research**: Li (2010) - footnote complexity

**S006: Exhibit Attachment Volume**
- **Description**: Supporting document quantity
- **Extraction**: Number of exhibits filed
- **Range**: [0, 200]
- **Research**: Hanley & Hoberg (2019) - exhibit information

**S007: Cross-Reference Density**
- **Description**: Document interconnectedness
- **Extraction**: Internal cross-references per page
- **Range**: [0, 20]
- **Research**: Loughran & McDonald (2014) - document structure

**S008: Subsection Fragmentation**
- **Description**: Granular breakdown of major sections
- **Extraction**: Average subsections per main section
- **Range**: [0, 50]
- **Research**: SEC (2013) - plain English guidelines

**S009: Bullet Point Usage Intensity**
- **Description**: List formatting frequency
- **Extraction**: Bullet/numbered list items per page
- **Range**: [0, 30]
- **Research**: Courtis (2004) - disclosure format

**S010: White Space Ratio**
- **Description**: Visual density of text
- **Extraction**: Character density per page
- **Range**: [0, 5000]
- **Research**: Li (2008) - readability formatting

### 2.2 Structural Changes (10 signals)

**S011: Section Reordering Events**
- **Description**: Major structural reorganization
- **Extraction**: Levenshtein distance of section sequences
- **Range**: [0, 20]
- **Research**: Huang et al. (2014) - disclosure changes

**S012: New Section Introduction**
- **Description**: Novel disclosure sections added
- **Extraction**: Section titles not in prior year filing
- **Range**: [0, 10]
- **Research**: Li et al. (2013) - disclosure innovation

**S013: Section Elimination Pattern**
- **Description**: Disclosure removal or consolidation
- **Extraction**: Prior-year sections absent in current filing
- **Range**: [0, 10]
- **Research**: Chen et al. (2015) - disclosure quality

**S014: Table Complexity Evolution**
- **Description**: Tabular data presentation changes
- **Extraction**: Average columns per table delta
- **Range**: [-10, 10]
- **Research**: Blankespoor et al. (2014) - information design

**S015: Historical Data Depth Change**
- **Description**: Time series disclosure extension/contraction
- **Extraction**: Years of historical data presented
- **Range**: [1, 10]
- **Research**: Lehavy et al. (2011) - historical disclosure

**S016: Segment Reporting Granularity**
- **Description**: Business segment breakdown detail
- **Extraction**: Number of reportable segments
- **Range**: [1, 20]
- **Research**: Berger & Hann (2007) - segment disclosure

**S017: Geographic Breakdown Detail**
- **Description**: Spatial revenue/operations granularity
- **Extraction**: Number of geographic regions reported
- **Range**: [1, 50]
- **Research**: Hope et al. (2013) - geographic disclosure

**S018: Product Line Disclosure Depth**
- **Description**: Product category granularity
- **Extraction**: Product/service categories disclosed
- **Range**: [1, 30]
- **Research**: Berger & Hann (2003) - product disclosure

**S019: Contractual Obligation Horizon**
- **Description**: Future commitment disclosure timeline
- **Extraction**: Years covered in contractual obligations table
- **Range**: [1, 10]
- **Research**: Nini et al. (2012) - debt covenant disclosure

**S020: Critical Accounting Policy Count**
- **Description**: Policies identified as "critical"
- **Extraction**: Number of critical accounting estimates
- **Range**: [0, 15]
- **Research**: Linsmeier (2011) - critical estimates

### 2.3 Formatting Patterns (10 signals)

**S021: Bold Text Emphasis Frequency**
- **Description**: Visual highlighting usage
- **Extraction**: Bold-formatted words per page
- **Range**: [0, 100]
- **Research**: Guillamon-Saorin et al. (2017) - typographic emphasis

**S022: Italic Usage Pattern**
- **Description**: Emphasis or definition markers
- **Extraction**: Italicized text frequency
- **Range**: [0, 100]
- **Research**: Lee (2012) - disclosure emphasis

**S023: ALL CAPS Alert Frequency**
- **Description**: Urgent warning markers
- **Extraction**: All-uppercase word frequency
- **Range**: [0, 50]
- **Research**: SEC plain English guidelines

**S024: Hyperlink Density**
- **Description**: XBRL tagging and external references
- **Extraction**: Hyperlinks per page
- **Range**: [0, 50]
- **Research**: Debreceny et al. (2011) - XBRL tagging

**S025: Paragraph Length Variance**
- **Description**: Text chunking consistency
- **Extraction**: Standard deviation of paragraph lengths
- **Range**: [0, 500]
- **Research**: Li (2008) - document readability

**S026: Indentation Depth Complexity**
- **Description**: Hierarchical structure complexity
- **Extraction**: Average indentation levels
- **Range**: [0, 10]
- **Research**: Dyer et al. (2017) - document structure

**S027: Header/Footer Consistency**
- **Description**: Document navigation aids
- **Extraction**: Header/footer information richness
- **Range**: [0, 10]
- **Research**: SEC Edgar filing guidelines

**S028: Page Break Logic**
- **Description**: Document segmentation strategy
- **Extraction**: Pages per major section
- **Range**: [0, 100]
- **Research**: Li (2008) - filing organization

**S029: Font Size Variation**
- **Description**: Visual hierarchy through typography (HTML/XBRL)
- **Extraction**: Distinct font sizes used
- **Range**: [1, 10]
- **Research**: Dyer et al. (2017) - presentation format

**S030: Color Usage Intensity**
- **Description**: Visual distinction in modern filings
- **Extraction**: Non-black text color usage (HTML filings)
- **Range**: [0, 100]
- **Research**: Blankespoor et al. (2014) - digital disclosure

---

## 3. NETWORK DIMENSION (30 Signals)

### 3.1 Entity Relationships (10 signals)

**N001: Subsidiary Network Complexity**
- **Description**: Corporate structure intricacy
- **Extraction**: Number of subsidiaries + ownership tiers
- **Range**: [0, 500]
- **Research**: Dyreng & Lindsey (2009) - corporate structure

**N002: Joint Venture Web Size**
- **Description**: Strategic partnership network
- **Extraction**: Number of joint ventures and equity investments
- **Range**: [0, 50]
- **Research**: Folta (1998) - governance structures

**N003: Board Interlock Degree**
- **Description**: Director network centrality
- **Extraction**: Shared directors with other public companies
- **Range**: [0, 100]
- **Research**: Fracassi & Tate (2012) - board interlocks

**N004: Auditor Industry Dominance**
- **Description**: Auditor market share in sector
- **Extraction**: Auditor's % of industry clients
- **Range**: [0, 100]
- **Research**: Francis et al. (2013) - auditor expertise

**N005: Legal Counsel Prestige**
- **Description**: Law firm reputation indicator
- **Extraction**: Vault/Chambers law firm ranking
- **Range**: [0, 100]
- **Research**: Krishnan & Wang (2014) - legal quality

**N006: Insider Trading Network**
- **Description**: Form 4 transaction patterns
- **Extraction**: Number of insiders with trades in period
- **Range**: [0, 50]
- **Research**: Cohen et al. (2012) - insider networks

**N007: Institutional Investor Overlap**
- **Description**: Shared institutional holders with peers
- **Extraction**: Jaccard similarity of top-20 institutional holders
- **Range**: [0, 1]
- **Research**: Hong & Kacperczyk (2009) - investor networks

**N008: Analyst Coverage Network**
- **Description**: Sell-side research coverage
- **Extraction**: Number of analysts covering the stock
- **Range**: [0, 100]
- **Research**: Frankel et al. (2006) - analyst following

**N009: Supplier Concentration**
- **Description**: Supply chain dependency
- **Extraction**: % revenue from top 3 suppliers (if disclosed)
- **Range**: [0, 100]
- **Research**: Fee et al. (2006) - supply chain risk

**N010: Customer Concentration Risk**
- **Description**: Revenue dependency on key customers
- **Extraction**: % revenue from top customers
- **Range**: [0, 100]
- **Research**: Patatoukas (2012) - customer concentration

### 3.2 Executive Networks (10 signals)

**N011: CEO Prior Company Count**
- **Description**: Executive experience breadth
- **Extraction**: Number of prior employer companies
- **Range**: [0, 20]
- **Research**: Custodio et al. (2013) - general managerial skills

**N012: Executive Education Network**
- **Description**: Management team educational clustering
- **Extraction**: Number of shared educational institutions
- **Range**: [0, 30]
- **Research**: Fracassi & Tate (2012) - social ties

**N013: Board Independence Score**
- **Description**: Director independence from management
- **Extraction**: Independent directors / total board seats
- **Range**: [0, 1]
- **Research**: Hermalin & Weisbach (2003) - board composition

**N014: Compensation Committee Network**
- **Description**: Compensation linkages across companies
- **Extraction**: Shared compensation committee members
- **Range**: [0, 20]
- **Research**: Hallock (1997) - interlocking boards

**N015: CFO Turnover Clustering**
- **Description**: Financial executive stability
- **Extraction**: CFO tenure relative to industry median
- **Range**: [0, 30] years
- **Research**: Mian (2001) - CFO characteristics

**N016: Founder-CEO Presence**
- **Description**: Founding team continuity
- **Extraction**: Binary indicator of founder involvement
- **Binary**: [0, 1]
- **Research**: Adams et al. (2009) - founder-CEOs

**N017: Nepotism Indicator**
- **Description**: Family relationships in management
- **Extraction**: Shared surnames in executive/board listings
- **Range**: [0, 10]
- **Research**: Villalonga & Amit (2006) - family firms

**N018: Political Connection Score**
- **Description**: Government relationship strength
- **Extraction**: Former government officials on board/management
- **Range**: [0, 10]
- **Research**: Faccio (2006) - political connections

**N019: Academic Advisory Network**
- **Description**: University/research institution ties
- **Extraction**: Board members with academic affiliations
- **Range**: [0, 10]
- **Research**: Lacetera et al. (2004) - academic ties

**N020: Trade Association Leadership**
- **Description**: Industry group involvement
- **Extraction**: Officers serving on industry boards
- **Range**: [0, 5]
- **Research**: Barnea & Guedj (2009) - industry networks

### 3.3 Corporate Actions Network (10 signals)

**N021: M&A Activity Frequency**
- **Description**: Acquisition transaction rate
- **Extraction**: Number of acquisitions in 8-K filings
- **Range**: [0, 50]
- **Research**: Moeller et al. (2004) - acquisition frequency

**N022: Strategic Alliance Count**
- **Description**: Partnership and collaboration volume
- **Extraction**: Material agreements disclosed
- **Range**: [0, 100]
- **Research**: Anand & Khanna (2000) - alliance networks

**N023: Divestiture Pattern**
- **Description**: Asset sale and spin-off activity
- **Extraction**: Number of divestitures disclosed
- **Range**: [0, 20]
- **Research**: Brauer (2006) - divestiture decisions

**N024: Licensing Agreement Depth**
- **Description**: IP and technology licensing activity
- **Extraction**: License agreements disclosed
- **Range**: [0, 50]
- **Research**: Fosfuri (2006) - licensing strategies

**N025: R&D Collaboration Network**
- **Description**: Research partnership ecosystem
- **Extraction**: R&D partners mentioned
- **Range**: [0, 30]
- **Research**: Hagedoorn (2002) - R&D partnerships

**N026: Supply Chain Integration Level**
- **Description**: Vertical integration vs. outsourcing
- **Extraction**: Make-vs-buy ratio indicators from narrative
- **Range**: [0, 1]
- **Research**: Acemoglu et al. (2010) - vertical integration

**N027: Distribution Channel Diversity**
- **Description**: Market access pathway variety
- **Extraction**: Distinct distribution channels described
- **Range**: [0, 20]
- **Research**: Hortacsu & Syverson (2007) - distribution networks

**N028: Patent Citation Network**
- **Description**: IP interconnectedness
- **Extraction**: Patent cross-citations from USPTO data
- **Range**: [0, 1000]
- **Research**: Hall et al. (2005) - patent citations

**N029: Regulatory Interaction Frequency**
- **Description**: Government engagement intensity
- **Extraction**: Regulatory filings, submissions, interactions disclosed
- **Range**: [0, 100]
- **Research**: Correia (2014) - regulatory relationships

**N030: Media Mention Network**
- **Description**: Press coverage interconnectedness
- **Extraction**: Co-mentions with other companies in news
- **Range**: [0, 10000]
- **Research**: Fang & Peress (2009) - media coverage

---

## 4. TEMPORAL DIMENSION (30 Signals)

### 4.1 Time Series Patterns (10 signals)

**T001: Filing Delay Duration**
- **Description**: Days from fiscal year-end to filing
- **Extraction**: Filing date - fiscal year end date
- **Range**: [0, 365]
- **Research**: Alford et al. (1994) - reporting lags

**T002: Filing Time of Day**
- **Description**: After-hours filing timing (negative signal)
- **Extraction**: Hour of day (0-23) filing submitted
- **Range**: [0, 23]
- **Research**: deHaan et al. (2015) - strategic disclosure timing

**T003: Amendment Frequency**
- **Description**: Filing restatement rate
- **Extraction**: 10-K/A amendments filed
- **Range**: [0, 10]
- **Research**: Palmrose & Scholz (2004) - restatements

**T004: Quarterly Momentum Consistency**
- **Description**: 10-Q to 10-K narrative alignment
- **Extraction**: Semantic similarity across quarterly reports
- **Range**: [0, 1]
- **Research**: Brochet et al. (2011) - reporting frequency

**T005: Guidance Revision Frequency**
- **Description**: Management forecast update rate
- **Extraction**: Number of 8-K guidance updates
- **Range**: [0, 20]
- **Research**: Hirst et al. (2008) - forecast revisions

**T006: Dividend Announcement Timing**
- **Description**: Dividend decision predictability
- **Extraction**: Days since prior dividend announcement
- **Range**: [0, 365]
- **Research**: Brav et al. (2005) - payout decisions

**T007: Conference Call Timing Delta**
- **Description**: Days between earnings release and call
- **Extraction**: Call date - earnings release date
- **Range**: [0, 30]
- **Research**: Frankel et al. (1999) - conference calls

**T008: Material Event Clustering**
- **Description**: 8-K filing concentration
- **Extraction**: 8-K filings per quarter
- **Range**: [0, 50]
- **Research**: Lerman & Livnat (2010) - 8-K informativeness

**T009: Seasonality Consistency**
- **Description**: Quarterly pattern stability
- **Extraction**: Coefficient of variation in quarterly metrics
- **Range**: [0, 2]
- **Research**: Barth et al. (1999) - quarterly patterns

**T010: Year-End Management**
- **Description**: Q4 earnings management indicator
- **Extraction**: Q4 accruals / Q1-Q3 average accruals
- **Range**: [0, 5]
- **Research**: Jacob & Jorgensen (2007) - timing strategies

### 4.2 Trend Evolution (10 signals)

**T011: Revenue Growth Acceleration**
- **Description**: Second derivative of revenue trend
- **Extraction**: YoY growth rate change
- **Range**: [-100, 100]
- **Research**: Chan et al. (2003) - revenue momentum

**T012: Margin Trajectory**
- **Description**: Operating margin trend strength
- **Extraction**: 3-year margin linear regression slope
- **Range**: [-50, 50]
- **Research**: Fairfield & Yohn (2001) - margin analysis

**T013: Capex Cycle Phase**
- **Description**: Capital expenditure cyclicality
- **Extraction**: Capex/Depreciation ratio trend
- **Range**: [0, 5]
- **Research**: Titman et al. (2004) - investment cycles

**T014: Working Capital Efficiency**
- **Description**: Cash conversion cycle trend
- **Extraction**: Days sales outstanding + inventory days - payables days
- **Range**: [-100, 500]
- **Research**: Kieschnick et al. (2013) - working capital

**T015: Debt Maturity Profile Evolution**
- **Description**: Debt refinancing pressure trend
- **Extraction**: Current debt / total debt ratio trend
- **Range**: [0, 1]
- **Research**: Barclay & Smith (1995) - debt maturity

**T016: R&D Intensity Trajectory**
- **Description**: Innovation investment trend
- **Extraction**: R&D / revenue 3-year slope
- **Range**: [-20, 20]
- **Research**: Eberhart et al. (2004) - R&D momentum

**T017: SG&A Leverage Pattern**
- **Description**: Operating leverage evolution
- **Extraction**: SG&A growth vs. revenue growth
- **Range**: [-50, 50]
- **Research**: Anderson et al. (2003) - cost stickiness

**T018: Tax Rate Drift**
- **Description**: Effective tax rate stability
- **Extraction**: ETR 5-year moving standard deviation
- **Range**: [0, 30]
- **Research**: Dyreng et al. (2008) - tax avoidance

**T019: Goodwill Accumulation Rate**
- **Description**: M&A premium buildup
- **Extraction**: Goodwill / total assets trend
- **Range**: [0, 1]
- **Research**: Hayn & Hughes (2006) - goodwill

**T020: Share Repurchase Momentum**
- **Description**: Buyback program consistency
- **Extraction**: Shares repurchased 4-quarter moving average
- **Range**: [0, 50]%
- **Research**: Ikenberry et al. (1995) - repurchases

### 4.3 Cyclical Behaviors (10 signals)

**T021: Industry Cycle Correlation**
- **Description**: Synchronization with sector peers
- **Extraction**: Revenue correlation with industry index
- **Range**: [-1, 1]
- **Research**: Moskowitz & Grinblatt (1999) - industry momentum

**T022: Economic Sensitivity Beta**
- **Description**: GDP correlation strength
- **Extraction**: Revenue vs. GDP beta coefficient
- **Range**: [-2, 3]
- **Research**: Berk et al. (1999) - cyclicality

**T023: Inventory Build/Liquidation Cycle**
- **Description**: Inventory management patterns
- **Extraction**: Inventory days trend direction
- **Range**: [-100, 100]
- **Research**: Rajgopal et al. (2003) - inventory signals

**T024: Hiring/Firing Cycle**
- **Description**: Employment volatility
- **Extraction**: Employee count % change
- **Range**: [-30, 50]
- **Research**: Bazdresch et al. (2018) - labor hiring

**T025: Geographic Revenue Rotation**
- **Description**: Regional mix evolution
- **Extraction**: Entropy of geographic revenue distribution
- **Range**: [0, 5]
- **Research**: Hann et al. (2013) - geographic diversity

**T026: Product Line Evolution**
- **Description**: Product mix shift velocity
- **Extraction**: Change in segment revenue mix
- **Range**: [0, 1]
- **Research**: Ali et al. (2004) - segment changes

**T027: Pricing Power Trajectory**
- **Description**: Price vs. volume growth contribution
- **Extraction**: Price effect / volume effect ratio
- **Range**: [-5, 5]
- **Research**: Callen et al. (2005) - pricing signals

**T028: Customer Acquisition Rate**
- **Description**: Customer base growth
- **Extraction**: New customer count / total customers
- **Range**: [0, 1]
- **Research**: Gupta et al. (2004) - customer metrics

**T029: Regulatory Cycle Alignment**
- **Description**: Regulatory environment phase
- **Extraction**: Regulatory mentions vs. industry average
- **Range**: [-5, 5]
- **Research**: Kang et al. (2017) - regulatory cycles

**T030: Litigation Wave Exposure**
- **Description**: Legal proceeding clustering
- **Extraction**: Active lawsuits vs. 5-year average
- **Range**: [-5, 10]
- **Research**: Pritchard & Sale (2005) - litigation waves

---

## 5. VISUAL DIMENSION (20 Signals)

### 5.1 Chart & Graph Analysis (10 signals)

**V001: Chart Quantity Index**
- **Description**: Visual data presentation frequency
- **Extraction**: Number of embedded charts/graphs
- **Range**: [0, 50]
- **Research**: Beattie & Jones (2001) - graphical disclosure

**V002: Chart Type Diversity**
- **Description**: Visualization technique variety
- **Extraction**: Distinct chart types (line, bar, pie, scatter, etc.)
- **Range**: [0, 10]
- **Research**: Penrose (2008) - visual rhetoric

**V003: Time Series Visualization Depth**
- **Description**: Historical data presentation span
- **Extraction**: Years of data shown in charts
- **Range**: [1, 20]
- **Research**: Beattie & Jones (2000) - impression management

**V004: Dual-Axis Chart Usage**
- **Description**: Complex comparison visualization
- **Extraction**: Charts with multiple Y-axes
- **Range**: [0, 20]
- **Research**: Few (2008) - data visualization

**V005: Chart Title Sentiment**
- **Description**: Visual framing bias
- **Extraction**: Sentiment analysis of chart titles
- **Range**: [-1, 1]
- **Research**: Hill & Milner (2003) - graphical manipulation

**V006: Y-Axis Truncation Frequency**
- **Description**: Scale manipulation indicator
- **Extraction**: Charts with non-zero baseline
- **Range**: [0, 20]
- **Research**: Beattie & Jones (2002) - distortion

**V007: Color Saturation Intensity**
- **Description**: Visual emphasis through color
- **Extraction**: Color palette complexity (HTML filings)
- **Range**: [0, 50]
- **Research**: Courtis (2004) - color usage

**V008: Interactive Element Count**
- **Description**: Digital engagement features (modern filings)
- **Extraction**: Interactive charts, drill-downs in HTML
- **Range**: [0, 30]
- **Research**: XBRL Inline (2019) - interactivity

**V009: Infographic Sophistication**
- **Description**: Complex visual storytelling
- **Extraction**: Multi-element visual explanations
- **Range**: [0, 20]
- **Research**: Davison (2015) - corporate reporting visuals

**V010: Logo/Branding Prominence**
- **Description**: Corporate branding in financial disclosure
- **Extraction**: Non-required brand imagery count
- **Range**: [0, 50]
- **Research**: Guillamon-Saorin et al. (2017) - impression management

### 5.2 Table & Data Presentation (10 signals)

**V011: Table Density Score**
- **Description**: Tabular data volume
- **Extraction**: Number of tables in filing
- **Range**: [0, 200]
- **Research**: Dyer et al. (2017) - table usage

**V012: Cell-Level Complexity**
- **Description**: Table granularity
- **Extraction**: Average cells per table
- **Range**: [0, 500]
- **Research**: Beattie & Jones (2001) - table design

**V013: Column Count Evolution**
- **Description**: Table width trend
- **Extraction**: Average columns per table YoY change
- **Range**: [-10, 20]
- **Research**: Li (2008) - table complexity

**V014: Row Grouping Sophistication**
- **Description**: Hierarchical data presentation
- **Extraction**: Multi-level row headers per table
- **Range**: [0, 10]
- **Research**: Debreceny et al. (2011) - structured data

**V015: Color-Coding Frequency**
- **Description**: Visual categorization in tables
- **Extraction**: Colored cells/rows in HTML tables
- **Range**: [0, 100]
- **Research**: Amer (2005) - table design

**V016: Footnote Marker Density**
- **Description**: Table annotation intensity
- **Extraction**: Footnote references per table
- **Range**: [0, 50]
- **Research**: Maines & McDaniel (2000) - footnotes

**V017: Variance Column Inclusion**
- **Description**: Change analysis presentation
- **Extraction**: "Change" or "Δ" columns in tables
- **Range**: [0, 30]
- **Research**: Hales et al. (2011) - variance reporting

**V018: Percentage vs. Absolute Mix**
- **Description**: Numeric presentation format balance
- **Extraction**: % values / absolute values ratio in tables
- **Range**: [0, 5]
- **Research**: Clor-Proell et al. (2015) - number formats

**V019: Table Caption Length**
- **Description**: Table explanatory text depth
- **Extraction**: Average words in table captions
- **Range**: [0, 100]
- **Research**: Beattie & Jones (2000) - table titles

**V020: Conditional Formatting Usage**
- **Description**: Dynamic visual highlighting (digital filings)
- **Extraction**: Conditional formats in HTML/XBRL
- **Range**: [0, 50]
- **Research**: Blankespoor et al. (2014) - digital presentation

---

## Signal Extraction Pipeline

### Phase 1: Document Ingestion
```python
# Parse SEC filing (10-K, 10-Q, 8-K)
# Extract sections using regex/ML classifier
# Generate section embeddings (BERT-base-financial)
# Store in vector database for similarity searches
```

### Phase 2: Linguistic Processing
```python
# Tokenization (spaCy + custom financial terms)
# POS tagging, dependency parsing
# Named entity recognition (FinNER)
# Sentiment analysis (FinBERT)
# Semantic similarity (sentence-transformers)
```

### Phase 3: Structural Analysis
```python
# HTML/XBRL parsing
# Section length calculation
# Cross-reference mapping
# Table/chart extraction
# Formatting feature extraction
```

### Phase 4: Network Construction
```python
# Entity extraction (officers, directors, subsidiaries)
# Relationship mapping (board interlocks, auditors)
# Graph database storage (Neo4j)
# Centrality metrics calculation
```

### Phase 5: Time Series Generation
```python
# Historical filing retrieval
# Metric calculation over time
# Trend analysis (linear/polynomial regression)
# Cycle detection (Fourier analysis)
```

### Phase 6: Visual Processing
```python
# Image extraction from PDF/HTML
# Chart classification (CNN)
# OCR for embedded text in images
# Color/layout analysis
```

---

## Research Foundation

### Key Academic Papers

1. **Loughran & McDonald (2011)** - "When Is a Liability Not a Liability? Textual Analysis, Dictionaries, and 10-Ks"
   - Foundation for financial sentiment analysis
   - Developed domain-specific word lists

2. **Li (2008)** - "Annual Report Readability, Current Earnings, and Earnings Persistence"
   - Established readability-performance links
   - Fog Index application in finance

3. **Hoberg & Phillips (2016)** - "Text-Based Network Industries and Endogenous Product Differentiation"
   - Text-based industry classification
   - Network analysis of product markets

4. **Buehlmaier & Whited (2018)** - "Are Financial Constraints Priced? Evidence from Textual Analysis"
   - Textual measures of financial constraints
   - Predictive power for returns

5. **Dyer et al. (2017)** - "The Evolution of 10-K Textual Disclosure"
   - Longitudinal analysis of filing changes
   - Structural complexity trends

6. **Blankespoor et al. (2014)** - "Fair Value Accounting for Financial Instruments"
   - Visual presentation effects
   - Digital disclosure impact

7. **Fracassi & Tate (2012)** - "External Networking and Internal Firm Governance"
   - Social network effects on governance
   - Board interlock analysis

8. **Cohen et al. (2012)** - "Decoding Inside Information"
   - Insider trading network patterns
   - Predictive signals from Form 4

### Implementation Libraries

- **NLP**: spaCy, transformers (FinBERT), sentence-transformers
- **Finance**: FinNLP, Edgar-Crawler, sec-api
- **Network**: NetworkX, Neo4j, igraph
- **Time Series**: statsmodels, prophet, pmdarima
- **Vision**: OpenCV, pytesseract, Pillow
- **ML**: scikit-learn, XGBoost, PyTorch

---

## Signal Validation Framework

Each signal should be validated against:

1. **Statistical Significance**: Correlation with future returns/events
2. **Predictive Power**: Out-of-sample performance
3. **Robustness**: Consistency across industries/time periods
4. **Interpretability**: Clear economic rationale
5. **Computational Feasibility**: Extraction speed < 10 seconds per filing

---

## Next Steps

1. Implement extraction algorithms for each signal dimension
2. Build signal database schema (PostgreSQL + Vector DB)
3. Create batch processing pipeline for historical filings
4. Develop signal combination/weighting optimization
5. Backtest predictive models using signal features
6. Deploy real-time extraction API
