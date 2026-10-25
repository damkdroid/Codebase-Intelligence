

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from parser import FunctionEntity


@dataclass
class ClusterGroup:
    """Represents a discovered cluster of functions."""
    cluster_id: int
    representative_terms: List[str]
    entities: List[FunctionEntity]

    @property
    def size(self) -> int:
        return len(self.entities)

    @property
    def label(self) -> str:
        terms = ", ".join(self.representative_terms[:3]) if self.representative_terms else "general"
        return f"Cluster {self.cluster_id} [{terms}] ({self.size} functions)"


@dataclass
class ClusteringOutcome:
    """Outcome of running K-means code clustering."""
    groups: List[ClusterGroup]
    requested_k: int
    effective_k: int
    note: Optional[str] = None


class CodeClusterer:
    """Clusters code entities using TF-IDF and K-Means."""

    def __init__(self, max_features: int = 1500):
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
            max_features=max_features,
            token_pattern=r"(?u)\b[a-zA-Z_][a-zA-Z0-9_]+\b",
            sublinear_tf=True,
        )

    def cluster(
        self,
        entities: List[FunctionEntity],
        n_clusters: int = 4,
        top_n_terms: int = 5,
        random_state: int = 42,
    ) -> ClusteringOutcome:
        """Run K-Means clustering on the provided entities.

        Args:
            entities: List of FunctionEntity objects.
            n_clusters: Desired number of clusters.
            top_n_terms: Number of representative vocabulary terms per cluster.
            random_state: Random seed for deterministic reproducibility.

        Returns:
            ClusteringOutcome containing cluster groups and adjustments.
        """
        if not entities:
            return ClusteringOutcome(
                groups=[],
                requested_k=n_clusters,
                effective_k=0,
                note="No functions available to cluster.",
            )

        n_samples = len(entities)
        note = None
        effective_k = n_clusters

        # Adjust k if sample count is smaller than requested clusters
        if n_samples < n_clusters:
            effective_k = max(1, n_samples)
            note = (
                f"Requested {n_clusters} clusters, but only {n_samples} function(s) were found. "
                f"Adjusted cluster count to {effective_k}."
            )

        corpus = [e.searchable_text for e in entities]
        try:
            X = self.vectorizer.fit_transform(corpus)
            feature_names = np.array(self.vectorizer.get_feature_names_out())
        except ValueError:
            # Vocabulary empty (e.g., all empty docstrings and functions)
            return ClusteringOutcome(
                groups=[
                    ClusterGroup(
                        cluster_id=0,
                        representative_terms=["unindexed"],
                        entities=list(entities),
                    )
                ],
                requested_k=n_clusters,
                effective_k=1,
                note="Insufficient text vocabulary to perform meaningful feature extraction.",
            )

        # Handle 1 cluster
        if effective_k == 1:
            mean_vector = np.asarray(X.mean(axis=0)).flatten()
            top_indices = mean_vector.argsort()[::-1][:top_n_terms]
            terms = [str(feature_names[i]) for i in top_indices if mean_vector[i] > 0]
            group = ClusterGroup(
                cluster_id=0,
                representative_terms=terms,
                entities=list(entities),
            )
            return ClusteringOutcome(
                groups=[group],
                requested_k=n_clusters,
                effective_k=1,
                note=note,
            )

        kmeans = KMeans(
            n_clusters=effective_k,
            random_state=random_state,
            n_init="auto",
        )
        labels = kmeans.fit_predict(X)

        # Extract top terms from cluster centers
        cluster_terms: Dict[int, List[str]] = {}
        order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]

        for i in range(effective_k):
            top_indices = order_centroids[i, :top_n_terms]
            cluster_terms[i] = [
                str(feature_names[idx])
                for idx in top_indices
                if idx < len(feature_names)
            ]

        # Group entities
        buckets: Dict[int, List[FunctionEntity]] = {i: [] for i in range(effective_k)}
        for idx, label in enumerate(labels):
            buckets[int(label)].append(entities[idx])

        groups: List[ClusterGroup] = []
        for i in range(effective_k):
            groups.append(
                ClusterGroup(
                    cluster_id=i,
                    representative_terms=cluster_terms.get(i, []),
                    entities=buckets[i],
                )
            )

        # Sort groups by size descending
        groups.sort(key=lambda g: g.size, reverse=True)

        return ClusteringOutcome(
            groups=groups,
            requested_k=n_clusters,
            effective_k=effective_k,
            note=note,
        )
