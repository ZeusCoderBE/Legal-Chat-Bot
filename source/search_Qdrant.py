import os
import source.gemini_Generate_Queries as g_G_Q
import re

from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from qdrant_client.models import Filter, FieldCondition, MatchValue
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from langchain_qdrant import Qdrant

load_dotenv()
# URL_QDRANT_3 = os.getenv("URL_QDRANT_3")
# API_QDRANT_3 = os.getenv("API_QDRANT_3")
URL_QDRANT_LOCAL = os.getenv("URL_QDRANT_LOCAL")
EXIST_ASMK_COLLECTION_NAME = os.getenv("EXIST_ASMK_COLLECTION_NAME")
EXIST_AMK_COLLECTION_NAME = os.getenv("EXIST_AMK_COLLECTION_NAME")

EMBEDDINGS_MODEL_bkai = "bkai-foundation-models/vietnamese-bi-encoder"
model_kwargs = {"device": "cpu"}
encode_kwargs = {"normalize_embeddings": True}
embeddings_bkai = HuggingFaceBgeEmbeddings(
    model_name=EMBEDDINGS_MODEL_bkai,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)

MODEL_RERANK = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
rerank_model = SentenceTransformer(MODEL_RERANK)

exist_ASMK_Collection = Qdrant.from_existing_collection(
    embedding = embeddings_bkai,
    # url = URL_QDRANT_3,
    # api_key = API_QDRANT_3,
    # prefer_grpc=True,
    url = URL_QDRANT_LOCAL,
    collection_name = EXIST_ASMK_COLLECTION_NAME,
	metadata_payload_key="metadata"
)

exist_AMK_Collection = Qdrant.from_existing_collection(
    embedding = embeddings_bkai,
    # url = URL_QDRANT_3,
    # api_key = API_QDRANT_3,
    # prefer_grpc=True,
    url = URL_QDRANT_LOCAL,
    collection_name = EXIST_AMK_COLLECTION_NAME,
	metadata_payload_key="metadata"
)

# Các metadata fields cần lọc
metadata_Fields_To_Filter = [
    "metadata.loai_van_ban_Keywords", 
    "metadata.noi_ban_hanh_Keywords", 
    "metadata.so_hieu", 
    "metadata.linhvuc_nganh_Keywords", 
    "metadata.ngay_ban_hanh", 
    "metadata.ngay_hieu_luc", 
    "metadata.chu_de_Keywords", 
    "metadata.Chapter_Keywords", 
    "metadata.Section_Keywords",  
    "metadata.Mini-Section_Keywords", 
    "metadata.Article_Keywords",
    "metadata.Article-Section_Keywords",
    "metadata.Content_Keywords",
    "metadata.combine_Article_Content_Keywords"
]

# Hàm trích xuất từ khóa từ văn bản, loại bỏ dấu câu ngoại trừ "/" và "-"
def extract_keywords(text):
    text = re.sub(r'[^\w\s/-]', '', text)  # Loại bỏ các dấu câu không mong muốn
    words = text.split()                   # Tách các từ theo khoảng trắng
    unique_words = list(dict.fromkeys(words))  # Loại bỏ từ trùng lặp
    return unique_words

# Hàm xử lý các từ khóa: chuyển về chữ thường, giữ nguyên số La Mã và từ khóa có "/" hoặc "-"
def process_keywords(keywords):
    result = []
    roman_numeral_pattern = re.compile(r"^(?=[MDCLXVI])M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$")
    
    for word in keywords:
        if roman_numeral_pattern.match(word) or any(c in word for c in "/-"):
            result.append(word)
        else:
            result.append(word.lower())  # Chuyển các từ còn lại thành chữ thường
    return result

def create_should_filter(user_keywords, metadata_fields = metadata_Fields_To_Filter):
    should_conditions = []

    for keyword in user_keywords:
        for field in metadata_fields:
            should_conditions.append(FieldCondition(
                key=field, 
                match=MatchValue(value=keyword)
            ))

    # Trả về bộ lọc với các điều kiện `should`
    return Filter(
        should=should_conditions
    )

def search_Article_Section_Documents(user_query, metadata_fields = metadata_Fields_To_Filter, top_k = 5):
    # Tách keywords từ query của user
    user_keywords = process_keywords(extract_keywords(user_query))
    
    # Tạo bộ lọc `should`
    filter_conditions = create_should_filter(user_keywords, metadata_fields)
    
    # Thực hiện tìm kiếm trên Qdrant với filter `should`
    search_results = exist_ASMK_Collection.similarity_search_with_score(
        query=user_query,
        filter=filter_conditions,
        k=top_k,
        timeout = 300
    )
    
    return search_results

def search_With_Similarity_Queries(user_query: str, key_manager):
    # Gọi hàm query_generator để sinh ra 3 truy vấn từ query gốc
    queries = g_G_Q.query_generator(user_query, key_manager)

    print("\nCác kết quả trả về:\n")
    # Lưu trữ kết quả cho từng query
    query_results = []

    # Thực hiện tìm kiếm cho mỗi query trong danh sách queries
    for query in queries:
        search_results = search_Article_Section_Documents(query)
        query_results.extend(search_results)  # Lưu kết quả riêng cho từng query

    # Dictionary để lưu các kết quả unique, key là `doc.page_content`
    unique_results = {}

    # Duyệt qua từng kết quả
    for doc, score in query_results:
        # Kiểm tra nếu `doc.page_content` đã tồn tại trong unique_results
        if doc.page_content in unique_results:
            # Nếu tồn tại, so sánh score và giữ lại cái có score cao hơn
            if score > unique_results[doc.page_content][1]:
                unique_results[doc.page_content] = (doc, score)
        else:
            # Nếu chưa tồn tại, thêm vào unique_results
            unique_results[doc.page_content] = (doc, score)

    # Trả về danh sách kết quả duy nhất, với các giá trị từ dictionary
    return list(unique_results.values())

