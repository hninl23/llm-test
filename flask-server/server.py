import os
from langchain.chains import RetrievalQA
from langchain_community.llms import OpenAI
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from flask_cors import CORS 
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_openai import OpenAIEmbeddings
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
import openai
import sys
import shutil

app = Flask(__name__)
CORS(app)
load_dotenv()
API_KEY = os.getenv('OPENAI_API_KEY')

from langchain_openai import OpenAI
from langchain.chains import ConversationChain
try:
    path = os.path.dirname(os.path.abspath(__file__))
    upload_folder = os.path.join(path, "tmp")
    os.makedirs(upload_folder, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = upload_folder
except Exception as e:
    app.logger.info("Error in creating upload folder:")
    app.logger.error("Exception occured: {}".format(e))

_chat_history = []
@app.route('/process_pdf', methods=['POST', 'GET'])
def process_pdf():

    pdf_file = request.files['file']
    if pdf_file is not None:

        save_path = os.path.join(app.config.get('UPLOAD_FOLDER'), "temp.pdf")

        pdf_file.save(save_path)

        loader = PyPDFLoader(save_path)

        pages = loader.load()
        print(pages)
        ##end of loading

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=200
        )
        chunks = text_splitter.split_documents(pages)
        
        vectordb = Chroma.from_documents (
            documents=chunks,
            embedding=OpenAIEmbeddings(),
            persist_directory="./data"
        )
        memory = ConversationBufferMemory(
            memory_key="chat_history", #chat history is a lsit of messages
            return_messages=True,
        )
        print("inside1")
        QA_prompt = PromptTemplate(
            template= """You are a PDF reader assistant. Given a question: {question} with the {chat_history} and a context: {context}, provide a short answer from the context that addresses the question.
                         If the context does not provide any answer to the question, respond with 'The information is not found in the PDF' """, input_variables=["question","chat_history", "context"]
        )
        print("inside2")

       
        qa = ConversationalRetrievalChain.from_llm(
            llm=ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0),
            retriever=vectordb.as_retriever(search_type="similarity", search_kwargs={"k": 4}),
            # memory=memory,
            response_if_no_docs_found="The answer is not provided in the PDF",
            combine_docs_chain_kwargs={"prompt": QA_prompt},
            return_source_documents= True
            
        )
        print("inside3")

        question = request.form.get('question')
        print("inside4")
        chat = memory.load_memory_variables({})["chat_history"]
        result = qa.invoke({"question": question, "chat_history": chat}) 
        source_docs = result["source_documents"]
        page_nums = source_docs[0].metadata["page"]
        if result["answer"] == "The information is not found in the PDF.":
            page_nums = ""
        print("Page", page_nums)
        print("inside5")
        print(result)


        chat = memory.load_memory_variables({})["chat_history"]
        print("Before9:" , chat)
        if question.lower() in ["exit", "bye", "leave"]:
            _chat_history.clear() 
            shutil.rmtree("./data")
            return jsonify({'statusCode': 200, "chat": _chat_history})
            
        _chat_history.append({"question": question, "answer": result["answer"], "page": page_nums})
        print("Chat History:", _chat_history)

        return jsonify(
            {'statusCode': 200,
            "chat": _chat_history}
        )
    else:
        return jsonify({'statusCode': 400, 'error': 'PDF file not provided'})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)



