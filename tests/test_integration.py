
from pathlib import Path
from scanner import scan_python_files
from parser import parse_repository
from search import CodeSearchEngine
from classifier import CodeClassifier
from clustering import CodeClusterer
from dependencies import build_dependency_graph, get_graph_metrics


def test_full_pipeline_on_sample_project():
    root = Path(__file__).parent.parent / "sample_project"

    files = scan_python_files(root)
    assert len(files) >= 6

    parsed_files = parse_repository(root, files)
    assert len(parsed_files) == len(files)

    all_functions = []
    for pf in parsed_files:
        assert pf.error is None
        all_functions.extend(pf.functions)

    assert len(all_functions) >= 15

    searcher = CodeSearchEngine()
    searcher.index(all_functions)

    results = searcher.search("verify password and hash credentials", top_k=3)
    assert len(results) > 0
    assert any("password" in r.entity.name.lower() or "auth" in r.file_path.lower() for r in results)

    classifier = CodeClassifier()
    predictions = [classifier.predict(fn.searchable_text) for fn in all_functions]
    categories_found = {p.category for p in predictions}
    assert len(categories_found) >= 4
    for p in predictions:
        assert 0.0 <= p.confidence <= 1.0

    clusterer = CodeClusterer()
    outcome = clusterer.cluster(all_functions, n_clusters=4)
    assert outcome.effective_k == 4
    assert len(outcome.groups) == 4
    for g in outcome.groups:
        assert len(g.representative_terms) > 0

    graph = build_dependency_graph(parsed_files)
    metrics = get_graph_metrics(graph)
    assert metrics["num_nodes"] >= 6
    assert metrics["num_edges"] >= 4
    depended_files = [f for f, count in metrics["most_depended_on"] if count > 0]
    assert len(depended_files) > 0
