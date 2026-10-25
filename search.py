
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from parser import FunctionEntity


@dataclass
class SearchResult:
    """Represents a ranked match for a search query."""
    entity: FunctionEntity
    score: float
    rank: int

    @property
    def file_path(self) -> str:
        return self.entity.file_path

    @property
    def line_start(self) -> int:
        return self.entity.line_start

    @property
    def line_end(self) -> int:
        return self.entity.line_end

    @property
    def full_name(self) -> str:
        return self.entity.full_name

    @property
    def docstring(self) -> str:
        return self.entity.docstring

    @property
    def source_code(self) -> str:
        return self.entity.source_code


class CodeSearchEngine:
    """TF-IDF and Cosine Similarity vector search engine for code entities."""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
            token_pattern=r"(?u)\b[a-zA-Z_][a-zA-Z0-9_]+\b",
            sublinear_tf=True,
        )
        self.entities: List[FunctionEntity] = []
        self.tfidf_matrix = None
        self.is_indexed: bool = False

    def index(self, entities: List[FunctionEntity]) -> None:
        """Build TF-IDF matrix from code entities."""
        self.entities = entities
        if not entities:
            self.tfidf_matrix = None
            self.is_indexed = False
            return

        corpus = [entity.searchable_text for entity in entities]
        # Ensure at least some non-empty text exists
        non_empty = [c for c in corpus if c.strip()]
        if not non_empty:
            self.tfidf_matrix = None
            self.is_indexed = False
            return

        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        self.is_indexed = True

    def search(
        self, query: str, top_k: int = 10, min_score: float = 0.001
    ) -> List[SearchResult]:
        """Search indexed code entities using natural language query.

        Args:
            query: User's search text.
            top_k: Maximum number of matches to return.
            min_score: Minimum cosine similarity score threshold (default 0.001).

        Returns:
            Ranked list of SearchResult objects sorted by score descending.
        """
        if not self.is_indexed or not query.strip() or self.tfidf_matrix is None:
            return []

        try:
            query_vec = self.vectorizer.transform([query])
        except Exception:
            return []

        # If query vector has zero magnitude (none of the tokens match vocab)
        if query_vec.nnz == 0:
            return []

        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        # Sort indices by score descending
        sorted_indices = np.argsort(similarities)[::-1]

        results: List[SearchResult] = []
        rank = 1
        for idx in sorted_indices:
            score = float(similarities[idx])
            if score < min_score:
                break
            results.append(
                SearchResult(
                    entity=self.entities[idx],
                    score=round(score, 4),
                    rank=rank,
                )
            )
            rank += 1
            if len(results) >= top_k:
                break

        return results
