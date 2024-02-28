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


@app.route('/process_pdf', methods=['POST', 'GET'])
def process_pdf():

    pdf_file = request.files['file']
    if pdf_file is not None:

        save_path = os.path.join(app.config.get('UPLOAD_FOLDER'), "temp.pdf")

        pdf_file.save(save_path)

        loader = PyPDFLoader(save_path)

        pages = loader.load()
        print(pages)
        # end of loading

        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=400,
                chunk_overlap=200
            )
            chunks = text_splitter.split_documents(pages)
        except ValueError as e:
            print("Invalid chunk_size(chunk_size must be > 0) | Invalid chunk overlap (overlap must be > 0 && > chunk_size)", e)
        except TypeError as e:
            print("Pages arugment is not a PyPDFLoader Object ", e)
        except AttributeError as e:
            print(
                "Text splitter object is not a 'RecursiveCharacterTextSplitter' object", e)
        except Exception as e:
            print("Text Splitting Failed", e)

        try:
            vectordb = Chroma.from_documents(
                documents=chunks,
                embedding=OpenAIEmbeddings(),
                persist_directory="./data"
            )
        except ValueError as e:
            vectordb = {}
            print("Chunks is not document object", e)
        except TypeError as e:
            vectordb = {}
            print("Current embedding is not an embedding object ", e)
        except AttributeError as e:
            vectordb = {}
            print("Chroma DB does not have 'from_documents' method", e)
        except Exception as e:
            vectordb = {}
            print("Unable to create Vector DB", e)

        try:
            memory = ConversationBufferMemory(
                memory_key="chat_history",  # chat history is a lsit of messages
                return_messages=True,
            )
        except ValueError as e:
            memory = {}
            print("Please define the memeory_key string", e)
        except TypeError as e:
            memory = {}
            print("Memory Key or return_message not returning the correct type", e)
        except Exception as e:
            memory = {}
            print("Unable to load memory", e)

        try:
            QA_prompt = PromptTemplate(
                template="""You are a PDF reader assistant. Given a question: {question} with the {chat_history} and a context: {context}, 
                                provide a short answer from the context that addresses the question.
                                If the context does not provide any answer to the question, respond with 
                                'The information is not found in the PDF' """, input_variables=["question", "chat_history", "context"]
            )
        except ValueError as e:
            print(
                "Expected inputs [question, chat_history, context] not found", e)
        except Exception as e:
            print("Unable to use QA Prompt", e)

        try:
            qa = ConversationalRetrievalChain.from_llm(
                llm=ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0),
                retriever=vectordb.as_retriever(
                    search_type="similarity", search_kwargs={"k": 4}),
                combine_docs_chain_kwargs={"prompt": QA_prompt},
                return_source_documents=True
            )
        except ImportError as e:
            print("Error: Unable to import all necessary modules.")
        except Exception as e:
            qa = None
            print(
                "Error: An unexpected error occurred while initializing ConversationalRetrievalChain.", e)

        try:
            question = request.form.get('question')
        except TypeError as e:
            question = ""
            print("Form data not in expected format")
        except KeyError as e:
            question = ""
            print("Key 'question' not found in Form Data")
        except Exception as e:
            question = ""
            print("Unable to retrieve question", e)

        if question.lower() in ["exit", "bye", "leave"]:
            _chat_history.clear()
            shutil.rmtree("./data")
            chat = ""
            return jsonify({'statusCode': 200, "chat": _chat_history})

        try:
            chat = memory.load_memory_variables({})["chat_history"]
            print("chat:", chat)
        except KeyError as e:
            chat = []
            print("Unable to retrieve the key 'chat_history'", e)
        except AttributeError as e:
            chat = []
            print("Memory Object does not have 'load_memory_variables' method", e)
        except Exception as e:
            chat = []
            print("Unable to retrieve chat_history memory", e)

        try:
            result = qa.invoke({"question": question, "chat_history": chat})
            print("Result:", result)
        except AttributeError as e:
            result = {}
            print("Memory Object does not have 'load_memory_variables' method", e)
        except Exception as e:
            result = {}
            print("Error invoking QA", e)

        try:
            source_docs = result["source_documents"]
        except KeyError as e:
            source_docs = ""
            print("Key 'source_documents' not found in the result dictionary", e)
        except Exception as e:
            source_docs = ""
            print("Unable to retrieve source document", e)

        try:
            page_nums = source_docs[0].metadata["page"]
        except KeyError as e:
            page_nums = ""
            print("Key 'page' not found in the metadata of soruce docs[0]", e)
        except Exception as e:
            page_nums = ""
            print("Unable to retrieve page number", e)

        try:
            if result["answer"] == "The information is not found in the PDF.":
                page_nums = ""
                _chat_history.append(
                    {"question": question, "answer": result["answer"], "page": page_nums})
            else:
                _chat_history.append(
                    {"question": question, "answer": result["answer"], "page": page_nums + 1})
                print("Chat History:", _chat_history)
        except KeyError as e:
            _chat_history = []
            print("Key 'answer' not found in the dictionary result", e)
        except Exception as e:
            _chat_history = []
            print("Unable to append to chat history", e)

        return jsonify(
            {'statusCode': 200,
             "chat": _chat_history}
        )
    else:
        return jsonify({'statusCode': 400, 'error': 'PDF file not provided'})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)



