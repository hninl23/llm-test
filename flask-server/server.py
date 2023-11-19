from flask import Flask, request, jsonify
from langchain.llms import OpenAI
from langchain.document_loaders import PyPDFLoader
from dotenv import load_dotenv
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
#from openai import get_openai_callback
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from flask_cors import CORS 
import openai
import os


app = Flask(__name__)
CORS(app)
load_dotenv()
API_KEY = os.getenv('OPENAI_API_KEY')
@app.route('/query_open_ai', methods=['POST'])
def query_open_ai():
    content_type = request.headers.get('Content-Type')
    prompt = None
    if (content_type =='application/json'):
        json_payload = request.json
        prompt = json_payload['prompt']
    else:
        return 'Content-Type not supported'
    llm = ChatOpenAI(temperature=0, model_name='gpt-3.5-turbo', openai_api_key=API_KEY, max_tokens=100)
    formatted_template = f'Answer like a Normal Person: {prompt}'
    response = llm([HumanMessage(content=formatted_template)])
    return {
        'statusCode': 500,
        'body': response.content
    }
#curl -XPOST --header "Content-Type: application/json" -d {\"prompt\":\"What is 2+2?\"}" 127.0.0.1:5000/query_open_ai
@app.route('/process-pdf', methods=['POST'])
def process_pdf():
    #load_dotenv()
    try:
        pdf = request.files['pdf']
        if pdf:
            pdf_reader = PyPDFLoader(pdf)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            # Additional processing steps go here
            print("Text from pdf:", text)

                # split into chunks
            text_splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
            )
            chunks = text_splitter.split_text(text)

            # create embeddings
            embeddings = OpenAIEmbeddings()
            knowledge_base = FAISS.from_texts(chunks, embeddings)

            # Get user question from the request
            user_question = request.form.get('user_question')

            # Load the OpenAI QA chain
            llm = OpenAI()
                    # Perform similarity search to get relevant documents
            docs = knowledge_base.similarity_search(user_question)

            # Use OpenAI's completion API for question-answering
            
            # openai.api_key = 'YOUR_OPENAI_API_KEY'  # Replace with your OpenAI API key
            
            response = llm.Completion.create(
                    model="gpt-3.5-turbo",  # You can choose a different model if needed
                    prompt=f"Question: {user_question}\nContext: {docs}",  # Combine question and context
                    temperature=0.7,  # Adjust temperature as needed
                    max_tokens=100  # Adjust max tokens as needed
            )

            answer = response['choices'][0]['text'].strip()
            print(answer)
            return jsonify({"text": text, "answer": response})
        else:
            return jsonify({"error": "PDF file not provided."})
    
    except Exception as e:
        print(f"An error occured: {e}")
        return jsonify({"error": "Internal Server Error"}), 500


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)


