"""Tests for optional image optimization."""

from io import BytesIO

from PIL import Image

from converter.image_optimizer import optimize_image


def _noisy_jpeg(tmp_path):
    path = tmp_path / "big.jpg"
    Image.effect_noise((400, 400), 60).convert("RGB").save(path, format="JPEG", quality=95)
    return path


def test_resized_jpeg_stays_jpeg(tmp_path):
    path = _noisy_jpeg(tmp_path)
    result = optimize_image(path, max_width=50, quality=85)
    assert result is not None
    data, original_size, new_size = result
    assert data[:2] == b"\xff\xd8"
    assert Image.open(BytesIO(data)).format == "JPEG"
    assert new_size < original_size


def test_small_image_is_not_optimized(tmp_path):
    path = tmp_path / "tiny.png"
    Image.new("RGB", (10, 10), (255, 0, 0)).save(path, format="PNG")
    assert optimize_image(path) is None
