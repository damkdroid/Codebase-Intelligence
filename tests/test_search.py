"""Unit tests for TF-IDF code search engine."""

from parser import FunctionEntity
from search import CodeSearchEngine


def make_entity(name, docstring, code, file_path="module.py", line_start=1):
    return FunctionEntity(
        name=name,
        parent_class=None,
        file_path=file_path,
        line_start=line_start,
        line_end=line_start + 5,
        docstring=docstring,
        source_code=code,
    )


def test_search_ranking():
    e1 = make_entity(
        "verify_password",
        "Verify raw password against hashed string using bcrypt",
        "def verify_password(plain, hashed): return check_hash(plain, hashed)",
        file_path="auth.py",
        line_start=10,
    )
    e2 = make_entity(
        "calculate_tax",
        "Calculate sales tax on total invoice amount",
        "def calculate_tax(amount): return amount * 0.08",
        file_path="billing.py",
        line_start=25,
    )
    e3 = make_entity(
        "connect_db",
        "Initialize connection to postgresql database",
        "def connect_db(): return engine.connect()",
        file_path="db.py",
        line_start=5,
    )

    engine = CodeSearchEngine()
    engine.index([e1, e2, e3])

    # Search for authentication password
    results = engine.search("how to verify user password hash")
    assert len(results) > 0
    top_match = results[0]
    assert top_match.entity.name == "verify_password"
    assert top_match.file_path == "auth.py"
    assert top_match.line_start == 10
    assert top_match.score > 0.1

    # Search for database
    db_results = engine.search("postgresql database connection pool")
    assert len(db_results) > 0
    assert db_results[0].entity.name == "connect_db"


def test_search_empty_queries_and_no_matches():
    engine = CodeSearchEngine()
    e = make_entity("foo", "simple helper", "def foo(): pass")
    engine.index([e])

    # Empty query
    assert engine.search("") == []
    assert engine.search("   ") == []

    # Unrelated query that doesn't match vocabulary
    assert engine.search("supercalifragilisticexpialidocious") == []


def test_search_unindexed_engine():
    engine = CodeSearchEngine()
    assert engine.search("test") == []
