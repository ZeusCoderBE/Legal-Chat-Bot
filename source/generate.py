import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForQuestionAnswering
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
model = AutoModelForQuestionAnswering.from_pretrained("quanghuy123/fine-tuning-bert-for-QA",token='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')
tokenizer = AutoTokenizer.from_pretrained('google-bert/bert-base-multilingual-cased')
MODEL_RERANK = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
rerank_model = SentenceTransformer(MODEL_RERANK)
MAX_LENGTH = 512
STRIDE = 380
N_BEST = 180
MAX_ANSWER_LENGTH = 2000
def predict(contexts, question):
    answer_final = []
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
            if best_answer not in answer_final:
                answer_final.append(best_answer)
        else: 
            return "Không có câu trả lời"
    return answer_final  

def rerank_By_Cosin_TF_IDF(user_query, documents):
    user_query_embedding = rerank_model.encode(user_query)
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(documents)  
    user_query_tfidf = vectorizer.transform([user_query]) 
    tfidf_scores = cosine_similarity(user_query_tfidf, tfidf_matrix).flatten() 
    
    combined_scores = []
    for i, document in enumerate(documents):
        document_embedding = rerank_model.encode(document) 
        cos_sim = cosine_similarity([user_query_embedding], [document_embedding])[0][0]  
        combined_score = 0.7 * cos_sim + 0.3 * tfidf_scores[i]  
        combined_scores.append(combined_score)
    
    results_with_scores = [(documents[i], combined_scores[i]) for i in range(len(documents))]
    results_with_scores.sort(key=lambda x: x[1], reverse=True)
    top_results = [results_with_scores[i][0] for i in range(min(3, len(documents)))]
    return top_results