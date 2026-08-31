"""Attention-map support for the deployed EfficientNet visual signal.

The map explains where the CNN's *visual component* responded. It is not an
explanation of fraud, and it is never evidence for an automatic claim outcome.
"""

from __future__ import annotations

import base64
import io
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps


def efficientnet_attention_map(backbone_path: Path, cnn_models: list, source: bytes, image_size: int) -> str | None:
    if not cnn_models:
        return None
    import tensorflow as tf

    image = Image.open(io.BytesIO(source)).convert("RGB")
    contained = ImageOps.contain(image, (image_size, image_size), Image.Resampling.BILINEAR)
    canvas = Image.new("RGB", (image_size, image_size))
    canvas.paste(contained, ((image_size - contained.width) // 2, (image_size - contained.height) // 2))
    pixels = np.asarray(canvas, dtype=np.float32)[None, ...]
    backbone = tf.keras.models.load_model(backbone_path, compile=False)
    conv_layer = next((layer for layer in reversed(backbone.layers) if isinstance(layer, tf.keras.layers.Conv2D)), None)
    if conv_layer is None:
        return None
    gradient_model = tf.keras.Model(backbone.inputs, [conv_layer.output, backbone.output])
    coefficients = np.mean([model.coef_[0] for model in cnn_models], axis=0).astype(np.float32)
    with tf.GradientTape() as tape:
        conv, embedding = gradient_model(pixels)
        score = tf.reduce_sum(embedding * coefficients[None, :])
    grads = tape.gradient(score, conv)[0]
    heat = tf.reduce_sum(grads * conv[0], axis=-1)
    heat = tf.maximum(heat, 0)
    heat = heat / (tf.reduce_max(heat) + 1e-8)
    heat_image = Image.fromarray(np.uint8(heat.numpy() * 255)).resize(canvas.size, Image.Resampling.BILINEAR)
    overlay = Image.blend(canvas, Image.merge("RGB", (heat_image, Image.new("L", canvas.size), Image.new("L", canvas.size))), 0.35)
    buffer = io.BytesIO()
    overlay.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")
