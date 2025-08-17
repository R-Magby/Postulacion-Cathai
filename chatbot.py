import sys
from langchain_community.document_loaders import PyPDFLoader

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
#from langchain.chains import RetrievalQA

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate, HumanMessagePromptTemplate,SystemMessagePromptTemplate, ChatPromptTemplate
from langchain.schema import Document
import os
# ------------------- Func PDFs ----------------------
'''
def encontrar_palabra(docs,page,palabra):
  cadena_de_texto = docs.page_content
  try:
    id_abstract = cadena_de_texto.lower().find(palabra)
    return page
  except Exception as e:
      return None 
0'''
# Hacer todo minusculas


# ------------------- SUBIR PDFs ----------------------
def update_retriver():
  # Esta funcion desarrolla los embeddings de los pdfs.


  folder_path = "/data/dir_pdfs"
  if len(os.listdir(folder_path)) > 0:
    lista_docs = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]
    lista_docs = lista_docs[:5] 

    doc_temp = []
    page_importantes = []

    #Lectura de documentos
    for id,name in enumerate(lista_docs):
      loader = PyPDFLoader( os.path.join("/data/dir_pdfs", name) )
      documents = loader.load() 

      num_pages = len(documents)
      if num_pages > 50:
          print(f"PDF demasiado largo: {num_pages} páginas.")
          sys.exit()
      else:
          print(f"id: {id}, {num_pages} páginas. OK.")
          for i, doc in enumerate(documents):

            if i==0:
              titulo = doc.metadata.get("title","Desconocido").lower()
            doc_temp.append(Document(page_content=doc.page_content, metadata={"source": name,"page": i,"title":titulo}))

          '''  for word in ["abstract","introduccion","introduction","conclusion"]:
              page_importantes.append(encontrar_palabra(doc,i,word))'''

    # ------------------- retriever ----------------------

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000,chunk_overlap=400)
    chunks = text_splitter.split_documents(doc_temp)
    print(f"Chunks generados: {len(chunks)}")
    embedding_model = HuggingFaceEmbeddings(model_name="paraphrase-multilingual-MiniLM-L12-v2")
    vectorstore = Chroma(persist_directory="/data/chroma", embedding_function=embedding_model)
    vectorstore.add_documents(chunks)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    #El proceso es lento, pero para que el modelo arroje resultados buenos, es mejor dejar con 2000 palabras por chunks y un k = 5, esto se puede optimizar.

    return retriever
  else:
    return None   


def generar_resumen():
  #Esta funcion genera resumenes llamando al modelos llama3.2:1b

  folder_path = "/data/dir_pdfs"
  if len(os.listdir(folder_path)) > 0:
    lista_docs = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]
    lista_docs = lista_docs[:5] 

    resumen = []
    query = "Segun las paginas indicadas genera un resumen"
    for id,name in enumerate(lista_docs):
      loader = PyPDFLoader( os.path.join("/data/dir_pdfs", name) )
      temp = loader.load() 

      #documentos contiene string de las 3 primeras paginas o en caso de que sean pocas, todas las paginas.
      if len(temp)>3:
        documentos = temp[0].page_content + temp[1].page_content + temp[2].page_content
      else:
        documentos = " ".join([doc.page_content for doc in temp])

      llm = ChatOllama(model="llama3.2:1b",base_url="http://llama:11434" )

      template = """
      Basado en las siguientes paginas, genera un resumen.
      Tiene que ser menos de 20 lineas y se lo mas claro posible.
      Si no puedes encontrar las paginas, indica que la información no está disponible.

      Paginas:
      {context}

      Pregunta:
      {question}

      Respuesta:
      """

      prompt_human = PromptTemplate(template=template, input_variables=["context", "question"])
      template_humano = HumanMessagePromptTemplate(prompt = prompt_human)

      template_temp= """Eres un sistema de analista de documentos, tu objetivo es entregar un resumen de un texto de manera clara.
                        Se te proprocionara las primeras paginas de un documento.
                        Prioriza el texto siguiente cuando identifiques palabras como introduccion, Abstract, introducction y conclusion,
                        te puede entregar informacion relevante."""

      promp_System = PromptTemplate(template=template_temp)
      template_System = SystemMessagePromptTemplate(prompt = promp_System)

      # ------------------- CHAIN ----------------------
      chat_prompt = ChatPromptTemplate.from_messages([template_System,template_humano])
      propmt_value = chat_prompt.format_prompt(context = documentos, question = query).to_messages()

      llm_chain = chat_prompt | llm
      resp = llm_chain.invoke({"context": documentos, "question": query})

      #Guardamos los resumenes generados por el modelo LLM
      resumen.append(resp.content)

    return resumen
  else:
    return None




def respuesta_bot(query,retriever):
    
  # ------------------- CHAT BOT LLAMA ----------------------

  llm = ChatOllama(model="llama3.2:1b",base_url="http://llama:11434" )

  # ------------------- RETRIEVER ----------------------

  relevant_docs = retriever.invoke( query)
  context = "\n".join([f"[source: {doc.metadata.get('source', 'desconocido')},page: {doc.metadata.get('page', 'desconocido')},title:{doc.metadata.get('title','Desconocido')}]\n{doc.page_content}" for doc in relevant_docs])


  #Se escogio ese modelo por lo liviano (1.9 GiB), contiene pocos parametros comparados con llama3 o chatgpt
  return llm, context

