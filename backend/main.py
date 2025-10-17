import os
import stat
import shutil
import git # You might need to run: pip install GitPython
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# --- LangChain Imports ---
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter, Language
from langchain.chains import RetrievalQA

# --- Environment Variables ---
from dotenv import load_dotenv
load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

# --- FastAPI App Initialization ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def remove_readonly(func, path, excinfo):
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWRITE)
        func(path)
    else:
        raise

# --- Data Models ---
class RepoURL(BaseModel):
    url: str

class ChatMessage(BaseModel):
    question: str

# --- API Endpoint to Analyze Repo ---
@app.post("/analyze")
def analyze_repo(repo_url: RepoURL):
    repo_path = "./temp_repo"
    db_path = "./chroma_db"

    try:
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path, onerror=remove_readonly)
        if os.path.exists(db_path):
            shutil.rmtree(db_path, onerror=remove_readonly)

        print(f"Cloning repo: {repo_url.url}")
        git.Repo.clone_from(repo_url.url, to_path=repo_path)
        print("Repo cloned successfully.")

        # --- UPGRADE #1: Better Document Filtering ---
        print("Loading and filtering documents...")
        all_docs = []
        # List of file extensions to load and directories to ignore
        allowed_extensions = ['.py', '.js', '.ts', '.md', '.html', '.css', '.java', '.cpp']
        ignored_dirs = ['.git', 'node_modules', '__pycache__']

        for root, dirs, files in os.walk(repo_path):
            # Modify dirs in-place to prevent os.walk from traversing them
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            
            for file in files:
                if any(file.endswith(ext) for ext in allowed_extensions):
                    file_path = os.path.join(root, file)
                    try:
                        loader = TextLoader(file_path, encoding='utf-8')
                        all_docs.extend(loader.load())
                    except Exception as e:
                        print(f"Skipping file {file_path} due to error: {e}")

        print(f"Loaded {len(all_docs)} relevant documents.")

        # --- UPGRADE #2: Smarter, Language-Aware Chunking ---
        # Using a general splitter that handles multiple languages
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.split_documents(all_docs)
        print(f"Split into {len(texts)} chunks.")

        print("Initializing Hugging Face local embeddings...")
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        print("Embeddings model loaded.")

        db = Chroma.from_documents(texts, embeddings, persist_directory=db_path)
        print("Vector database created successfully.")

        return {"message": "Repository analyzed and indexed successfully. Ready to chat."}

    except Exception as e:
        print(f"An error occurred during analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- API Endpoint for Chat (Updated Logic) ---
@app.post("/chat")
def chat_with_repo(message: ChatMessage):
    db_path = "./chroma_db"

    if not os.path.exists(db_path):
        raise HTTPException(status_code=400, detail="Repository not analyzed yet. Please analyze a repository first.")

    try:
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        db = Chroma(persist_directory=db_path, embedding_function=embeddings)

        # --- UPGRADE #3: Widen the Net for More Context ---
        retriever = db.as_retriever(search_kwargs={"k": 7})

        # --- UPGRADE #4: Give the AI Better Instructions ---
        prompt_template = """
        You are an expert programming assistant. Use the following pieces of context from a codebase to answer the user's question.
        Your goal is to provide a helpful and accurate summary or explanation based ONLY on the provided code context.
        If you don't know the answer from the context, just say that you don't have enough information from the codebase to answer.
        Do not try to make up an answer or use external knowledge.

        Context:
        {context}

        User Question: {question}
        Helpful Answer:
        """
        PROMPT = PromptTemplate(
            template=prompt_template, input_variables=["context", "question"]
        )

        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash") # Using gemini-pro for robust answers
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": PROMPT},
            return_source_documents=True # Optional: helps in debugging
        )

        # Use the dictionary-based call for the chain
        result = qa_chain.invoke({"query": message.question})
        
        print(f"Retrieved {len(result['source_documents'])} source documents for the query.")
        return {"answer": result['result']}

    except Exception as e:
        print(f"An error occurred during chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def read_root():
    return {"message": "Codebase Companion Backend is running!"}