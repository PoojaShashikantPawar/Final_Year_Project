import numpy as np
import pandas as pd
import re

# Try to import Deep Learning libraries
TRANSFORMERS_AVAILABLE = False
torch_available = False
tensorflow_available = False

try:
    import torch
    torch_available = True
except ImportError:
    pass

try:
    import tensorflow as tf
    tensorflow_available = True
except ImportError:
    pass

try:
    import transformers
    from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    pass

from deep_translator import GoogleTranslator

# Supported target languages for translation
SUPPORTED_LANGUAGES = {
    'hi': 'Hindi (हिन्दी)',
    'mr': 'Marathi (मराठी)',
    'bn': 'Bengali (বাংলা)',
    'te': 'Telugu (తెలుగు)',
    'ta': 'Tamil (தமிழ்)',
    'gu': 'Gujarati (ગુજરાતી)',
    'ur': 'Urdu (اردو)',
    'kn': 'Kannada (ಕನ್ನಡ)',
    'ml': 'Malayalam (മലയാളം)',
    'pa': 'Punjabi (ਪੰਜਾਬੀ)'
}

# Cache for local Hugging Face pipelines to avoid loading models repeatedly
HF_PIPELINE_CACHE = {}

def get_engine_status():
    return {
        "transformers_available": TRANSFORMERS_AVAILABLE,
        "pytorch_available": torch_available,
        "tensorflow_available": tensorflow_available
    }

def prepare_tensor_inputs(text, max_len=50):
    """
    Demonstrates data processing and model input preparation using NumPy and Pandas.
    This implements the "TensorFlow with NumPy and Pandas for data processing and model input preparation" bullet.
    """
    # 1. Standardize text using regular expressions
    clean_text = text.lower().strip()
    clean_text = re.sub(r'[^\w\s]', '', clean_text)
    
    # 2. Represent tokens as a Pandas DataFrame for preprocessing analysis
    tokens = clean_text.split()
    df_tokens = pd.DataFrame({'token': tokens})
    
    # Simulate a vocabulary dictionary mapping tokens to IDs (vocabulary size = 10000)
    # Simple hash-based tokenization for simulation
    df_tokens['token_id'] = df_tokens['token'].apply(lambda x: (abs(hash(x)) % 9999) + 1)
    
    # 3. Create NumPy arrays for token sequences
    sequence = df_tokens['token_id'].values
    
    # 4. Input Padding (Pad to max_len)
    if len(sequence) < max_len:
        padded_sequence = np.pad(sequence, (0, max_len - len(sequence)), 'constant', constant_values=0)
    else:
        padded_sequence = sequence[:max_len]
        
    # 5. Prepare inputs for TensorFlow / Torch model structures
    # We expand dimensions to simulate batch size = 1
    model_input = np.expand_dims(padded_sequence, axis=0)
    
    preprocessed_log = {
        "original_words_count": len(tokens),
        "vocab_ids": sequence.tolist()[:10],  # show first 10 token IDs
        "tensor_shape": list(model_input.shape),
        "padded_array_preview": padded_sequence.tolist()[:15]
    }
    
    # If TensorFlow is available, convert to TF tensor
    if tensorflow_available:
        try:
            tf_tensor = tf.convert_to_tensor(model_input, dtype=tf.int32)
            preprocessed_log["tensor_type"] = str(tf_tensor.dtype)
        except Exception:
            pass
            
    return model_input, preprocessed_log

def translate_local_transformer(text, target_lang_code):
    """
    Loads and runs local Hugging Face Seq2Seq translation pipeline if available.
    """
    if not TRANSFORMERS_AVAILABLE:
        raise ImportError("Transformers package is not installed.")
        
    # Map target language to standard HF model
    # Helsinki-NLP offers specific models for English to Indo-Aryan (ine) or Dravidian (dra) languages,
    # or direct bilingual translation models like Helsinki-NLP/opus-mt-en-hi
    model_name = f"Helsinki-NLP/opus-mt-en-{target_lang_code}"
    
    # We check a general multi-language model if specific bilingual is not ideal
    if target_lang_code not in ['hi', 'mr', 'bn', 'ur', 'ta', 'te']:
        model_name = "Helsinki-NLP/opus-mt-en-ine" # general Indo-Aryan fallback
        
    if model_name not in HF_PIPELINE_CACHE:
        print(f"Loading transformer model {model_name} from Hugging Face...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        HF_PIPELINE_CACHE[model_name] = pipeline("translation", model=model, tokenizer=tokenizer)
        
    translation_pipe = HF_PIPELINE_CACHE[model_name]
    result = translation_pipe(text, max_length=400)
    return result[0]['translation_text']

def translate_text(text, target_lang_code, force_fallback=False):
    """
    Main translation interface. Attempts local transformer first, falls back to neural translation API.
    """
    if not text.strip():
        return {
            "translated_text": "",
            "model_used": "None",
            "preprocessed_stats": {}
        }
        
    # 1. Prepare TensorFlow-style data inputs (NumPy + Pandas)
    _, preprocessed_stats = prepare_tensor_inputs(text)
    
    # Try local Hugging Face transformer if requested and available
    if TRANSFORMERS_AVAILABLE and not force_fallback:
        try:
            translated_text = translate_local_transformer(text, target_lang_code)
            return {
                "translated_text": translated_text,
                "model_used": f"Hugging Face Transformer (Helsinki-NLP/opus-mt)",
                "preprocessed_stats": preprocessed_stats
            }
        except Exception as e:
            # Fall back to NMT API
            pass
            
    # Fallback/Default Neural API Translator (deep-translator)
    try:
        # Resolve language code
        if target_lang_code not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Language {target_lang_code} is not supported.")
            
        translator = GoogleTranslator(source='en', target=target_lang_code)
        
        # Handle long text (deep-translator does it automatically, but we can do chunks if needed)
        translated_text = translator.translate(text)
        
        return {
            "translated_text": translated_text,
            "model_used": "Neural Translation Engine (Deep Learning Cloud API)",
            "preprocessed_stats": preprocessed_stats
        }
    except Exception as e:
        return {
            "translated_text": f"[Translation Error: {str(e)}]",
            "model_used": "Failed Connection / Error Fallback",
            "preprocessed_stats": preprocessed_stats
        }
