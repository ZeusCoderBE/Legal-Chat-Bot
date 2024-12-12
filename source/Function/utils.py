import re

def extract_keywords(text):
    text = re.sub(r'[^\w\s/-]', '', text)  
    words = text.split()                  
    unique_words = list(dict.fromkeys(words))  
    return unique_words

def process_keywords(keywords):
    result = []
    roman_numeral_pattern = re.compile(r"^(?=[MDCLXVI])M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$")
    
    for word in keywords:
        if roman_numeral_pattern.match(word) or any(c in word for c in "/-"):
            result.append(word)
        else:
            result.append(word.lower())  # Chuyển các từ còn lại thành chữ thường
    
    return result

def find_relevant_contexts(contexts, answers):
    lst_Relevant_Documents = []

    for answer in answers:
        for context in contexts:
            if answer in context and context not in lst_Relevant_Documents:
                # Tìm và thay thế {combine_Article_Content} bằng câu trả lời
                parts = context.split('<=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=>')

                if len(parts) > 1:
                    metadata_part = parts[0].strip()  # Lấy phần metadata
                    # Tạo một định dạng mới với {combine_Article_Content} được thay thế bằng answer
                    new_context = f"{answer}\n\n<=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=>\n\n{metadata_part}"
                    # Thêm ngữ cảnh đã thay đổi vào danh sách kết quả
                    lst_Relevant_Documents.append(new_context)

    return lst_Relevant_Documents

