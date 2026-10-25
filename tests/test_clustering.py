
from parser import FunctionEntity
from clustering import CodeClusterer


def make_entity(name, doc, code):
    return FunctionEntity(
        name=name,
        parent_class=None,
        file_path="src.py",
        line_start=1,
        line_end=10,
        docstring=doc,
        source_code=code,
    )


def test_clustering_normal_case():
    entities = [
        make_entity("login", "authenticate jwt password", "def login(): hash_password()"),
        make_entity("logout", "terminate jwt session token", "def logout(): revoke_token()"),
        make_entity("query_db", "sql select query execute", "def query_db(): cursor.execute()"),
        make_entity("insert_db", "insert into sql database table", "def insert_db(): session.commit()"),
    ]

    clusterer = CodeClusterer()
    outcome = clusterer.cluster(entities, n_clusters=2)

    assert outcome.effective_k == 2
    assert len(outcome.groups) == 2
    assert sum(g.size for g in outcome.groups) == 4

    for g in outcome.groups:
        assert len(g.representative_terms) > 0
        assert g.size > 0


def test_clustering_small_dataset_clamping():
    entities = [
        make_entity("alpha", "utility format timestamp", "def alpha(): return time()"),
        make_entity("beta", "utility sanitize string", "def beta(): return clean()"),
    ]

    clusterer = CodeClusterer()
    outcome = clusterer.cluster(entities, n_clusters=5)

    assert outcome.effective_k == 2
    assert outcome.note is not None
    assert "Adjusted cluster count to 2" in outcome.note
    assert len(outcome.groups) == 2


def test_clustering_empty_entities():
    clusterer = CodeClusterer()
    outcome = clusterer.cluster([], n_clusters=3)

    assert outcome.effective_k == 0
    assert len(outcome.groups) == 0
    assert outcome.note is not None
