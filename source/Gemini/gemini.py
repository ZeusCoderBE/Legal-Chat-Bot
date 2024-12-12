from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from typing import List, Tuple

class Gemini():
    def __init__(self,key_manager,model_gemini) :
        self.key_manager=key_manager
        self.model_gemini=model_gemini

    def query_generator(self, original_query: str) -> list[str]:
        query = original_query
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", 
                """
                   Bạn là một trợ lý AI chuyên gia về pháp luật Việt Nam, chuyên phân tích ngữ nghĩa và tối ưu hóa truy vấn tìm kiếm. 
                   Nhiệm vụ:
                    - Tạo 5 câu truy vấn tìm kiếm khác nhau dựa trên truy vấn gốc, giữ nguyên ý chính nhưng thay đổi cách diễn đạt.
                    - Tăng tính bao quát và chi tiết bằng cách sử dụng từ khóa liên quan và cụm từ pháp lý thông dụng.
                    - Tối ưu hóa phù hợp với tìm kiếm trên vector database.
                """),
                ("human", f"""
                Từ câu truy vấn gốc '"{original_query}"', hãy làm 3 yêu cầu bên dưới:
                ***Yêu cầu 1 Cách tạo sinh :***
                -Tạo sinh câu hỏi bằng cách đọc kĩ hiểu câu hỏi sau đó phân loại truy vấn theo hai nhóm để biết cách tạo sinh các câu hỏi cho phù:
                    1. Người dùng không biết luật (tìm kiếm thông tin cơ bản).
                    2. Người dùng biết luật (tìm kiếm thông tin chi tiết, cụ thể với điều luật hoặc tài liệu pháp lý)
                Ví dụ cho người dùng không biết luật thì sẽ đổi thành:
                1."- 'Điều kiện để thành lập doanh nghiệp tại Việt Nam là gì?' có thể đổi thành 'Thành lập doanh nghiệp tại Việt Nam cần những điều kiện gì?'"
                2."- 'Quyền lợi của người lao động khi tham gia bảo hiểm xã hội là gì?' có thể đổi thành 'Bảo hiểm xã hội mang lại quyền lợi gì cho người lao động?'"
                3."- 'Các bước thủ tục ly hôn theo quy định của pháp luật Việt Nam như thế nào?' có thể đổi thành 'Thủ tục ly hôn theo pháp luật Việt Nam bao gồm những bước nào?'"
                4.- 'Tôi có thể khởi kiện vì bị xâm phạm quyền lợi như thế nào?' có thể đổi thành 'Cách khởi kiện khi quyền lợi bị xâm phạm là gì?'"
                5."- 'Quyền lợi của người lao động khi bị sa thải theo quy định của pháp luật là gì?' có thể đổi thành 'Khi bị sa thải, người lao động có quyền lợi gì theo pháp luật Việt Nam?'"

                Ví dụ cho người dùng biết luật thì sẽ đổi thành:
                -Khi người dùng biết luật
                "- 'Điều 12 của Luật Doanh nghiệp số 68/2014/QH13 quy định như thế nào về việc thành lập doanh nghiệp?'" " có thể đổi thành 'Luật Doanh nghiệp 68/2014/QH13 quy định về điều kiện thành lập doanh nghiệp tại Điều 12 như thế nào?'"
                "- 'Theo Luật Lao động số 45/2019/QH14, quyền lợi của người lao động khi tham gia bảo hiểm xã hội được quy định tại Chương III?'" " có thể đổi thành 'Quyền lợi của người lao động khi tham gia bảo hiểm xã hội theo Luật Lao động số 45/2019/QH14 được quy định ở đâu?'"
                "- 'Công ty tôi có thể tham gia vào hợp đồng lao động theo Điều 16 của Bộ luật Lao động 2012 không?'" " có thể đổi thành 'Bộ luật Lao động 2012 có quy định gì về hợp đồng lao động tại Điều 16 không?'"
                "- 'Thủ tục ly hôn theo pháp luật Việt Nam được quy định tại Điều 51 của Luật Hôn nhân và Gia đình 2014 như thế nào?'"" có thể đổi thành 'Luật Hôn nhân và Gia đình 2014 quy định thủ tục ly hôn ở Điều 51 ra sao?'"
                "- 'Điều 10 của Luật Đầu tư 2020 quy định về đầu tư vào ngành nghề nào tại Việt Nam?'" " có thể đổi thành 'Luật Đầu tư 2020 quy định ngành nghề nào được ưu tiên đầu tư tại Điều 10?'
                
                ***Yêu cầu 2:Cấu trúc***:
                - Các câu truy vấn không được lặp lại ý hoàn toàn.
                - Phải giữ cấu trúc rõ ràng, từ ngữ dễ hiểu, và có tính ứng dụng thực tiễn cao.
                - Dùng ngữ cảnh cụ thể hơn hoặc từ khóa liên quan nếu phù hợp.
                
                *** Yêu cầu 3:Số lượng *** 
                - Tạo chính xác 5 câu truy vấn tối ưu hóa nhất cho truy vấn gốc.
                - Chỉ trả về 5 câu truy vấn, không giải thích thêm.""")
            ]
        )


        model = ChatGoogleGenerativeAI(
            google_api_key=self.key_manager.get_next_key(),
            model=self.model_gemini,
            temperature=0
        )

        query_generator_chain = (
            prompt | model | StrOutputParser()
        )

        result = query_generator_chain.invoke({"original_query": query})
        generated_queries = result.strip().split('\n')

        if len(generated_queries) > 5:
            generated_queries = generated_queries[:5]

        queries = [query] + generated_queries

        return queries

    def prompt_template(self, docs: List[Tuple], original_query: str) -> str:
        # Kết hợp các tài liệu thành một chuỗi văn bản có cấu trúc
        context = "\n".join([doc for doc in docs])

        response_prompt = ChatPromptTemplate.from_messages([
            ("system", 
            "Bạn là một chuyên gia tư vấn pháp luật với hơn 30 năm kinh nghiệm trong nghề. "
            "Nhiệm vụ của bạn là trả lời các câu hỏi về Pháp Luật Việt Nam dựa trên thông tin được cung cấp. "
            "Bạn phải đảm bảo rằng câu trả lời chính xác, dễ hiểu, và phù hợp với các quy định pháp luật hiện hành."),
            
            ("human", f"""
            Dưới đây là câu hỏi bạn cần trả lời:
            '{original_query}'
            
            **Thông tin tham khảo để trả lời**:
            {context}
            
            **Yêu cầu trả lời**:
            
            ### 1. Phân tích câu hỏi:
            - Hiểu ý nghĩa toàn diện của câu hỏi, bao gồm các cách diễn đạt tương tự, từ đồng nghĩa và biến thể ngữ nghĩa.
            - Xác định rõ các khía cạnh chính hoặc các điểm cần làm rõ từ câu hỏi.
            
            ### 2. Cấu trúc câu trả lời:
            - Mở đầu câu trả lời ngắn gọn, đi thẳng vào ý chính.
            Ví dụ: Với câu hỏi *'Người từ bao nhiêu tuổi phải đăng ký căn cước công dân?'*, câu trả lời sẽ bắt đầu bằng câu đầu tiên là: *'Theo quy định, người từ đủ 14 tuổi phải đăng ký căn cước công dân.'*
            - Trả lời theo từng ý rõ ràng, mỗi ý tương ứng với một điểm hoặc khía cạnh cụ thể.
            - Sử dụng các số thứ tự (1, 2, 3...) hoặc dấu đầu dòng để trình bày nội dung một cách logic.
            
            ### 3. Tuân thủ nội dung:
            - Chỉ sử dụng thông tin từ nội dung được cung cấp, có thể suy diễn và suy luận.Nhưng không thêm thông tin từ bên ngoài.
                
            ### 4. Xử lý trường hợp không có thông tin:
            - Nếu không có thông tin phù hợp trong dữ liệu cung cấp, trả lời như sau: *'Xin lỗi Bạn câu hỏi này không nằm trong phần kiến thức của Tôi.'*
            
            ### 5. Phong cách trình bày:
            - Ngắn gọn, rõ ràng, súc tích nhưng vẫn đảm bảo đủ ý.
            - Chuyên nghiệp và chính xác theo ngôn ngữ pháp luật Việt Nam.
            - Tránh sử dụng ngôn ngữ không trang trọng hoặc diễn đạt quá phức tạp.
            
            ### 6. Đảm bảo chất lượng:
            - Mọi câu trả lời cần được kiểm tra tính chính xác và rõ ràng trước khi gửi đi.
            - Kết thúc câu trả lời bằng một tóm lược ngắn gọn nếu cần thiết.
            *Lưu ý mấy yêu cầu này là dành cho bạn hiểu để khi trả lời bạn làm theo yêu cầu chứ không phải kêu bạn lúc trả lời tạo ra yêu cầu.Bắt buộc lúc trả lời là chỉ trả lời chứ không được tạo ra yêu cầu ### ở trên.*
            """)
        ])
        return response_prompt

    
    def generate_response(self,original_query: str, docs: List) -> str:
        response_model = ChatGoogleGenerativeAI(
            google_api_key=self.key_manager.get_next_key(),
            model=self.model_gemini,
            temperature=0.2,
            max_tokens=3000,
            top_p=0.6,
        )

        response_chain = self.prompt_template(docs, original_query) | response_model | StrOutputParser()
        final_response = response_chain.invoke({"original_query": original_query}).strip()
        
        return final_response 