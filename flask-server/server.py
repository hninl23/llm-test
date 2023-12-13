from flask import Flask, request, jsonify, render_template
from langchain.llms import OpenAI
from langchain.document_loaders import PyPDFLoader,WebBaseLoader
from dotenv import load_dotenv
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from flask_cors import CORS 
import openai
import os
import chromadb
from langchain.prompts import PromptTemplate
from chromadb.config import Settings
from langchain.retrievers import SVMRetriever
from langchain.retrievers import ContextualCompressionRetriever
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.retrievers.document_compressors import LLMChainExtractor
import time
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
import asyncio
from langchain.callbacks import get_openai_callback
from langchain.llms import OpenAI
from datetime import datetime
import requests


# Tenacity library
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # for exponential backoff

gpt_rpm = 3
ada_rpm = 3


@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(gpt_rpm))
def completion_with_backoff_ChatOpenAI(**kwargs):
    if len(kwargs) == 0:
        print("ChatOpenAI/no args")
        return ChatOpenAI()
    return ChatOpenAI(**kwargs)


@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(ada_rpm))
def completion_with_backoff_Embedding(**kwargs):
    if len(kwargs) == 0:
        print("OpenAIEmbeddings/no args")
        return OpenAIEmbeddings()
    return OpenAIEmbeddings(**kwargs)

# QA with embedding RPM


@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(ada_rpm))
def completion_with_backoff_qa(func):
    # if len(kwargs) == 0:
    #     print("OpenAIEmbeddings/no args")
    #     return qa()
    # def wrapper(**kwargs):
    #     return func(**kwargs)
    return func

# For current day only
def get_total_api_calls():
    api_calls_today = {'text-embedding-ada-002-v2': 0, 'gpt-3.5-turbo-0613': 0, 'text-davinci:003': 0}
    headers = {'Authorization': f'Bearer {API_KEY}'}
    url = 'https://api.openai.com/v1/usage'
    # today_date = datetime.date(2023, 12, 13)
    # today = datetime.now().date
    today_date = str(datetime.now().date())
    params = {'date': today_date}
    print(today_date)
    # print(type(today_date))
    response = requests.get(url, headers=headers, params=params)
    usage_data = response.json()['data']
    # all_data = response.json()
    # with open('usage_data.txt', 'w') as file:
    #     file.write(str(usage_data))
    for data in usage_data:
        if (data['snapshot_id'] == 'gpt-3.5-turbo-0613'):
            # print(data['n_requests'])
            api_calls_today['gpt-3.5-turbo-0613'] += data['n_requests']
        if (data['snapshot_id'] == 'text-embedding-ada-002-v2'):
            # print(data['n_requests'])
            api_calls_today['text-embedding-ada-002-v2'] += data['n_requests']
        if (data['snapshot_id'] == 'text-davinci:003'):
            # print(data['n_requests'])
            api_calls_today['text-davinci:003'] += data['n_requests']
    print(api_calls_today)
    return(api_calls_today)

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

token_counts_history = []
initial_time = time.strftime("%A, %d. %B %Y %I:%M:%S %p") 

try:
    path = os.path.dirname(os.path.abspath(__file__))
    upload_folder = os.path.join(path, "tmp")
    os.makedirs(upload_folder, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = upload_folder
except Exception as e:
    app.logger.info("Error in creating upload folder:")
    app.logger.error("Exception occured: {}".format(e))

@app.route('/process_pdf', methods=['POST', 'GET'])
def process_pdf():
    try:
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    except Exception as e:
        app.logger.error(f"Error in creating upload folder: {e}")

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    pdf_file = request.files['file']
    if pdf_file is not None:

        save_path = os.path.join(app.config.get('UPLOAD_FOLDER'), "temp.pdf")
        pdf_file.save(save_path)

        loader = PyPDFLoader(save_path)

        pages = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_documents(pages)

        # embeddings = OpenAIEmbeddings()
        embeddings = completion_with_backoff_Embedding()

        vectordb = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory="./data"
        )
        # llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
        llm = completion_with_backoff_ChatOpenAI()

        template = """Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer. Use two sentences maximum. Keep the answer as concise as possible. Always say "thanks for asking!" at the end of the answer. 
            {context}
            Question: {question}
            Helpful Answer:"""
        QA_CHAIN_PROMPT = PromptTemplate(input_variables=["context", "question"],template=template,)

        memory = ConversationBufferMemory(
            memory_key="chat_history", #chat history is a lsit of messages
            return_messages=True
        )
        qa = ConversationalRetrievalChain.from_llm(
            llm,
            retriever=vectordb.as_retriever(search_type="similarity", search_kwargs={"k": 2}),
            memory=memory
        )

        question= request.form.get('question')
        with get_openai_callback() as cb:
            # result = qa({"question": question})
            result = completion_with_backoff_qa(qa({"question": question}))
            token_counts_history.append(cb.total_tokens)
        ans = result.get('answer')
        # print(result['answer'])
        # question="How much are they worth?"
        # result = qa({"question": question})
        # print(result['answer'])
        print(ans)
        return jsonify({
            'statusCode': 200,
            'ans': ans
        })
    else:
        # Return an error response if the file is not provided
        return jsonify({'statusCode': 400, 'error': 'PDF file not provided'})

def print_date_time():
    print(time.strftime("%A, %d. %B %Y %I:%M:%S %p"))
    return(time.strftime("%A, %d. %B %Y %I:%M:%S %p"))

def count_token():
    print(sum(token_counts_history))
    return(sum(token_counts_history))

# Create the background scheduler
scheduler = BackgroundScheduler()
# Create the job
scheduler.add_job(func=print_date_time, trigger="interval", minutes=1)
scheduler.add_job(func=count_token, trigger="interval", minutes=1)
# Start the scheduler
scheduler.start()

@app.route('/get_date_time', methods=['GET'])
def get_date_time():
    current_time = time.strftime("%A, %d. %B %Y %I:%M:%S %p")
    relative_time_difference = time.mktime(time.strptime(current_time, "%A, %d. %B %Y %I:%M:%S %p")) - time.mktime(time.strptime(initial_time, "%A, %d. %B %Y %I:%M:%S %p"))
    return jsonify({"relative_time_difference": relative_time_difference, "formatted_time": print_date_time()})


@app.route('/get_token_count', methods=['GET'])
def get_token_count():
    return jsonify({"token_count": count_token()})

@app.route('/get_api_calls', methods=['GET'])
def get_api_calls():
    return jsonify({"total_api_calls": get_total_api_calls()})



if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)

