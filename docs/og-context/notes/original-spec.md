# `311-nlp` — NYC 311 Complaint Intelligence

> Archived planning note: this spec preserves the original `v0.1` product
> framing. For the active release framing, use the main docs for the upcoming
> `0.2.0a1` alpha.

## Resume variants: 🏛️ Civic (primary), 🧠 Frontier (secondary), 📊 Econ (secondary)

---

## One-liner

NLP pipeline that turns NYC's 30M+ 311 service request records into structured
intelligence — extracting complaint themes, detecting emerging neighborhood
issues before they escalate, and mapping the gap between what residents report
and what agencies address.

---

## Why this matters to real users

NYC 311 is the largest municipal service request system in the US. Since 2003
it's logged tens of millions of complaints: noise, heat/hot water outages,
rodents, illegal parking, broken streetlights, building conditions, and hundreds
of other categories. The data is public and enormous.

But the raw data has two problems. First, the _complaint type_ taxonomy is
agency-defined and coarse — "Noise - Residential" doesn't tell you if it's
construction, a party, or an alarm. The actual detail is in free-text
description fields that nobody analyzes at scale. Second, 311 data is mostly
used reactively (respond to individual complaints) rather than proactively (what
neighborhoods are developing new problems?).

`311-nlp` applies NLP to the free-text fields to extract structured intelligence
that doesn't exist in the categorical data alone.

**Who would actually use this:**

- City Council members understanding their district's complaints at a granular
  level
- Agency heads (DOB, HPD, DEP, DSNY) identifying emerging patterns in their
  complaint types
- Journalists investigating neighborhood quality-of-life trends
- Urban researchers studying 311 as a proxy for neighborhood conditions
- Community boards preparing testimony with data backing
- OTI / MODA (analytics arm) looking for NLP approaches to unstructured city
  data

---

## What the end product looks like

### Core library (`nyc311`)

1. **Data loader:** Pulls from the Socrata API for the 311 dataset (the single
   largest dataset on NYC Open Data). Handles pagination, date filtering,
   spatial filtering (by borough, community district, council district, or
   bounding box). Caches locally.

2. **NLP pipeline:**
   - **Topic extraction:** Cluster the free-text `descriptor` and
     `resolution_description` fields into fine-grained topics within each
     complaint type. Example: within "Noise - Residential," distinguish
     construction noise, party noise, barking dogs, mechanical noise.
   - **Severity/urgency signals:** Classify language indicating severity
     ("emergency," "dangerous," "children present," "elderly") — produces a
     derived urgency score not present in the raw data.
   - **Temporal anomaly detection:** For each complaint topic × geography
     combination, fit a baseline trend and flag statistically significant
     spikes. "Rodent complaints in Bushwick jumped 3σ above baseline this
     month."
   - **Resolution gap analysis:** Compare complaint volume to resolution rates
     and times by topic × geography. Where are complaints piling up unresolved?

3. **Spatial outputs:**
   - GeoJSON of complaint density by topic at census tract / community district
     level
   - Time-series CSV of topic trends by geography
   - Anomaly alerts: list of (topic, geography, time period) tuples with
     significance scores

4. **CLI:** `nyc311 topics --borough brooklyn --since 2025-01-01 --top 20` or
   `nyc311 anomalies --district 301 --window 30d`

### Example notebook

Analyze one community district's complaints over a year. Show: top fine-grained
topics (not just the coarse 311 categories), temporal trends, anomalies
detected, resolution gap analysis. Produce a "neighborhood report card" that a
community board member could actually present at a meeting.

---

## Key technical decisions

**Topic modeling approach:** Start with TF-IDF + UMAP + HDBSCAN for unsupervised
topic clustering on the free-text fields. This is fast, interpretable, and
doesn't require GPU. For the stretch version, use sentence-transformers
embeddings for better semantic grouping. Don't use LDA — it produces less
coherent topics on short texts like 311 descriptors.

**Anomaly detection:** Use simple z-score on rolling window counts per (topic,
geography). More sophisticated: STL decomposition to separate
trend/seasonal/residual, then flag residual spikes. This connects directly to
your ASTECH project (spatiotemporal anomaly detection).

**Text is short and messy.** 311 descriptors are often just a few words or a
short sentence, frequently misspelled, sometimes in Spanish or other languages.
The NLP pipeline needs to handle this gracefully — lowercasing, basic
normalization, but not heavy preprocessing that destroys signal.

**Lean dependencies.** Core: `pandas`, `scikit-learn`, `hdbscan`, `umap-learn`,
`geopandas`. Optional: `sentence-transformers` for embedding-based topics. No
LLM required for the core pipeline — this is classical NLP done well, which is
actually more impressive for frontier lab applications than "I called GPT-4."

**Reproducibility.** Pin the random seeds, document the clustering parameters,
version the topic model outputs. Someone should be able to re-run your pipeline
on the same data and get the same topics.

---

## MVP scope (weekend 1)

- [ ] 311 data loader via Socrata API with date/borough filtering
- [ ] TF-IDF + HDBSCAN topic clustering on `descriptor` field within top 5
      complaint types
- [ ] Tract-level complaint density GeoJSON
- [ ] Basic temporal trend visualization (matplotlib)
- [ ] Notebook walking through one community district
- [ ] README with methodology, example output, data source

## Stretch scope (weekend 2+)

- [ ] Embedding-based topic modeling (sentence-transformers)
- [ ] Temporal anomaly detection with z-score flagging
- [ ] Resolution gap analysis (time-to-close by topic × geography)
- [ ] Severity/urgency classifier on free text
- [ ] CLI tool
- [ ] Interactive Folium/deck.gl map
- [ ] "Neighborhood report card" generator (Markdown template)
- [ ] ASTECH integration: use your spatiotemporal convex hull library on 311
      anomaly clusters
- [ ] Spanish-language complaint handling

---

## README must communicate

1. **The problem:** 311 data is massive but the interesting signal is locked in
   free-text fields nobody analyzes at scale
2. **What you get that the raw data doesn't give you:** fine-grained topics,
   anomaly detection, resolution gaps
3. **Example output:** the neighborhood report card for a real community
   district
4. **A map:** complaint topic density or anomaly map for a borough
5. **Methodology:** be explicit about the NLP approach — this is what labs and
   data science teams will evaluate

---

## What this proves on your resume

- You can apply NLP to messy, real-world government text data — not clean
  academic corpora
- You combine text analysis with spatial and temporal analysis — rare skill
  intersection
- You can connect to your ASTECH library for spatiotemporal anomaly detection
  (portfolio coherence)
- You think about what makes analysis _useful to decision-makers_, not just
  technically interesting
- The classical ML approach (TF-IDF, HDBSCAN) shows depth beyond "I used an LLM
  for everything"
