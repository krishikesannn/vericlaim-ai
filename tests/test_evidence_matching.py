import io
import unittest

from PIL import Image, ImageDraw, ImageOps

from vericlaim.evidence_matching import build_evidence_dna, compare_evidence_dna, find_historical_matches


def image_bytes(image: Image.Image) -> bytes:
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue()


def evidence_scene() -> Image.Image:
    image = Image.new("RGB", (480, 360), "#d8e3e8")
    draw = ImageDraw.Draw(image)
    draw.rectangle((30, 40, 450, 300), fill="#27465c", outline="#101820", width=7)
    draw.ellipse((65, 235, 155, 325), fill="#111111", outline="#9ee8ff", width=8)
    draw.ellipse((330, 235, 420, 325), fill="#111111", outline="#9ee8ff", width=8)
    draw.polygon([(180, 80), (370, 95), (420, 230), (115, 225)], fill="#cf334b")
    for offset in range(0, 90, 12):
        draw.line((235 + offset, 110, 180 + offset, 220), fill="#ffe070", width=5)
    draw.rectangle((360, 120, 405, 170), fill="#ffffff")
    return image


class EvidenceMatchingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = evidence_scene()
        cls.reference = build_evidence_dna(image_bytes(cls.original))

    def assert_detected(self, transformed: Image.Image):
        query = build_evidence_dna(image_bytes(transformed))
        match = compare_evidence_dna(query, self.reference)
        self.assertNotEqual(match.match_type, "none", match)
        self.assertGreaterEqual(match.similarity, 0.91)

    def test_exact_file(self):
        match = compare_evidence_dna(self.reference, self.reference)
        self.assertEqual(match.match_type, "exact")

    def test_horizontal_flip(self):
        self.assert_detected(ImageOps.mirror(self.original))

    def test_inverted_image(self):
        self.assert_detected(ImageOps.invert(self.original))

    def test_right_angle_rotation(self):
        self.assert_detected(self.original.rotate(90, expand=True))

    def test_small_arbitrary_rotation(self):
        self.assert_detected(self.original.rotate(15, expand=False, fillcolor=(0, 0, 0)))

    def test_small_cropped_segment(self):
        self.assert_detected(self.original.crop((110, 70, 360, 245)).resize((500, 350)))

    def test_cropped_inverted_segment(self):
        segment = self.original.crop((110, 70, 360, 245)).resize((500, 350))
        self.assert_detected(ImageOps.invert(segment))

    def test_jpeg_recompression(self):
        stream = io.BytesIO()
        self.original.save(stream, format="JPEG", quality=35)
        query = build_evidence_dna(stream.getvalue())
        match = compare_evidence_dna(query, self.reference)
        self.assertNotEqual(match.match_type, "none", match)

    def test_historical_case_details(self):
        query = {"name": "cropped.png", "evidence_dna": build_evidence_dna(image_bytes(self.original.crop((110, 70, 360, 245))))}
        cases = [{"case_id": "VC-OLD1234", "evidence_manifest": [{"name": "original.png", "evidence_dna": self.reference}]}]
        matches = find_historical_matches([query], cases)
        self.assertEqual(matches[0]["previous_case_id"], "VC-OLD1234")
        self.assertIn(matches[0]["match_type"], {"partial", "transformed"})

    def test_unrelated_image_is_not_flagged(self):
        unrelated = Image.new("RGB", (480, 360), "#f6f1dd")
        draw = ImageDraw.Draw(unrelated)
        for x in range(0, 480, 30):
            draw.ellipse((x, 20 + x % 90, x + 18, 38 + x % 90), fill="#2f8f5b")
        match = compare_evidence_dna(build_evidence_dna(image_bytes(unrelated)), self.reference)
        self.assertEqual(match.match_type, "none", match)


if __name__ == "__main__":
    unittest.main()
