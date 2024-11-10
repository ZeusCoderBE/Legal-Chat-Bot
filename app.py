import os

from dotenv import load_dotenv
from source.apikeys_GEMINI import APIKeyManager
from flask import Flask, request, jsonify,render_template
from source.generate import predict,rerank_By_Cosin_TF_IDF
from source.search_Qdrant import  search_Article

load_dotenv()
APIS_GEMINI_LIST = os.getenv('APIS_GEMINI_LIST').split(',')
key_manager = APIKeyManager(APIS_GEMINI_LIST)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chatbot', methods=['POST'])
def chatbot():
    user_input = request.json['query']
    contexts= search_Article(user_input, key_manager)
    answer_candidate= predict(contexts,user_input)
    answer=rerank_By_Cosin_TF_IDF(user_input,answer_candidate)
    print(answer)

    return jsonify({'answer': answer})

if __name__ == '__main__':
    app.run(port=5000, debug=True)
