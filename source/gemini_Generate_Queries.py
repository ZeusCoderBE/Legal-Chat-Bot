import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

MODEL_GEMINI = os.getenv("MODEL_GEMIMI")
if MODEL_GEMINI is None:
    raise ValueError("Environment variable MODEL_GEMINI is not set")
elif not MODEL_GEMINI.startswith("models/"):
    MODEL_GEMINI = f"models/{MODEL_GEMINI}"

def query_generator(original_query: str, key_manager) -> list[str]:
    """Generate queries from original query"""
    # Câu truy vấn gốc
    query = original_query
    
    # Cập nhật prompt để yêu cầu rõ ràng chỉ trả về 3 câu truy vấn và câu gốc
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Bạn là một trợ lý hữu ích và có nhiệm vụ tạo ra nhiều truy vấn tìm kiếm dựa trên một truy vấn gốc."),
            ("human", """Tạo chính xác 3 câu truy vấn tìm kiếm liên quan đến: {original_query}. Mỗi câu truy vấn trên một dòng mới. 
            Không được trả về nhiều hơn hoặc ít hơn 3 câu truy vấn. Đảm bảo không thêm bất kỳ văn bản nào khác ngoài 3 câu truy vấn này."""),
        ]
    )
    
    model = ChatGoogleGenerativeAI(
        # key api google gemini, nếu test mà bị báo lỗi api core thì lấy api khác trong .env để test
        google_api_key=key_manager.get_next_key(),
        model=MODEL_GEMINI,
        temperature=0.15
    )
    
    query_generator_chain = (
        prompt | model | StrOutputParser()
    )
    
    # Kết quả sẽ là một chuỗi các câu truy vấn cách nhau bằng dấu xuống dòng
    result = query_generator_chain.invoke({"original_query": query})
    
    # Tách kết quả thành danh sách các câu truy vấn
    generated_queries = result.strip().split('\n')
    
    # Đảm bảo chỉ lấy 3 câu truy vấn nếu có nhiều hơn 3 câu sinh ra
    if len(generated_queries) > 3:
        generated_queries = generated_queries[:len(generated_queries) - 1]
    
    # Kết hợp câu gốc với các câu truy vấn sinh ra
    queries = [query] + generated_queries
    
    return queries