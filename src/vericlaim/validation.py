"""Leakage-aware validation helpers for visually related claim images."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from sklearn.model_selection import StratifiedGroupKFold

from .features import hamming_distance


class _UnionFind:
    def __init__(self, size: int):
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, item: int) -> int:
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, left: int, right: int) -> None:
        left_root, right_root = self.find(left), self.find(right)
        if left_root == right_root:
            return
        if self.rank[left_root] < self.rank[right_root]:
            left_root, right_root = right_root, left_root
        self.parent[right_root] = left_root
        if self.rank[left_root] == self.rank[right_root]:
            self.rank[left_root] += 1


@dataclass
class _BKNode:
    value: str
    index: int
    children: dict[int, "_BKNode"] = field(default_factory=dict)

    def add(self, value: str, index: int) -> None:
        distance = hamming_distance(value, self.value)
        child = self.children.get(distance)
        if child is None:
            self.children[distance] = _BKNode(value, index)
        else:
            child.add(value, index)

    def query(self, value: str, radius: int) -> list[tuple[int, int]]:
        distance = hamming_distance(value, self.value)
        matches = [(distance, self.index)] if distance <= radius else []
        lower, upper = distance - radius, distance + radius
        for edge, child in self.children.items():
            if lower <= edge <= upper:
                matches.extend(child.query(value, radius))
        return matches


def build_perceptual_groups(hashes: list[str], max_distance: int = 6) -> np.ndarray:
    """Cluster hashes transitively so visually related images stay in one fold."""

    if not hashes:
        return np.asarray([], dtype=np.int32)
    union = _UnionFind(len(hashes))
    representatives: dict[str, int] = {}
    tree: _BKNode | None = None
    for index, value in enumerate(hashes):
        duplicate = representatives.get(value)
        if duplicate is not None:
            union.union(index, duplicate)
            continue
        if tree is None:
            tree = _BKNode(value, index)
        else:
            for _, neighbor in tree.query(value, max_distance):
                union.union(index, neighbor)
            tree.add(value, index)
        representatives[value] = index

    roots = [union.find(index) for index in range(len(hashes))]
    compact = {root: group for group, root in enumerate(dict.fromkeys(roots))}
    return np.asarray([compact[root] for root in roots], dtype=np.int32)


def grouped_holdout_indices(
    labels: np.ndarray,
    groups: np.ndarray,
    folds: int = 5,
    random_state: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    """Return one reproducible stratified holdout with no group overlap."""

    splitter = StratifiedGroupKFold(n_splits=folds, shuffle=True, random_state=random_state)
    fit, validation = next(splitter.split(np.zeros(len(labels)), labels, groups))
    if set(groups[fit]) & set(groups[validation]):
        raise RuntimeError("Perceptual groups crossed the validation boundary")
    return fit, validation


def perceptual_overlap_audit(
    train_hashes: list[str],
    train_labels: np.ndarray,
    test_hashes: list[str],
    test_labels: np.ndarray,
    max_distance: int = 6,
) -> dict[str, object]:
    """Screen the supplied test split for close training-image fingerprints."""

    if not train_hashes:
        return {
            "hash": "pHash-63",
            "distance_threshold": max_distance,
            "test_images_with_close_train_match": 0,
            "test_images_with_identical_perceptual_hash": 0,
            "close_match_rate": 0.0,
            "cross_label_close_matches": 0,
        }
    tree = _BKNode(train_hashes[0], 0)
    unique = {train_hashes[0]}
    for index, value in enumerate(train_hashes[1:], start=1):
        if value not in unique:
            tree.add(value, index)
            unique.add(value)

    close = exact = conflicts = 0
    distances: list[int] = []
    for test_hash, test_label in zip(test_hashes, test_labels):
        matches = tree.query(test_hash, max_distance)
        if not matches:
            continue
        close += 1
        nearest = min(distance for distance, _ in matches)
        distances.append(nearest)
        exact += int(nearest == 0)
        conflicts += int(any(train_labels[index] != test_label for _, index in matches))
    histogram = {str(distance): distances.count(distance) for distance in sorted(set(distances))}
    return {
        "hash": "pHash-63",
        "distance_threshold": max_distance,
        "test_images_with_close_train_match": close,
        "test_images_with_identical_perceptual_hash": exact,
        "close_match_rate": round(close / max(1, len(test_hashes)), 5),
        "cross_label_close_matches": conflicts,
        "nearest_distance_histogram": histogram,
        "warning": "Perceptual matches are a screening signal and require visual or geometric confirmation.",
    }
