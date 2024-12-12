import os
import cohere

from source.Function import utils as u
from source.Gemini.gemini import Gemini
from source.Gemini.apikeys_gemini import APIKeyManager
from sentence_transformers import CrossEncoder
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from qdrant_client.models import Filter, FieldCondition, MatchValue
from typing import List, Tuple
from langchain_qdrant import Qdrant

load_dotenv()
URL_QDRANT_LOCAL = os.getenv("URL_QDRANT_LOCAL")
EXIST_ASMK_COLLECTION_NAME = os.getenv("EXIST_ASMK_COLLECTION_NAME")
EXIST_AMK_COLLECTION_NAME = os.getenv("EXIST_AMK_COLLECTION_NAME")
APIS_GEMINI_LIST = os.getenv('APIS_GEMINI_LIST').split(',')
MODEL_GEMINI = os.getenv("MODEL_GEMIMI")
MODEL_RERANK=os.getenv("MODEL_RERANKER")
API_RERANKER=os.getenv('API_RERANKER').split(',')
MODEL_EMBEDDING = os.getenv("MODEL_EMBEDDING")
key_manager_cohere=APIKeyManager(API_RERANKER)
key_manager = APIKeyManager(APIS_GEMINI_LIST)

model_kwargs = {"device": "cpu"}
encode_kwargs = {"normalize_embeddings": True}
embeddings_bkai = HuggingFaceBgeEmbeddings(
    model_name=MODEL_EMBEDDING,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)

key_manager = APIKeyManager(APIS_GEMINI_LIST)
gemini_model=Gemini(key_manager,MODEL_GEMINI)

exist_ASMK_Collection = Qdrant.from_existing_collection(
    embedding = embeddings_bkai,
    url = URL_QDRANT_LOCAL,
    collection_name = EXIST_ASMK_COLLECTION_NAME,
	metadata_payload_key="metadata"
)

exist_AMK_Collection = Qdrant.from_existing_collection(
    embedding = embeddings_bkai,
    url = URL_QDRANT_LOCAL,
    collection_name = EXIST_AMK_COLLECTION_NAME,
	metadata_payload_key="metadata"
)

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

def create_should_filter(user_keywords, metadata_fields = metadata_Fields_To_Filter):
    should_conditions = []
    
    for keyword in user_keywords:
        for field in metadata_fields:
            should_conditions.append(FieldCondition(
                key=field, 
                match=MatchValue(value=keyword)
            ))
    
    return Filter(
        should=should_conditions
    )

def search_Article_Section_Documents(user_query, metadata_fields = metadata_Fields_To_Filter, top_k = 5):
    user_keywords = u.process_keywords(u.extract_keywords(user_query))
    filter_conditions = create_should_filter(user_keywords, metadata_fields)
    
    search_results = exist_ASMK_Collection.similarity_search_with_score(
        query=user_query,
        filter=filter_conditions,
        k=top_k,
        timeout = 300
    )
    
    return search_results

def search_With_Similarity_Queries(user_query: str):
    queries = gemini_model.query_generator(user_query)
    query_results = []
    for query in queries:
        search_results = search_Article_Section_Documents(query)
        query_results.extend(search_results)  

    unique_results = {}
    for doc, score in query_results:
        if doc.page_content in unique_results:
            if score > unique_results[doc.page_content][1]:
                unique_results[doc.page_content] = (doc, score)
        else:
            unique_results[doc.page_content] = (doc, score)
    
    return list(unique_results.values())

def rerank_documents(query: str, documents: List[Tuple]) -> List[Tuple[str, float]]:
    ranked_documents = []
    doc_contents = [doc.page_content for doc, _ in documents]
    try:
        co = cohere.ClientV2(key_manager_cohere.get_next_key())
        response = co.rerank(
            model=MODEL_RERANK,
            query=query,
            documents=doc_contents,
            top_n=5,
        )
        reranked_results = response.results
        ranked_documents = [documents[res.index] for res in reranked_results]
    except Exception as e:
        print(f"An error occurred: {e}")
    return ranked_documents  

