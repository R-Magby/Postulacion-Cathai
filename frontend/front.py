
import streamlit as st
import os
import sys
import shutil

sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))
import chatbot as cb
import importlib
importlib.reload(cb)

class ChatBotApp:
    def __init__(self):

        if "retriever" not in st.session_state:
            st.session_state.retriever = 0
        self.retriever = st.session_state.retriever 
        if "page" not in st.session_state:
            st.session_state.page = "inicio"
        self.page = st.session_state.page

    def guardar_pdfs_dir(self,archivos):
        #Esta funcion guarda los pdfs en un directorio y genera un retriver

        #primero eliminamos los pdfs antiguos. Esto se hace solamente en la pagina inicio.
        # ----- Limpiar ------
        for f in os.listdir("/data/dir_pdfs"):
            file_dir = os.path.join("/data/dir_pdfs", f)
            try:
                os.unlink(file_dir)
            except Exception as e:
                print(f"Error al borrar {file_dir}: {e}")

        # ----- Guardar ------
        if len(archivos) == 0:
            with open(os.path.join("/data/dir_pdfs",archivos.name),"wb") as f:
                f.write(archivos.getbuffer())
        else:
            for i in range(len(archivos)):
                with open(os.path.join("/data/dir_pdfs",archivos[i].name),"wb") as f:
                    f.write(archivos[i].getbuffer())
        st.success(f"Archivos guardados")

        # generar retriver (embeddings de los pdfs)
        temp = cb.update_retriver()
        return temp


    def actualizar(self,archivos):

        #La funcion actualiza los retriver, se añaden pdfs nuevos y llama al backend.
        if len(archivos) == 0:
            with open(os.path.join("/data/dir_pdfs",archivos.name),"wb") as f:
                f.write(archivos.getbuffer())
        else:
            for i in range(len(archivos)):
                with open(os.path.join("/data/dir_pdfs",archivos[i].name),"wb") as f:
                    f.write(archivos[i].getbuffer())
        
        st.sidebar.success(f"Archivos actualizado")
        st.session_state.pdf_update_key += 1 
        with st.spinner("Generando el nuevo retriver...", show_time=True):
            temp = cb.update_retriver()
        return temp

    def validar_limite_archivos(self):
        # Funcion para on_changes de la subida de documentos, verifica si estas subiendo mas de 5 pdfs, se reinicia el st.session_state.pdf_uploader_key

        if "pdf_uploader_key" in st.session_state:
            # ---- inicio -----
            key = f"pdfs_upload_{st.session_state.pdf_uploader_key}"
            archivos = st.session_state.get(key, [])
            if len(archivos) > 5:
                st.error("¡Límite excedido! Por favor, sube 5 archivos o menos.")
                st.session_state.pdf_uploader_key += 1 

        if "pdf_update_key" in st.session_state:
            # ---- chatbot -----
            key = f"pdfs_update_{st.session_state.pdf_update_key}"
            archivos = st.session_state.get(key, [])
            if len(archivos) > 5:
                st.error("¡Límite excedido! Por favor, sube 5 archivos o menos.")
                st.session_state.pdf_update_key += 1 

        

    def pagina_chatbot(self):

        #Botones de vovler al inicio o ir a leer los resumenes
        inicio, resumen = st.columns(2)
        if inicio.button("Volver"):
            st.session_state.page = "inicio"
            st.rerun()
        if resumen.button("Resumen"):
            st.session_state.page = "resumen"
            st.rerun()

        st.title("Chat Bot bib bob")


        #----------------- sidebar -----------------

        #Barra lateral para actualizar los documentos.
        if "pdf_update_key" not in st.session_state:    
            st.session_state.pdf_update_key = 0

        st.sidebar.header("Archivos")
        archivo = st.sidebar.file_uploader("Sube los PDFs", type = ["pdf"], accept_multiple_files = True, key=f"pdfs_update_{st.session_state.pdf_update_key}",on_change=self.validar_limite_archivos)
        pdf_files = os.listdir("/data/dir_pdfs")
        for pdf in pdf_files:
            col1, col2 = st.sidebar.columns([4, 1])
            col1.write(pdf)
        
        # Opcionde eleminar los pdfs con una X.
            if col2.button("❌", key=pdf):
                os.remove(os.path.join("/data/dir_pdfs", pdf))
                st.rerun()


        # Boton de actualizar
        archivos_validos = archivo is not None and 0 < len(archivo) <= 5
        if st.sidebar.button("Actualizar",disabled=not archivos_validos):
            st.session_state.retriever = self.actualizar(archivo)
            self.retriever = st.session_state.retriever
            st.session_state.resumen = cb.generar_resumen()

            st.rerun()


        #----------------- chat -----------------

        # Generamos los template
        template_system = """   Eres un sistema de analista de documentos, tu funcion es leer y analisar los documentos enviados y responder las preguntas del usuario. 
                                Se te proporcionara Resumen de los documentos enviados, contexto de las paginas necesarias para la respuesta y la pregunta.
                                El resumen y el context es una ayuda.  """

        template_human = """    Basado en la informacion dada, responde a la pregunta.
                                Si no puedes encontrar la respuesta en el context o resumen, indica que la información no está disponible, pero en casos en que uno de ellos te sea util para la respuesta
                                no menciones que falta informacion.

                                Resumen:
                                {resumen}

                                Context:
                                {context}

                                Pregunta:
                                {question}

                                Respuesta:
                                """
        
        # Se guardan los mensajes para el modelo
        if "messages_model" not in st.session_state:
            st.session_state.messages_model = []

        # Registro de los mensajes del chat, esto para que no se muestre el template en el chat   
        if "messages_chat" not in st.session_state:
            st.session_state.messages_chat = []

        # Guaedamos el rol del sistema
        if "system" not in st.session_state:
            st.session_state.system = [{"role":"system","content":template_system}]

        for msj in st.session_state.messages_chat:
            with st.chat_message(msj["role"]):
                st.markdown(msj["content"])
        
        if prompt := st.chat_input("Consulta..."):
            #Mensaje del ususario
            with st.chat_message("user"):
                st.markdown(prompt)

            #mensaje del chatbot
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                with st.spinner("Pensando..."):
                    robot_dice = cb.respuesta_bot(prompt, self.retriever)

                respuesta = ""
                # Guardamos en la memoria del modelo la pregunta del ususario
                if robot_dice[0] is not None:   
                    llm, content = robot_dice 
                    st.session_state.messages_model.append({"role":"user","content":template_human.format(resumen=st.session_state.resumen ,context=content ,question=prompt)})
                    st.session_state.messages_chat.append({"role":"user","content":prompt})
                #historial de la conversacion, variable para el .invoke()
                historial = st.session_state.system + st.session_state.messages_model

                for i in llm.stream(historial):
                    if i.content is not None:
                        respuesta += i.content
                        message_placeholder.markdown(respuesta)

                # guardar mensaje del bot.
                st.session_state.messages_model.append({"role":"assistant","content":respuesta})
                st.session_state.messages_chat.append({"role":"assistant","content":respuesta})




    def pagina_resumen(self):
        volver, chat = st.columns(2)
        if volver.button("Volver"):
            st.session_state.page = "inicio"
            st.rerun()
        if chat.button("Chatbot"):
            st.session_state.page = "chatbot"
            st.rerun()

        st.write("Resumen ")
        st.header("Informacion de los documentos dados por el chatbot")

        if "resumen" not in st.session_state:
            st.session_state.resumen = ""

        pdf_files = os.listdir("/data/dir_pdfs")
        col1, col2 = st.columns([2, 5])
        for id,pdf in enumerate(pdf_files):
            if col1.button(pdf):
                col2.write( st.session_state.resumen[id] )
        



    def pagina_inicial(self):

        #variables para subir resumenes y documentos.
        if "pdf_uploader_key" not in st.session_state:
            st.session_state.pdf_uploader_key = 0
        if "resuemn" not in st.session_state:
            st.session_state.resumen = ""
        st.title("Chat Bot para el analisis de documentos")

        st.write("Sube 5 archivos o menos")

        # subida de documentos
        archivo = st.file_uploader("Sube los PDFs", type = ["pdf"], accept_multiple_files = True, key=f"pdfs_upload_{st.session_state.pdf_uploader_key}",on_change=self.validar_limite_archivos)
        archivos_validos = archivo is not None and 0 < len(archivo) <= 5

        # Este boton te envia a la pagina del chatbot
        if st.button("Iniciar Chat",disabled=not archivos_validos):
            with st.spinner("Generando el retriver...", show_time=True):
                st.session_state.retriever = self.guardar_pdfs_dir(archivo)
                self.retriever = st.session_state.retriever
                st.session_state.resumen = cb.generar_resumen()
            st.session_state.page = "chatbot"
            st.rerun()

        # Este boron te envia a una pagina que contiene los resumenes de los textos
        if st.button("Ver resumen",disabled=not archivos_validos):
            with st.spinner("Generando el retriver...", show_time=True):
                st.session_state.retriever = self.guardar_pdfs_dir(archivo)
                self.retriever = st.session_state.retriever
                st.session_state.resumen = cb.generar_resumen()
            st.session_state.page = "resumen"
            st.rerun()

    def run(self):
        #Seccion de paginas
        self.page = st.session_state.page
        if self.page == "inicio":
            self.pagina_inicial()
        elif self.page == "chatbot":
            self.pagina_chatbot()
        elif self.page == "resumen":
            self.pagina_resumen()
            
if __name__ == "__main__":
    app = ChatBotApp()
    app.run()


#Muchas gracias por leer el documento.
#Atte: Rodolfo Godoy Arteaga.

#cual es el titulo del documento? tambien dime quien o quienes lo escribieron
