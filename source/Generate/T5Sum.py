import re
import os

from dotenv import load_dotenv
from transformers import T5ForConditionalGeneration, AutoTokenizer
load_dotenv()
T5SUM_MODEL_TOKENIZER = os.getenv('T5SUM_MODEL_TOKENIZER')
T5SUM_MODEL_GENERATE = os.getenv('T5SUM_MODEL_GENERATE')
tokenizer = AutoTokenizer.from_pretrained(T5SUM_MODEL_TOKENIZER, trust_remote_code=True)
model = T5ForConditionalGeneration.from_pretrained(T5SUM_MODEL_GENERATE)
def preprocess_text(text):
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s{2,}', ' ', text)
        text = re.sub(r'\s*\.{2,}\s*', '. ', text)  
        text = re.sub(r'\s*\.\s*', '. ', text)     
        text = text.strip(" .")
        return text
def predict_summary(input_texts, max_length=200, num_beams=5):
        # Tokenize đầu vào
        inputs = tokenizer(
            input_texts,
            truncation=True,
            max_length=512,
            stride=256,
            padding="max_length",
            return_tensors="pt",
        )
        
        # Tạo dự đoán
        outputs = model.generate(
            input_ids=inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
            max_length=max_length,
            num_beams=num_beams,
            early_stopping=True
        )
        
        # Giải mã kết quả
        summary = tokenizer.decode(outputs[0], skip_special_tokens=True, clean_up_tokenization_spaces=True)
        return summary