def rerank_By_Cosin_TF_IDF(user_query, unique_results, rerank_model = rerank_model):
    # Tạo danh sách các doc.page_content từ unique_results
    documents = [doc.page_content for doc, _ in unique_results]
    
    # Tính cosine similarity
    user_query_embedding = rerank_model.encode(user_query)
    document_embeddings = rerank_model.encode(documents)
    cosine_similarities = cosine_similarity([user_query_embedding], document_embeddings)[0]

    # Tính TF-IDF
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([user_query] + documents)
    tfidf_scores = tfidf_matrix.toarray()[0][1:]  # Lấy chỉ số TF-IDF cho các documents

    # Tính điểm tổng hợp
    combined_scores = []
    for cos_sim, tfidf_score in zip(cosine_similarities, tfidf_scores):
        combined_score = 0.7 * cos_sim + 0.3 * tfidf_score
        combined_scores.append(combined_score)

    # Tạo danh sách kết quả với điểm số
    results_with_scores = [(unique_results[i][0], unique_results[i][1], combined_scores[i]) for i in range(len(unique_results))]

    # Sắp xếp kết quả theo điểm số giảm dần
    results_with_scores.sort(key=lambda x: x[2], reverse=True)

    # Lấy top 5 kết quả
    top_results = results_with_scores[:5]
    
    return top_results

def get_Article_Section_Content_Result(user_Query, key_manager):
    article_Section_Documents = search_With_Similarity_Queries(user_Query, key_manager)
    rerank_Article_Section_Documents = rerank_By_Cosin_TF_IDF(user_Query, article_Section_Documents)

    # Tạo list chỉ chứa doc.page_content từ danh sách kết quả
    article_Section_Content_Results = [result[0].metadata["combine_Article_Content"] for result in rerank_Article_Section_Documents]
    return article_Section_Content_Results

def extract_Unique_Metadata(top_results):
    metadata_list = []
    metadata_dict_set = set()  # Sử dụng set để lưu trữ các metadata duy nhất

    # Truy cập vào từng result trong top_results
    for result in top_results:
        doc = result[0]  # Lấy doc từ result
        
        # Tạo một dictionary chứa các thuộc tính từ metadata
        metadata = {
            "stt": doc.metadata.get('stt'),
            "loai_van_ban": doc.metadata.get('loai_van_ban'),
            "noi_ban_hanh": doc.metadata.get('noi_ban_hanh'),
            "so_hieu": doc.metadata.get('so_hieu'),
            "linhvuc_nganh": doc.metadata.get('linhvuc_nganh'),
            "ngay_ban_hanh": doc.metadata.get('ngay_ban_hanh'),
            "ngay_hieu_luc": doc.metadata.get('ngay_hieu_luc'),
            "chu_de": doc.metadata.get('chu_de'),
            "Chapter": doc.metadata.get('Chapter'),
            "Section": doc.metadata.get('Section'),
            "Mini-Section": doc.metadata.get('Mini-Section'),
            "Article": doc.metadata.get('Article'),
        }

        # Lọc bỏ các key-value có giá trị None
        filtered_metadata = {key: value for key, value in metadata.items() if value is not None}

        # Chuyển đổi dict thành tuple để thêm vào set
        metadata_tuple = tuple(filtered_metadata.items())
        
        # Kiểm tra và thêm vào set nếu chưa có
        metadata_dict_set.add(metadata_tuple)

    # Chuyển đổi lại set thành list và định dạng lại thành dict
    for metadata_tuple in metadata_dict_set:
        metadata_dict = dict(metadata_tuple)
        metadata_list.append(metadata_dict)

    return metadata_list

def search_Article_Documents(list_Metadata, top_k = 1):
    search_results = []

    # Duyệt qua từng phần tử trong list_Metadata
    for metadata in list_Metadata:        
        # Thực hiện tìm kiếm với query trống và bộ lọc
        results = exist_AMK_Collection.similarity_search_with_score(
            query="",  # Query để trống
            filter=metadata,
            k=top_k,
            timeout = 300
        )

        # Thêm kết quả vào danh sách tìm kiếm
        search_results.extend(results)

    return search_results

def get_Article_Content_Results(user_Query, key_manager):
    article_Section_Documents = search_With_Similarity_Queries(user_Query, key_manager)
    rerank_Article_Section_Documents = rerank_By_Cosin_TF_IDF(user_Query, article_Section_Documents)
    list_Metadata = extract_Unique_Metadata(rerank_Article_Section_Documents)
    article_Documents = search_Article_Documents(list_Metadata)
    
    article_Content_Resuls = []
    for doc, score in article_Documents:
        article_Content_Resuls.append(doc.metadata["combine_Article_Content"])

    return article_Content_Resuls

def search_Article_Section(user_Query, key_manager):
    article_Section_Content_Results = get_Article_Section_Content_Result(user_Query, key_manager)
    
    return article_Section_Content_Results

def search_Article(user_Query, key_manager):
    article_Document_Results = get_Article_Content_Results(user_Query, key_manager)
    
    return article_Document_Results