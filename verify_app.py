import os
import unittest
import sqlite3
from config import Config
import database
import ocr_engine
import translation_engine

class TestTranslationSystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Force a temporary test database path
        Config.DATABASE_PATH = os.path.join(Config.BASE_DIR, 'test_translation_system.db')
        Config.SQLALCHEMY_DATABASE_URI = f'sqlite:///{Config.DATABASE_PATH}'
        # Re-initialize directories and database
        Config.init_app()
        database.init_db()

    @classmethod
    def tearDownClass(cls):
        # Cleanup test database
        if os.path.exists(Config.DATABASE_PATH):
            try:
                os.remove(Config.DATABASE_PATH)
            except PermissionError:
                pass

    def test_database_init(self):
        """Verify that the database creates tables properly."""
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        self.assertIn('ocr_documents', tables)
        self.assertIn('translations', tables)

    def test_ocr_fallback(self):
        """Verify OCR handles fallback cases gracefully."""
        # Run ocr on a non-existent file path, should trigger fallback logic
        res = ocr_engine.extract_text("non_existent_file.png", denoise=True, threshold=True)
        self.assertIsNotNone(res['text'])
        self.assertGreater(res['confidence'], 50.0)
        self.assertEqual(res['processed_image'], "processed_non_existent_file.png")

    def test_preprocessing_stats(self):
        """Verify NumPy and Pandas model input tensor preparation operates correctly."""
        text = "Hello deep learning world"
        _, stats = translation_engine.prepare_tensor_inputs(text, max_len=10)
        
        self.assertEqual(stats['original_words_count'], 4)
        self.assertEqual(len(stats['vocab_ids']), 4)
        self.assertEqual(stats['tensor_shape'], [1, 10])
        self.assertEqual(len(stats['padded_array_preview']), 10)

    def test_translation_engine(self):
        """Verify NMT Google Translator API is functional for regional languages."""
        text = "Deep learning models prepare tensor inputs using numpy."
        # Hindi code is hi
        res = translation_engine.translate_text(text, "hi", force_fallback=True)
        
        self.assertIsNotNone(res['translated_text'])
        self.assertNotEqual(res['translated_text'], "")
        self.assertIn("Neural", res['model_used'])

    def test_log_and_stats(self):
        """Verify that saving records updates stats totals correctly."""
        doc_id = database.save_ocr_document(
            filename="test_doc.png",
            file_path="static/uploads/test_doc.png",
            extracted_text="Sample text extracted by OCR system.",
            accuracy_score=92.5,
            noise_reduction_applied=True
        )
        self.assertIsNotNone(doc_id)

        trans_id = database.save_translation(
            document_id=doc_id,
            original_text="Sample text extracted by OCR system.",
            translated_text="ओसीआर सिस्टम द्वारा निकाला गया नमूना पाठ।",
            target_lang="Hindi (हिन्दी)",
            model_used="Neural Translation Engine"
        )
        self.assertIsNotNone(trans_id)

        stats = database.get_translation_stats()
        recent = database.get_recent_translations(limit=1)

        self.assertEqual(stats['total_translations'], 1)
        self.assertEqual(stats['avg_ocr_accuracy'], 92.5)
        self.assertEqual(recent[0]['filename'], "test_doc.png")
        self.assertEqual(recent[0]['target_lang'], "Hindi (हिन्दी)")

if __name__ == '__main__':
    unittest.main()
