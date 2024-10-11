import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.chains.question_answering import load_qa_chain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate



def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text+=page.extract_text()
    return text

def get_text_chunks(raw_text):
    text_splitter = CharacterTextSplitter(
    separator="\n",
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
    ) 
    chunks = text_splitter.split_text(raw_text)
    return chunks

def get_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store=FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")
    
def get_conversation_chain():
    prompt_template="""
    Answer the question as detailed as possible from the provided context, make sure to provide all the details, 
    if the answer is not in the provided context, just say "answer is not available"
    don't provide wrong answer
    Context:\n{context}?\n
    Question:\n{question}\n
    
    Answer:
    """
    model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.4)
    prompt=PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain
    
def user_input(user_question):
       embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
       
       new_db=FAISS.load_local("faiss_index", embeddings,allow_dangerous_deserialization=True)
       
       docs = new_db.similarity_search(user_question)
       
       chain = get_conversation_chain()
       
       response = chain(
           {"input_documents":docs,
            "question":user_question},
           return_only_outputs=True
       )
       print(response)
       st.write("Reply:", response["output_text"])
    
def main():
    load_dotenv()
    st.set_page_config(page_title="Chat with PDFs", page_icon=":books:")
    st.header("PDF analyzer :books:")
    user_question = st.text_input("Put up your query:")
    
    if user_question:
        user_input(user_question)
    
    
    with st.sidebar:
        st.subheader("Your documents")
        pdf_docs = st.file_uploader("Upload your PDFs here and press and click on process", accept_multiple_files=True)
        if st.button("Process"):
            with st.spinner("Processing"):
                # get the pdf text
                raw_text = get_pdf_text(pdf_docs)
                
                
                #get the text chunks
                text_chunks = get_text_chunks(raw_text)
                
                #create vector store
                get_vector_store(text_chunks)
                st.success("Done")
                
                
                
                

if __name__ == '__main__':
    main()