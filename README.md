# Codebase Intelligence

A zero-cloud, static code intelligence and semantic analysis platform for Python repositories. Built with **Python 3.12**, **AST grammar parsing**, **scikit-learn**, **NetworkX**, and **Streamlit**.


---

## Key Capabilities

1. **AST Codebase Scanner and Parser**
   - Recursively discovers Python files while strictly ignoring `.git`, virtual environments (`venv`, `.venv`), bytecode caches (`__pycache__`, `.pytest_cache`), and build folders.
   - Extracts top-level functions, class methods, classes, docstrings, imports, line boundaries, and raw code snippets using Python's standard library `ast`.
   - Safely catches syntax errors and encoding anomalies without halting the scan.
   - **Zero code execution guarantee**: analyzed repository source code is never executed.

2. **Natural-Language Code Search**
   - Semantic vector search across function names, parameter signatures, docstrings, and source code.
   - Powered by `TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)` and cosine similarity.
   - Ranks matches with relevance percentages, file paths, line ranges, and search keyword highlighting.

3. **Architectural Code Classification**
   - Categorizes functions into 6 core architectural categories:
     - `Authentication`
     - `Database Operations`
     - `API/Communication`
     - `Business Logic`
     - `Configuration/Utilities`
     - `Testing`
   - Supervised multiclass Logistic Regression model trained on `training_data.json`.
   - Displays predicted roles, calibrated confidence scores, and probability distributions.

4. **Code Topic Discovery and Clustering**
   - Unsupervised K-Means clustering discovering functional subsystems without manual tags.
   - Interactive cluster count ($k$) with automated small-dataset safeguards.
   - Extracts top representative vocabulary terms directly from centroid coordinates.

5. **Internal Dependency Graph**
   - Constructs a directed graph of internal file-level imports using **NetworkX**.
   - Resolves both absolute and relative imports.
   - Computes in-degree (core utilities), out-degree (high consumers), and circular dependency cycle detection.
   - Theme-aware NetworkX visualization adapting to active Light or Dark theme.

---

## Project Structure

```
.
├── app.py                  # Streamlit dashboard application
├── ui_theme.py             # Centralized design system, Pygments highlighting, and themes
├── scanner.py              # Recursive file traversal with exclusions
├── parser.py               # AST visitor extracting functions, classes, and imports
├── search.py               # TF-IDF + Cosine similarity search engine
├── classifier.py           # TF-IDF + Logistic Regression classification model
├── clustering.py           # TF-IDF + K-Means topic grouping
├── dependencies.py         # NetworkX directed graph builder and import resolver
├── training_data.json      # Labeled training dataset (6 categories)
├── requirements.txt        # Core dependencies
├── README.md               # Quickstart guide & documentation
├── LEARNING_GUIDE.md       # In-depth architectural & interview guide
├── sample_project/         # Sample multi-module Python codebase
│   ├── __init__.py
│   ├── config.py           # Configuration / Utilities
│   ├── database.py         # Database Operations
│   ├── auth.py             # Authentication
│   ├── billing.py          # Business Logic
│   ├── api.py              # API / Communication
│   └── tests/              # Testing
│       ├── test_auth.py
│       └── test_billing.py
└── tests/                  # Unit and integration test suite (23 tests)
    ├── test_scanner.py
    ├── test_parser.py
    ├── test_search.py
    ├── test_classifier.py
    ├── test_clustering.py
    ├── test_dependencies.py
    └── test_integration.py
```

---

## Quickstart & Installation

### 1. Requirements
- Python 3.11 or higher (Tested on Python 3.12)
- PowerShell, Bash, or Command Prompt

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the Dashboard
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

- To launch directly in Light mode: [http://localhost:8501/?theme=light](http://localhost:8501/?theme=light)
- To launch directly in Dark mode: [http://localhost:8501/?theme=dark](http://localhost:8501/?theme=dark)
- Toggle themes at any time using the **Theme** selector in the sidebar.

---

## Running Tests

Run the complete test suite (23 tests across unit, integration, and sample project tests):

```bash
# Run all tests
python -m pytest -v

# Run engine tests only
python -m pytest tests/ -v

# Run sample project tests only
python -m pytest sample_project/tests/ -v
```

---

## Exploring the Sample Codebase

1. In the sidebar, click **Load Sample** (or enter the path to `sample_project/`) and click **Scan Repository**.
2. **Overview**: View metrics for lines of code, functions, classes, and file breakdown.
3. **Code Search**: Try quick query buttons (e.g., *"Password verification"* or *"Database query execution"*) to inspect ranked results with Pygments syntax highlighting and line numbers.
4. **Classification**: Filter by architectural role (e.g., `Authentication` or `Business Logic`) to see predicted tags and full probability distributions.
5. **Clustering**: Adjust the cluster count ($k$) to discover semantic functional groupings and representative keywords.
6. **Dependency Graph**: Inspect internal import coupling, in-degree/out-degree rankings, and verify that circular import count is zero.

---

## Limitations & Design Boundaries

1. **Static AST vs. Dynamic Imports**:
   - Python `ast` parses code statically. Dynamic imports like `importlib.import_module("foo." + var)` or `__import__(name)` cannot be determined without runtime execution. By design, runtime code execution is avoided for security.
2. **Compact Classifier Training Data**:
   - `training_data.json` contains a baseline set of representative snippets across 6 categories. While accurate for standard web and API patterns, specialized or domain-specific codebases will benefit from supplemental fine-tuning data.
3. **Lexical vs. Dense Vector Embeddings**:
   - TF-IDF uses n-gram token overlap. Synonyms not present in the vocabulary will score lower than dense neural embeddings (like BERT/OpenAI). However, TF-IDF runs in milliseconds, requires zero external APIs, and incurs zero infrastructure costs.
