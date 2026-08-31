"""Transformation-resistant Evidence DNA for cross-claim reuse screening.

This module is deliberately independent of the fraud classifier. A match means
"review the claim linkage", not "the customer committed fraud".
"""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass
from typing import BinaryIO, Iterable

import numpy as np
from PIL import Image, ImageOps
from scipy.fft import dctn


DNA_VERSION = "evidence-dna-v1"
PHASH_BITS = 63
DHASH_BITS = 64


def _open(source: bytes | BinaryIO) -> tuple[Image.Image, bytes]:
    raw = source if isinstance(source, bytes) else source.read()
    if not isinstance(source, bytes):
        source.seek(0)
    image = Image.open(io.BytesIO(raw))
    image.load()
    return ImageOps.exif_transpose(image).convert("RGB"), raw


def _phash(image: Image.Image) -> str:
    gray = np.asarray(image.convert("L").resize((32, 32), Image.Resampling.LANCZOS), dtype=np.float32)
    coeff = dctn(gray, norm="ortho")[:8, :8].flatten()[1:]
    bits = coeff > np.median(coeff)
    value = 0
    for bit in bits:
        value = (value << 1) | int(bit)
    return f"{value:016x}"


def _dhash(image: Image.Image) -> str:
    gray = np.asarray(image.convert("L").resize((9, 8), Image.Resampling.LANCZOS), dtype=np.int16)
    bits = gray[:, 1:] > gray[:, :-1]
    value = 0
    for bit in bits.flat:
        value = (value << 1) | int(bit)
    return f"{value:016x}"


def _signature(image: Image.Image) -> str:
    return f"{_phash(image)}:{_dhash(image)}"


def _descriptor(image: Image.Image) -> list[float]:
    """Compact crop-tolerant colour/edge distribution descriptor."""
    resized = np.asarray(image.convert("RGB").resize((96, 96), Image.Resampling.BILINEAR), dtype=np.uint8)
    hsv = np.asarray(Image.fromarray(resized).convert("HSV"), dtype=np.float32)
    values: list[float] = []
    for channel, bins in ((0, 12), (1, 8), (2, 8)):
        hist, _ = np.histogram(hsv[:, :, channel], bins=bins, range=(0, 256))
        values.extend((hist / max(1, hist.sum())).tolist())
    gray = np.asarray(Image.fromarray(resized).convert("L"), dtype=np.float32)
    gy, gx = np.gradient(gray)
    magnitude = np.sqrt(gx * gx + gy * gy)
    orientation = (np.arctan2(gy, gx) + np.pi) % np.pi
    indices = np.minimum((orientation / np.pi * 8).astype(int), 7)
    edge_hist = np.bincount(indices.ravel(), weights=magnitude.ravel(), minlength=8)
    values.extend((edge_hist / max(1e-6, edge_hist.sum())).tolist())
    vector = np.asarray(values, dtype=np.float32)
    vector /= np.linalg.norm(vector) + 1e-6
    return np.round(vector, 5).tolist()


def _information_score(image: Image.Image) -> float:
    gray = np.asarray(image.convert("L").resize((64, 64), Image.Resampling.BILINEAR), dtype=np.float32)
    return float(gray.std() + np.abs(np.gradient(gray)[0]).mean())


def _variants(image: Image.Image, include_arbitrary_rotations: bool = False) -> Iterable[Image.Image]:
    base = ImageOps.contain(image, (512, 512), Image.Resampling.LANCZOS)
    variants = [
        base,
        ImageOps.mirror(base),
        ImageOps.flip(base),
        base.rotate(90, expand=True),
        base.rotate(180, expand=True),
        base.rotate(270, expand=True),
    ]
    if include_arbitrary_rotations:
        variants.extend(base.rotate(angle, expand=False, fillcolor=(0, 0, 0)) for angle in (-45, -30, -15, 15, 30, 45))
    for variant in variants:
        yield variant
        yield ImageOps.invert(variant)


def _patches(image: Image.Image) -> Iterable[Image.Image]:
    """Yield overlapping regions so a submitted crop can match a prior image."""
    width, height = image.size
    for scale in (0.30, 0.40, 0.50, 0.60, 0.75):
        patch_w, patch_h = max(48, int(width * scale)), max(48, int(height * scale))
        x_positions = sorted(set(int((width - patch_w) * step / 6) for step in range(7)))
        y_positions = sorted(set(int((height - patch_h) * step / 6) for step in range(7)))
        for top in y_positions:
            for left in x_positions:
                patch = image.crop((left, top, left + patch_w, top + patch_h))
                if _information_score(patch) >= 12.0:
                    yield patch


