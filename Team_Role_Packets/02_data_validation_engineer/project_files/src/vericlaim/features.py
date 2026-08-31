"""Deterministic, dependency-light image features for claim triage.

The production roadmap replaces or augments these features with a fine-tuned
vision backbone.  The handcrafted representation keeps the hackathon demo
fully runnable on a CPU and makes every signal auditable.
"""

from __future__ import annotations

import hashlib
import io
import math
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

import numpy as np
from PIL import ExifTags, Image, ImageOps
from scipy.fft import dctn


FEATURE_VERSION = "vericlaim-vision-v1"
IMAGE_SIZE = 96


@dataclass(frozen=True)
class ImageForensics:
    width: int
    height: int
    megapixels: float
    aspect_ratio: float
    format: str
    exif_present: bool
    gps_present: bool
    software_tag: str | None
    capture_time: str | None
    sha256: str
    perceptual_hash: str
    quality_score: float
    tamper_signal: float


def _open_image(source: str | Path | bytes | BinaryIO) -> tuple[Image.Image, bytes]:
    if isinstance(source, (str, Path)):
        raw = Path(source).read_bytes()
    elif isinstance(source, bytes):
        raw = source
    else:
        raw = source.read()
    image = Image.open(io.BytesIO(raw))
    image.load()
    original_format = image.format
    image = ImageOps.exif_transpose(image)
    image.format = original_format
    return image, raw


def _safe_exif(image: Image.Image) -> dict[str, object]:
    try:
        return {ExifTags.TAGS.get(k, str(k)): v for k, v in image.getexif().items()}
    except Exception:
        return {}


def _entropy(gray: np.ndarray) -> float:
    hist, _ = np.histogram(gray, bins=64, range=(0, 255), density=False)
    probs = hist.astype(np.float64) / max(1, hist.sum())
    probs = probs[probs > 0]
    return float(-(probs * np.log2(probs)).sum())


def _perceptual_hash(gray: np.ndarray) -> str:
    small = Image.fromarray(gray.astype(np.uint8)).resize((32, 32), Image.Resampling.LANCZOS)
    coeff = dctn(np.asarray(small, dtype=np.float32), norm="ortho")[:8, :8]
    block = coeff.flatten()[1:]
    bits = block > np.median(block)
    value = 0
    for bit in bits:
        value = (value << 1) | int(bit)
    return f"{value:016x}"


def hamming_distance(hash_a: str, hash_b: str) -> int:
    return (int(hash_a, 16) ^ int(hash_b, 16)).bit_count()