def get_Article_Section_Content_Result(user_Query):
    article_Section_Documents = search_With_Similarity_Queries(user_Query)
    rerank_Article_Section_Documents = rerank_documents(user_Query,article_Section_Documents)
    
    article_Section_Content_Results = [
        result[0].metadata["combine_Article_Content"] for result in rerank_Article_Section_Documents
    ]

    return article_Section_Content_Results

def extract_Unique_Metadata(top_results):
    metadata_list = []
    metadata_dict_set = set() 

    for result in top_results:
        doc = result[0]  
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

        filtered_metadata = {key: value for key, value in metadata.items() if value is not None}
        metadata_tuple = tuple(filtered_metadata.items())
        metadata_dict_set.add(metadata_tuple)

    for metadata_tuple in metadata_dict_set:
        metadata_dict = dict(metadata_tuple)
        metadata_list.append(metadata_dict)

    return metadata_list
def search_Article_Documents(list_Metadata, top_k = 1):
    search_results = []

    for metadata in list_Metadata:        
        results = exist_AMK_Collection.similarity_search_with_score(
            query="",  
            filter=metadata,
            k=top_k,
            timeout = 300
        )
        search_results.extend(results)

    return search_results

def get_Article_Content_Results(user_Query):
    article_Section_Documents = search_With_Similarity_Queries(user_Query)
    rerank_Article_Section_Documents = rerank_documents(user_Query,article_Section_Documents)
    list_Metadata = extract_Unique_Metadata(rerank_Article_Section_Documents)
    article_Documents = search_Article_Documents(list_Metadata)

    article_Content_Resuls = []
    lst_Article_Quote = []

    for doc, _ in article_Documents:
        article_Content_Resuls.append(doc.metadata["combine_Article_Content"])
        loai_van_ban = doc.metadata.get("loai_van_ban", "N/A")
        noi_ban_hanh = doc.metadata.get("noi_ban_hanh", "N/A")
        so_hieu = doc.metadata.get("so_hieu", "N/A")
        linhvuc_nganh = doc.metadata.get("linhvuc_nganh", "N/A")
        ngay_ban_hanh = doc.metadata.get("ngay_ban_hanh", "N/A")
        ngay_hieu_luc = doc.metadata.get("ngay_hieu_luc", "N/A")
        chu_de = doc.metadata.get("chu_de", "N/A")
        chapter = doc.metadata.get("Chapter", "N/A")
        section = doc.metadata.get("Section", "N/A")
        mini_section = doc.metadata.get("Mini-Section", "N/A")
        article = doc.metadata.get("Article","N/A")
        combine_Article_Content = doc.metadata.get("combine_Article_Content", "N/A")
        formatted_quote = f"""\
                        Loại văn bản: {loai_van_ban}
                        Nơi ban hành: {noi_ban_hanh}
                        Số hiệu: {so_hieu}
                        Lĩnh vực - ngành: {linhvuc_nganh}
                        Ngày ban hành: {ngay_ban_hanh}
                        Ngày hiệu lực: {ngay_hieu_luc}
                        Chủ đề: {chu_de}
                        Chương: {chapter}
                        Mục: {section}
                        Tiểu mục: {mini_section}
                        Điều: {article}
                        <=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=>
                        {combine_Article_Content}
                        """
        lst_Article_Quote.append(formatted_quote)

    return article_Content_Resuls, lst_Article_Quote

def search_Article_Section(user_Query):
    article_Section_Content_Results = get_Article_Section_Content_Result(user_Query)
    return article_Section_Content_Results

def search_Article(user_Query):
    article_Document_Results, lst_Article_Quote = get_Article_Content_Results(user_Query)
    return article_Document_Results, lst_Article_Quote