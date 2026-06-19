import os
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, make_response
from werkzeug.utils import secure_filename

from config import Config
import database
import ocr_engine
import translation_engine

app = Flask(__name__)
app.config.from_object(Config)

# Initialize application directories and database tables
Config.init_app()
database.init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@app.route('/')
def dashboard():
    stats = database.get_translation_stats()
    recent = database.get_recent_translations(limit=5)
    tesseract_info = ocr_engine.check_tesseract_status()
    engine_info = translation_engine.get_engine_status()
    
    # Supported languages list for selection dropdown
    languages = translation_engine.SUPPORTED_LANGUAGES
    
    return render_template(
        'dashboard.html', 
        stats=stats, 
        recent=recent, 
        tesseract_info=tesseract_info, 
        engine_info=engine_info,
        languages=languages
    )

@app.route('/translator')
def translator_workspace():
    languages = translation_engine.SUPPORTED_LANGUAGES
    tesseract_info = ocr_engine.check_tesseract_status()
    return render_template('translator.html', languages=languages, tesseract_info=tesseract_info)

@app.route('/api/process', methods=['POST'])
def api_process():
    """
    Handles combined OCR and Translation requests.
    Supports:
    1. Direct Text Translation (only original_text + target_lang provided)
    2. Image OCR + Translation (image file + target_lang + preprocessing options provided)
    """
    target_lang = request.form.get('target_lang', 'hi')
    force_fallback = request.form.get('force_fallback', 'false').lower() == 'true'
    
    # 1. OCR + Translation flow
    if 'file' in request.files and request.files['file'].filename != '':
        file = request.files['file']
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Unsupported file type.'}), 400
            
        # Get preprocessing parameters from request
        denoise = request.form.get('denoise', 'true').lower() == 'true'
        threshold = request.form.get('threshold', 'true').lower() == 'true'
        contrast = request.form.get('contrast', 'true').lower() == 'true'
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        # Append unique prefix to avoid collisions
        import time
        unique_filename = f"{int(time.time())}_{filename}"
        file_path = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        
        try:
            # Perform OCR
            ocr_result = ocr_engine.extract_text(
                file_path, 
                denoise=denoise, 
                threshold=threshold, 
                contrast=contrast
            )
            
            extracted_text = ocr_result['text']
            confidence = ocr_result['confidence']
            processed_image = ocr_result['processed_image']
            ocr_method = ocr_result['method']
            
            # Save OCR log to database
            doc_id = database.save_ocr_document(
                filename=unique_filename,
                file_path=file_path,
                extracted_text=extracted_text,
                accuracy_score=confidence,
                noise_reduction_applied=denoise
            )
            
            # Translate text
            translation_result = translation_engine.translate_text(
                extracted_text, 
                target_lang,
                force_fallback=force_fallback
            )
            
            translated_text = translation_result['translated_text']
            model_used = translation_result['model_used']
            preprocessed_stats = translation_result['preprocessed_stats']
            
            # Save translation log
            database.save_translation(
                document_id=doc_id,
                original_text=extracted_text,
                translated_text=translated_text,
                target_lang=translation_engine.SUPPORTED_LANGUAGES.get(target_lang, target_lang),
                model_used=model_used
            )
            
            return jsonify({
                'success': True,
                'mode': 'ocr_translation',
                'original_text': extracted_text,
                'translated_text': translated_text,
                'confidence': confidence,
                'original_image': unique_filename,
                'processed_image': processed_image,
                'model_used': f"{ocr_method} -> {model_used}",
                'preprocessed_stats': preprocessed_stats
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': f"Processing error: {str(e)}"}), 500
            
    # 2. Text-only Translation flow
    else:
        original_text = request.form.get('original_text', '').strip()
        if not original_text:
            return jsonify({'success': False, 'error': 'No input text or file provided.'}), 400
            
        try:
            translation_result = translation_engine.translate_text(
                original_text, 
                target_lang,
                force_fallback=force_fallback
            )
            
            translated_text = translation_result['translated_text']
            model_used = translation_result['model_used']
            preprocessed_stats = translation_result['preprocessed_stats']
            
            # Save to Database with dummy document ID
            database.save_translation(
                document_id=None,
                original_text=original_text,
                translated_text=translated_text,
                target_lang=translation_engine.SUPPORTED_LANGUAGES.get(target_lang, target_lang),
                model_used=model_used
            )
            
            return jsonify({
                'success': True,
                'mode': 'text_only',
                'original_text': original_text,
                'translated_text': translated_text,
                'confidence': 100.0,  # Max confidence for raw text inputs
                'model_used': model_used,
                'preprocessed_stats': preprocessed_stats
            })
        except Exception as e:
            return jsonify({'success': False, 'error': f"Translation error: {str(e)}"}), 500

@app.route('/history')
def history_log():
    records = database.get_all_translations()
    return render_template('history.html', records=records)

@app.route('/api/delete/<int:record_id>', methods=['POST'])
def api_delete_record(record_id):
    success = database.delete_translation(record_id)
    return jsonify({'success': success})

@app.route('/download/<int:record_id>/<string:fmt>')
def download_record(record_id, fmt):
    record = database.get_translation_by_id(record_id)
    if not record:
        return redirect(url_for('history_log'))
        
    filename = record['filename'] or 'text_input'
    target_lang = record['target_lang']
    date_str = record['translated_at'].replace(' ', '_').replace(':', '-')
    
    if fmt == 'txt':
        content = (
            f"==================================================\n"
            f"MULTILINGUAL RESOURCE TRANSLATION EXPORT\n"
            f"Source Document: {filename}\n"
            f"Translation Date: {record['translated_at']}\n"
            f"Target Language: {target_lang}\n"
            f"Model Engine: {record['model_used']}\n"
            f"OCR Accuracy (if applicable): {record['accuracy_score'] or 'N/A'}%\n"
            f"==================================================\n\n"
            f"--- ORIGINAL ENGLISH TEXT ---\n"
            f"{record['original_text']}\n\n"
            f"--- TRANSLATED REGIONAL TEXT ({target_lang}) ---\n"
            f"{record['translated_text']}\n"
        )
        
        response = make_response(content)
        response.headers["Content-Disposition"] = f"attachment; filename=translation_{date_str}_{target_lang}.txt"
        response.headers["Content-Type"] = "text/plain; charset=utf-8"
        return response
        
    elif fmt == 'json':
        response_data = {
            "source_document": filename,
            "translated_at": record['translated_at'],
            "target_language": target_lang,
            "model_used": record['model_used'],
            "ocr_accuracy": record['accuracy_score'],
            "original_text": record['original_text'],
            "translated_text": record['translated_text']
        }
        
        response = make_response(json.dumps(response_data, indent=4, ensure_ascii=False))
        response.headers["Content-Disposition"] = f"attachment; filename=translation_{date_str}_{target_lang}.json"
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return response

    return redirect(url_for('history_log'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
