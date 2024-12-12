import numpy as np
import torch
import os 
import cohere
from transformers import AutoTokenizer, AutoModelForQuestionAnswering
from source.Gemini.apikeys_gemini import APIKeyManager
from source.Gemini.gemini import Gemini
from dotenv import load_dotenv

load_dotenv()
MODEL_EXTRACT=os.getenv("GENERATE_MODEL_EXTRACT")
TOKENIZER=os.getenv("GENERATE_MODEL_TOKENIZER")
MODEL_GEMINI = os.getenv("MODEL_GEMIMI")
APIS_GEMINI_LIST = os.getenv('APIS_GEMINI_LIST').split(',')
key_manager = APIKeyManager(APIS_GEMINI_LIST)
API_RERANKER=os.getenv('API_RERANKER').split(',')
key_manager_cohere=APIKeyManager(API_RERANKER)
MODEL_RERANK=os.getenv("MODEL_RERANKER")
model =AutoModelForQuestionAnswering.from_pretrained(MODEL_EXTRACT, token='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')
tokenizer = AutoTokenizer.from_pretrained(TOKENIZER)
MAX_LENGTH = 512
STRIDE = 380
N_BEST = 180
MAX_ANSWER_LENGTH = 2000
model_gemini=Gemini(key_manager,MODEL_GEMINI)

def predict(contexts, question):
    lst_Answer_Final = []  
    txt_Answer_Final = ""  
    for context in contexts:
        inputs = tokenizer(
            question,
            context,
            max_length=MAX_LENGTH,
            truncation="only_second",
            stride=STRIDE,
            return_offsets_mapping=True,
            padding="max_length",
            return_tensors="pt"
        )

        with torch.no_grad():
            outputs = model(**{k: v for k, v in inputs.items() if k in ['input_ids', 'attention_mask']})
        
        start_logits = outputs.start_logits.squeeze().cpu().numpy()
        end_logits = outputs.end_logits.squeeze().cpu().numpy()
        offsets = inputs["offset_mapping"][0].cpu().numpy()
        
        answers = []
        start_indexes = np.argsort(start_logits)[-N_BEST:][::-1].tolist()
        end_indexes = np.argsort(end_logits)[-N_BEST:][::-1].tolist()

        for start_index in start_indexes:
            for end_index in end_indexes:
                if end_index < start_index or end_index - start_index + 1 > MAX_ANSWER_LENGTH:
                    continue
                if offsets[start_index][0] is not None and offsets[end_index][1] is not None:
                    answer_text = context[offsets[start_index][0]: offsets[end_index][1]].strip()
                    if answer_text:
                        answer = {
                            "text": answer_text,
                            "score": start_logits[start_index] + end_logits[end_index],
                        }
                        answers.append(answer)
        
        if answers:
            answers.sort(key=lambda x: x["score"], reverse=True)
            best_answer = answers[0]['text']
            
            if best_answer not in lst_Answer_Final:
                lst_Answer_Final.append(best_answer)
        else: 
            return "Không có câu trả lời"
        txt_Answer_Final="\n".join(lst_Answer_Final)
    return lst_Answer_Final , txt_Answer_Final
def results_Gemini(question, lst_Answer_Final):
    result_final = model_gemini.generate_response(question, lst_Answer_Final)
    return result_final