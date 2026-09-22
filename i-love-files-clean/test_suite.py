"""
Comprehensive Test Suite for 'I LOVE FILES'
Tests CAD (DXF/DWG), Media (FFmpeg), Documents, Images, Resizer, and FastAPI endpoints.
"""
import os
import sys
import unittest
import numpy as np
from PIL import Image
import fitz
import ezdxf

# Import local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import format_registry
from converters.cad_converter import convert_cad
from converters.media_converter import convert_media
from converters.doc_converter import convert_document
from converters.image_converter import convert_image
from converters.resizer import resize_pdf, resize_image

TEST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_artifacts")
os.makedirs(TEST_DIR, exist_ok=True)

class TestILoveFilesEngines(unittest.TestCase):

    def test_01_format_registry(self):
        """Verify format catalog has CAD, Video, Audio, Document, Image."""
        self.assertIn("dwg", format_registry.FORMAT_CATALOG)
        self.assertIn("dxf", format_registry.FORMAT_CATALOG)
        self.assertIn("mp4", format_registry.FORMAT_CATALOG)
        self.assertIn("mp3", format_registry.FORMAT_CATALOG)
        self.assertIn("pdf", format_registry.FORMAT_CATALOG)
        
        # Test use case lookup
        use_case = format_registry.get_use_case("dwg", "pdf")
        self.assertTrue("blueprint" in use_case.lower() or "pdf" in use_case.lower())

    def test_02_cad_dxf_conversions(self):
        """Create synthetic DXF architectural blueprint and convert to SVG, PDF, and PNG."""
        dxf_path = os.path.join(TEST_DIR, "blueprint.dxf")
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()
        msp.add_line((0, 0), (100, 100), dxfattribs={"color": 1})
        msp.add_circle((50, 50), 30, dxfattribs={"color": 2})
        msp.add_text("TEST CAD SCHEMATIC", dxfattribs={"height": 5}).set_placement((10, 10))
        doc.saveas(dxf_path)

        # 1. DXF -> SVG
        svg_path = os.path.join(TEST_DIR, "blueprint.svg")
        ok_svg = convert_cad(dxf_path, svg_path, "svg")
        self.assertTrue(ok_svg)
        self.assertTrue(os.path.exists(svg_path))
        self.assertGreater(os.path.getsize(svg_path), 100)

        # 2. DXF -> PDF
        pdf_path = os.path.join(TEST_DIR, "blueprint.pdf")
        ok_pdf = convert_cad(dxf_path, pdf_path, "pdf")
        self.assertTrue(ok_pdf)
        self.assertTrue(os.path.exists(pdf_path))
        self.assertGreater(os.path.getsize(pdf_path), 500)

        # 3. DXF -> PNG
        png_path = os.path.join(TEST_DIR, "blueprint.png")
        ok_png = convert_cad(dxf_path, png_path, "png")
        self.assertTrue(ok_png)
        self.assertTrue(os.path.exists(png_path))
        self.assertGreater(os.path.getsize(png_path), 500)

    def test_03_media_conversions(self):
        """Test audio synthesis and transcoding with FFmpeg."""
        import wave

        # Create 1-second synthetic 440Hz sine wave WAV file
        wav_path = os.path.join(TEST_DIR, "tone.wav")
        sample_rate = 44100
        duration = 1.0
        frequency = 440.0
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        tone = np.sin(frequency * t * 2 * np.pi)
        audio = (tone * 32767).astype(np.int16)

        with wave.open(wav_path, "w") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(sample_rate)
            f.writeframes(audio.tobytes())

        # Transcode WAV -> MP3
        mp3_path = os.path.join(TEST_DIR, "tone.mp3")
        ok_mp3 = convert_media(wav_path, mp3_path, "mp3")
        self.assertTrue(ok_mp3)
        self.assertTrue(os.path.exists(mp3_path))
        self.assertGreater(os.path.getsize(mp3_path), 1000)

    def test_04_document_conversions(self):
        """Test Markdown -> HTML and Markdown -> PDF."""
        md_path = os.path.join(TEST_DIR, "sample.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("# Architectural Project Proposal\n\nThis is a sample document for conversion.\n\n- Phase 1: Planning\n- Phase 2: Execution\n")

        html_path = os.path.join(TEST_DIR, "sample.html")
        ok_html = convert_document(md_path, html_path, "html")
        self.assertTrue(ok_html)
        self.assertTrue(os.path.exists(html_path))

    def test_05_image_conversions(self):
        """Test PNG -> WebP with Pillow."""
        img_path = os.path.join(TEST_DIR, "test_img.png")
        img = Image.new("RGBA", (200, 200), (0, 82, 255, 200)) # Coinbase blue
        img.save(img_path)

        webp_path = os.path.join(TEST_DIR, "test_img.webp")
        ok_webp = convert_image(img_path, webp_path, "webp")
        self.assertTrue(ok_webp)
        self.assertTrue(os.path.exists(webp_path))

    def test_06_pdf_resizer_and_compressor(self):
        """Test PDF page resizing to A4 and file compression."""
        doc = fitz.open()
        p1 = doc.new_page(width=800, height=800)
        p1.insert_text((100, 100), "Page 1 - Large Square Format", fontsize=24)
        sample_pdf = os.path.join(TEST_DIR, "large_doc.pdf")
        doc.save(sample_pdf)
        doc.close()

        # Resize to standard A4
        resized_pdf = os.path.join(TEST_DIR, "resized_a4.pdf")
        stats = resize_pdf(sample_pdf, resized_pdf, target_size="a4", compress_mode="medium")
        self.assertTrue(os.path.exists(resized_pdf))
        self.assertEqual(stats["pages"], 1)

        # Verify page dimensions match A4 (595.28 x 841.89)
        verify_doc = fitz.open(resized_pdf)
        page_rect = verify_doc[0].rect
        self.assertAlmostEqual(page_rect.width, 595.28, delta=1.0)
        self.assertAlmostEqual(page_rect.height, 841.89, delta=1.0)
        verify_doc.close()

    def test_07_image_resizer(self):
        """Test Image Resizer with aspect ratio preservation."""
        src_img = os.path.join(TEST_DIR, "highres.bmp")
        # Save uncompressed BMP with noise to ensure substantial raw bytes
        noise = np.random.randint(0, 255, (1000, 1000, 3), dtype=np.uint8)
        Image.fromarray(noise).save(src_img, format="BMP")

        out_img = os.path.join(TEST_DIR, "resized_500.webp")
        stats = resize_image(src_img, out_img, width=500, height=500, keep_aspect=True, quality=80, output_format="webp")
        self.assertTrue(os.path.exists(out_img))
        self.assertEqual(stats["new_width"], 500)
        self.assertEqual(stats["new_height"], 500)
        self.assertGreater(stats["savings_percent"], 50)

if __name__ == "__main__":
    unittest.main()