def _gradient_features(gray: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    gy, gx = np.gradient(gray.astype(np.float32))
    magnitude = np.sqrt(gx * gx + gy * gy)
    orientation = (np.arctan2(gy, gx) + np.pi) % np.pi
    return gx, magnitude, orientation


def _hog(gray: np.ndarray, cells: int = 8, bins: int = 9) -> np.ndarray:
    resized = np.asarray(
        Image.fromarray(gray.astype(np.uint8)).resize((64, 64), Image.Resampling.BILINEAR),
        dtype=np.float32,
    )
    _, magnitude, orientation = _gradient_features(resized)
    cell_size = resized.shape[0] // cells
    result: list[float] = []
    for row in range(cells):
        for col in range(cells):
            rs = slice(row * cell_size, (row + 1) * cell_size)
            cs = slice(col * cell_size, (col + 1) * cell_size)
            indices = np.minimum((orientation[rs, cs] / np.pi * bins).astype(int), bins - 1)
            hist = np.bincount(indices.ravel(), weights=magnitude[rs, cs].ravel(), minlength=bins)
            hist = hist / (np.linalg.norm(hist) + 1e-6)
            result.extend(hist.tolist())
    return np.asarray(result, dtype=np.float32)


def _block_stats(channel: np.ndarray, blocks: int = 3) -> np.ndarray:
    values: list[float] = []
    h, w = channel.shape
    for row in range(blocks):
        for col in range(blocks):
            rs = slice(row * h // blocks, (row + 1) * h // blocks)
            cs = slice(col * w // blocks, (col + 1) * w // blocks)
            block = channel[rs, cs]
            values.extend([float(block.mean()) / 255.0, float(block.std()) / 128.0])
    return np.asarray(values, dtype=np.float32)


def extract_features(source: str | Path | bytes | BinaryIO) -> tuple[np.ndarray, ImageForensics]:
    image, raw = _open_image(source)
    original_format = image.format or "unknown"
    width, height = image.size
    exif = _safe_exif(image)

    rgb_image = image.convert("RGB").resize((IMAGE_SIZE, IMAGE_SIZE), Image.Resampling.LANCZOS)
    rgb = np.asarray(rgb_image, dtype=np.float32)
    gray = np.asarray(rgb_image.convert("L"), dtype=np.float32)
    hsv = np.asarray(rgb_image.convert("HSV"), dtype=np.float32)
    _, magnitude, _ = _gradient_features(gray)
    laplacian = (
        -4 * gray
        + np.roll(gray, 1, axis=0)
        + np.roll(gray, -1, axis=0)
        + np.roll(gray, 1, axis=1)
        + np.roll(gray, -1, axis=1)
    )

    features: list[float] = [
        math.log1p(width * height),
        width / max(height, 1),
        _entropy(gray) / 8.0,
        float(magnitude.mean()) / 128.0,
        float(magnitude.std()) / 128.0,
        float(np.mean(magnitude > 20)),
        float(np.mean(magnitude > 40)),
        float(laplacian.var()) / 10000.0,
    ]
    for channels in (rgb, hsv):
        for idx in range(3):
            channel = channels[:, :, idx]
            features.extend([float(channel.mean()) / 255.0, float(channel.std()) / 128.0])
            hist, _ = np.histogram(channel, bins=16, range=(0, 255), density=False)
            features.extend((hist / max(1, hist.sum())).tolist())
    gray_hist, _ = np.histogram(gray, bins=16, range=(0, 255), density=False)
    features.extend((gray_hist / max(1, gray_hist.sum())).tolist())
    features.extend((np.quantile(gray, [0.05, 0.25, 0.5, 0.75, 0.95]) / 255.0).tolist())
    features.extend(_block_stats(gray).tolist())

    dct = dctn(
        np.asarray(rgb_image.convert("L").resize((32, 32), Image.Resampling.BILINEAR), dtype=np.float32),
        norm="ortho",
    )[:8, :8].flatten()[1:]
    features.extend((dct / (np.linalg.norm(dct) + 1e-6)).tolist())
    features.extend(_hog(gray).tolist())

    focus = float(np.clip(laplacian.var() / 4500.0, 0, 1))
    exposure = 1.0 - float(np.mean((gray < 8) | (gray > 247)))
    resolution = float(np.clip((width * height) / (1024 * 768), 0, 1))
    quality = 100.0 * (0.45 * focus + 0.35 * exposure + 0.20 * resolution)

    software = exif.get("Software")
    software_text = str(software) if software else None
    tamper = 0.0
    if software_text and any(token in software_text.lower() for token in ("photoshop", "gimp", "snapseed", "editor")):
        tamper = 0.75

    phash = _perceptual_hash(gray)
    forensic = ImageForensics(
        width=width,
        height=height,
        megapixels=round(width * height / 1_000_000, 3),
        aspect_ratio=round(width / max(height, 1), 3),
        format=original_format,
        exif_present=bool(exif),
        gps_present="GPSInfo" in exif,
        software_tag=software_text,
        capture_time=str(exif.get("DateTimeOriginal")) if exif.get("DateTimeOriginal") else None,
        sha256=hashlib.sha256(raw).hexdigest(),
        perceptual_hash=phash,
        quality_score=round(quality, 1),
        tamper_signal=round(float(np.clip(tamper, 0, 1)), 3),
    )
    return np.asarray(features, dtype=np.float32), forensic


def feature_names() -> list[str]:
    names = [
        "log_pixel_count", "aspect_ratio", "entropy", "edge_mean", "edge_std",
        "edge_density_20", "edge_density_40", "focus_variance",
    ]
    for space in ("rgb", "hsv"):
        for channel in range(3):
            names.extend([f"{space}_{channel}_mean", f"{space}_{channel}_std"])
            names.extend([f"{space}_{channel}_hist_{i}" for i in range(16)])
    names.extend([f"gray_hist_{i}" for i in range(16)])
    names.extend([f"gray_q_{q}" for q in (5, 25, 50, 75, 95)])
    names.extend([f"block_{i}_{stat}" for i in range(9) for stat in ("mean", "std")])
    names.extend([f"dct_{i}" for i in range(63)])
    names.extend([f"hog_{i}" for i in range(8 * 8 * 9)])
    return names
