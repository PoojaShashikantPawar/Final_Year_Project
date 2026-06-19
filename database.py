import sqlite3
import os
from datetime import datetime
from config import Config

def get_db_connection():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create OCR Documents table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ocr_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            uploaded_at TEXT NOT NULL,
            extracted_text TEXT,
            accuracy_score REAL DEFAULT 0.0,
            noise_reduction_applied INTEGER DEFAULT 0
        )
    ''')
    
    # Create Translations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS translations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER,
            original_text TEXT NOT NULL,
            translated_text TEXT NOT NULL,
            source_lang TEXT DEFAULT 'English',
            target_lang TEXT NOT NULL,
            translated_at TEXT NOT NULL,
            model_used TEXT NOT NULL,
            FOREIGN KEY (document_id) REFERENCES ocr_documents (id) ON DELETE SET NULL
        )
    ''')
    
    conn.commit()
    conn.close()

def save_ocr_document(filename, file_path, extracted_text, accuracy_score, noise_reduction_applied):
    conn = get_db_connection()
    cursor = conn.cursor()
    uploaded_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
        INSERT INTO ocr_documents (filename, file_path, uploaded_at, extracted_text, accuracy_score, noise_reduction_applied)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (filename, file_path, uploaded_at, extracted_text, accuracy_score, 1 if noise_reduction_applied else 0))
    
    doc_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return doc_id

def save_translation(document_id, original_text, translated_text, target_lang, model_used):
    conn = get_db_connection()
    cursor = conn.cursor()
    translated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
        INSERT INTO translations (document_id, original_text, translated_text, target_lang, translated_at, model_used)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (document_id, original_text, translated_text, target_lang, translated_at, model_used))
    
    translation_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return translation_id

def get_recent_translations(limit=10):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT t.id, t.original_text, t.translated_text, t.target_lang, t.translated_at, t.model_used,
               d.filename, d.accuracy_score, d.noise_reduction_applied
        FROM translations t
        LEFT JOIN ocr_documents d ON t.document_id = d.id
        ORDER BY t.translated_at DESC
        LIMIT ?
    ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_all_translations():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT t.id, t.original_text, t.translated_text, t.target_lang, t.translated_at, t.model_used,
               d.filename, d.accuracy_score, d.noise_reduction_applied
        FROM translations t
        LEFT JOIN ocr_documents d ON t.document_id = d.id
        ORDER BY t.translated_at DESC
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_translation_by_id(translation_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT t.id, t.original_text, t.translated_text, t.target_lang, t.translated_at, t.model_used,
               d.filename, d.accuracy_score
        FROM translations t
        LEFT JOIN ocr_documents d ON t.document_id = d.id
        WHERE t.id = ?
    ''', (translation_id,))
    
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def delete_translation(translation_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Retrieve document ID to clean it up if necessary (optional)
    cursor.execute('SELECT document_id FROM translations WHERE id = ?', (translation_id,))
    row = cursor.fetchone()
    doc_id = row[0] if row else None
    
    cursor.execute('DELETE FROM translations WHERE id = ?', (translation_id,))
    
    if doc_id:
        cursor.execute('DELETE FROM ocr_documents WHERE id = ?', (doc_id,))
        
    conn.commit()
    conn.close()
    return True

def get_translation_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # Total translations
    cursor.execute('SELECT COUNT(*) FROM translations')
    stats['total_translations'] = cursor.fetchone()[0]
    
    # Average OCR accuracy
    cursor.execute('SELECT AVG(accuracy_score) FROM ocr_documents WHERE accuracy_score > 0')
    val = cursor.fetchone()[0]
    stats['avg_ocr_accuracy'] = round(val, 2) if val else 0.0
    
    # Language distribution
    cursor.execute('SELECT target_lang, COUNT(*) as count FROM translations GROUP BY target_lang')
    stats['lang_distribution'] = {row['target_lang']: row['count'] for row in cursor.fetchall()}
    
    # Accuracy over time (last 7 logs)
    cursor.execute('''
        SELECT d.uploaded_at, d.accuracy_score 
        FROM ocr_documents d 
        WHERE d.accuracy_score > 0
        ORDER BY d.uploaded_at DESC 
        LIMIT 7
    ''')
    stats['accuracy_history'] = [{'date': row[0][:10], 'score': row[1]} for row in cursor.fetchall()][::-1]
    
    conn.close()
    return stats
