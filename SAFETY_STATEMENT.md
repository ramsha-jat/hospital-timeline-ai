Safety and Data Statement
Intended Use
Exploring structured hospital data for research and education
Reconstructing patient timelines from relational tables
Answering verifiable questions about structured clinical data
Validating data quality and detecting leakage in research splits
Teaching healthcare data analysis methods
Prohibited Use
❌ Diagnosis of any condition
❌ Treatment recommendations
❌ Triage decisions
❌ Emergency guidance
❌ Clinical decision support
❌ Claims of clinical effectiveness, safety, or generalizability
❌ Claims of improved patient outcomes
❌ Re-identification of deidentified patients
❌ Deployment in any clinical setting
Data Lineage
Source: MIMIC-IV Clinical Database Demo v2.2
DOI: https://doi.org/10.13026/dp1f-ex47
Coverage: 100 patients, one tertiary academic medical center, Boston, USA
Deidentification: All dates are shifted per patient; real chronology must not be inferred
No free-text notes: MIMIC-IV-Note is NOT used
Transformation log: All data transformations logged and reversible
No external patient-level data added
Pretrained model: None required (rule-based). Gemini optional fallback.
Synthetic data: None used
Privacy Handling
Data stored in MongoDB Atlas with encrypted connection
No patient-level rows sent to external LLM services
Only schema descriptions sent to Gemini (when used)
PhysioNet license and attribution followed
Date shifting preserved — no attempt to infer real dates
API keys stored in .env, never committed to git
Failure Modes
Failure Mode	System Behavior	Human Review Required?
Unrecognized question	Suggests available topics	No
Zero supporting rows	Abstains (verification gate)	Yes — consider rephrasing
Invalid hadm_id	Returns 404 error	No
Out-of-scope question	Refuses + explains	Yes
Temporal anomaly in data	Flagged in quality report	Yes — investigate source
MongoDB connection lost	Returns degraded status	Yes — check connection
Rate limit (if Gemini used)	Falls back to rule-based	No — graceful degradation
Human Review Boundary
Before any research conclusion is drawn
When the system abstains — user must decide if question was poorly formed
When quality checks flag issues — user must investigate
Before publishing any finding from this 100-patient sample
System NEVER takes automated clinical action
Subgroup Composition
Group	Count	Note
Male	~56	100 patients cannot support
Female	~44	reliable fairness conclusions
Age range	25-90	Reported for transparency only
Required Notice
Research and educational prototype only. Not for clinical use. Do not use for diagnosis, treatment, triage, or emergency decisionsDtriage, or emergency decisions.