def build_evidence_dna(source: bytes | BinaryIO) -> dict:
    image, raw = _open(source)
    whole_variants = list(_variants(image, include_arbitrary_rotations=True))
    whole = sorted({_signature(item) for item in whole_variants})
    whole_descriptors = [_descriptor(item) for item in whole_variants]
    patch_hashes: set[str] = set()
    patch_descriptors: list[list[float]] = []
    for patch in _patches(image):
        # Whole-image variants are compared against these dense local regions,
        # so storing one orientation per patch avoids a large redundant index.
        patch_hashes.add(_signature(patch))
        patch_descriptors.append(_descriptor(patch))
    return {
        "version": DNA_VERSION,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "width": image.width,
        "height": image.height,
        "whole": whole,
        "patches": sorted(patch_hashes),
        "whole_descriptors": whole_descriptors,
        "patch_descriptors": patch_descriptors,
    }


def _distance(left: str, right: str) -> tuple[int, int]:
    lp, ld = left.split(":", 1)
    rp, rd = right.split(":", 1)
    return (int(lp, 16) ^ int(rp, 16)).bit_count(), (int(ld, 16) ^ int(rd, 16)).bit_count()


def _similarity(left: str, right: str) -> float:
    pdistance, ddistance = _distance(left, right)
    return float(np.clip(1.0 - 0.72 * pdistance / PHASH_BITS - 0.28 * ddistance / DHASH_BITS, 0, 1))


def _best(left: list[str], right: list[str]) -> float:
    if not left or not right:
        return 0.0
    return max(_similarity(a, b) for a in left for b in right)


def _best_descriptor(left: list[list[float]], right: list[list[float]]) -> float:
    if not left or not right:
        return 0.0
    left_matrix = np.asarray(left, dtype=np.float32)
    right_matrix = np.asarray(right, dtype=np.float32)
    return float(np.max(left_matrix @ right_matrix.T))


@dataclass(frozen=True)
class EvidenceMatch:
    similarity: float
    match_type: str
    reason: str


def compare_evidence_dna(query: dict, reference: dict) -> EvidenceMatch:
    if query.get("sha256") and query.get("sha256") == reference.get("sha256"):
        return EvidenceMatch(1.0, "exact", "Exact previously submitted file")

    query_whole = list(query.get("whole", []))
    reference_whole = list(reference.get("whole", []))
    query_patches = list(query.get("patches", []))
    reference_patches = list(reference.get("patches", []))
    whole = _best(query_whole, reference_whole)
    segment = max(
        _best(query_whole, reference_patches),
        _best(query_patches, reference_whole),
    )
    descriptor_segment = max(
        _best_descriptor(list(query.get("whole_descriptors", [])), list(reference.get("patch_descriptors", []))),
        _best_descriptor(list(query.get("patch_descriptors", [])), list(reference.get("whole_descriptors", []))),
    )
    if whole >= 0.91:
        return EvidenceMatch(whole, "transformed", "Same scene after rotation, mirroring, inversion, resizing or editing")
    if segment >= 0.925 or descriptor_segment >= 0.97:
        combined = max(segment, descriptor_segment)
        return EvidenceMatch(combined, "partial", "Cropped or partial region resembles previously submitted evidence")
    return EvidenceMatch(max(whole, segment, descriptor_segment), "none", "No strong historical reuse match")


def find_historical_matches(query_images: list[dict], cases: list[dict], limit: int = 5) -> list[dict]:
    matches: list[dict] = []
    for image_index, query in enumerate(query_images):
        dna = query.get("evidence_dna", {})
        if not dna:
            continue
        for case in cases:
            for evidence in case.get("evidence_manifest", []):
                reference = evidence.get("evidence_dna")
                # Legacy claims can still participate in exact-file matching.
                if not reference and evidence.get("sha256"):
                    reference = {"sha256": evidence["sha256"], "whole": [], "patches": []}
                if not reference:
                    continue
                match = compare_evidence_dna(dna, reference)
                if match.match_type != "none":
                    matches.append({
                        "current_image_index": image_index,
                        "current_image_name": query.get("name", f"image-{image_index + 1}"),
                        "previous_case_id": case.get("case_id"),
                        "previous_image_name": evidence.get("name", "previous evidence"),
                        "similarity": round(match.similarity * 100, 1),
                        "match_type": match.match_type,
                        "reason": match.reason,
                    })
    matches.sort(key=lambda item: item["similarity"], reverse=True)
    return matches[:limit]
