import os
import openai
import sys
import shutil
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from langchain_community.llms import OpenAI
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings, OpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
import uuid


app = Flask(__name__)
CORS(app)
load_dotenv()
API_KEY = os.getenv('OPENAI_API_KEY')


try:
    path = os.path.dirname(os.path.abspath(__file__))
    upload_folder = os.path.join(path, "tmp")
    os.makedirs(upload_folder, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = upload_folder
except Exception as e:
    app.logger.info("Error in creating upload folder:")
    app.logger.error("Exception occured: {}".format(e))


_chat_history = []


def process_question(question, memory, qa, chat):
    result = qa.invoke({"question": question, "chat_history": chat})

    return result


def process_pdf_file(pdf_file, pdf_file_name):
    loader = PyPDFLoader(pdf_file)

    pages = loader.load()
    return pages


def initialize_memory():
    memory = ConversationBufferMemory(
        memory_key="chat_history",  # chat history is a lsit of messages
        return_messages=True,
    )
    return memory


def initialize_qa(llm, vectordb, qa_prompt):
    qa = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectordb.as_retriever(
            search_type="similarity", search_kwargs={"k": 4}),
        combine_docs_chain_kwargs={"prompt": qa_prompt},
        return_source_documents=True
    )
    return qa


@app.route('/process_pdf', methods=['POST', 'GET'])
def process_pdf():
    pdf_file = request.files.get('file')
    print("primary", pdf_file)
    if pdf_file is not None:
        try:
            print(pdf_file)
            save_path = os.path.join(
                app.config.get('UPLOAD_FOLDER'), "temp.pdf")
            pdf_file.save(save_path)
            pdf_file_name = pdf_file.filename.split(".")

            pages = process_pdf_file(save_path, pdf_file_name)

            # end of loading
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=400,
                chunk_overlap=200
            )
            chunks = text_splitter.split_documents(pages)

            persist_directory = "./docs/chroma" + pdf_file_name[0]
            print("upload", persist_directory)
            if os.path.exists(persist_directory):
                print("hey I exist")
                vectordb = Chroma(persist_directory=persist_directory,
                                  embedding_function=OpenAIEmbeddings())
                print("hey i just loaded", vectordb)
            else:
                vectordb = Chroma.from_documents(
                    documents=chunks,
                    embedding=OpenAIEmbeddings(),
                    persist_directory=persist_directory
                )
                vectordb.persist()

            memory = initialize_memory()

            QA_prompt = PromptTemplate(template="""You are a PDF reader assistant. Given a question: {question} with the {chat_history} and a context: {context}, 
                            If the context does not provide any answer to the question, respond only with
                            'The information is not found in the PDF.', nothing else. if information is there
                            provide a short answer from the context that addresses the question. """, input_variables=["question", "chat_history", "context"]
                                       )

            llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
            qa = initialize_qa(llm, vectordb, QA_prompt)

            question = request.form.get('question')

            if question.lower() in ["exit", "bye", "leave", "end"]:
                _chat_history.clear()
                shutil.rmtree("./docs")
                chat = ""
                return jsonify({'statusCode': 200, "chat": _chat_history})

            chat = memory.load_memory_variables({})["chat_history"]
            result = process_question(question, memory, qa, chat)
            print(result)
            source_docs = result["source_documents"]

            page_nums = source_docs[0].metadata["page"]

            if "The information is not found in the PDF." in result["answer"]:
                pdf_file = ''
                page_nums = ""
                pdf_file = None
                _chat_history.append(
                    {"question": question, "answer": result["answer"], "page": page_nums, "pdf_file_name": pdf_file_name})
            else:
                pdf_file = None
                _chat_history.append(
                    {"question": question, "answer": result["answer"], "page": page_nums + 1, "pdf_file_name": pdf_file_name[0]})
                print("Chat History:", _chat_history)

            return jsonify(
                {'statusCode': 200,
                 "chat": _chat_history}
            )
        except Exception as e:
            return jsonify({'statusCode': 400, 'error': 'Invalid PDF'})
    else:
        print("Hi, No PDF")
        _default_pdf = "/Users/hninlwin/llm-test-2/flask-server/purposes-of-syllabus.pdf"

        pages = process_pdf_file(_default_pdf, "default")

        # end of loading

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=200
        )
        chunks = text_splitter.split_documents(pages)

        persist_directory = "./docs/chroma" + "default"

        if os.path.exists(persist_directory):
            vectordb = Chroma(persist_directory=persist_directory,
                              embedding_function=OpenAIEmbeddings())
        else:
            vectordb = Chroma.from_documents(
                documents=chunks,
                embedding=OpenAIEmbeddings(),
                persist_directory=persist_directory
            )
            vectordb.persist()

        memory = initialize_memory()

        QA_prompt = PromptTemplate(
            template="""You are a PDF reader assistant. Given a question: {question} with the {chat_history} and a context: {context}, 
                                provide a short answer from the context that addresses the question.
                                If the context does not provide any answer to the question, respond with 
                                'The information is not found in the PDF.' """, input_variables=["question", "chat_history", "context"]
        )
        llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
        qa = initialize_qa(llm, vectordb, QA_prompt)

        question = request.form.get('question')

        if question.lower() in ["exit", "bye", "leave", "end"]:
            _chat_history.clear()
            shutil.rmtree("./docs")
            chat = ""
            return jsonify({'statusCode': 200, "chat": _chat_history})
        chat = memory.load_memory_variables({})["chat_history"]
        result = process_question(question, memory, qa, chat)
        print(result)
        source_docs = result["source_documents"]

        try:
            page_nums = source_docs[0].metadata["page"]
        except Exception as e:
            page_nums = 0
            print("Error: out of index")

        if result["answer"] == "The information is not found in the PDF.":
            page_nums = ""
            pdf_file_name = ""
            _chat_history.append(
                {"question": question, "answer": result["answer"], "page": page_nums, "pdf_file_name": pdf_file_name})
        else:
            _chat_history.append(
                {"question": question, "answer": result["answer"], "page": page_nums + 1, "pdf_file_name": "Purpose of Syllabus"})
            print("Chat History:", _chat_history)

        return jsonify(
            {'statusCode': 200,
             "chat": _chat_history}
        )


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)



