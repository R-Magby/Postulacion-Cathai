# Postulacion-Cathai
## Como ejecutar el codigo:
Se debe ejecutar DockerDesktop y desde ubuntu ejecutar desde la carpeta que contenga el proyecto para crear los contenedores : `sudo docker-compose build` y luego `sudo docker-compose up -d`, finalmente para ejecutar el proyecto se usa: ` sudo docker exec -it chatbot streamlit run frontend/front.py --server.port=8501 --server.address=0.0.0.0`.
Ya con esto hay que ingresar a la dirreccion: `http://localhost:8501/`

## Acerca del proyecto:
El objetivo era realizar un chatbot que reciba hasta 5 PDFs y te pueda dar respuesta en contexto a esto.
- El codigo **chatbot.py** debe estar en una carpeta llamada backend y el condigo **front.py** en una llamada frontend.
- Para ello utilicé el orquestador LangChain y para el frontend Streamlit.
- Utilice el modelo `llama3.2:1b`, por la razon de que no tengo acceso a openAI (si no hubiera sido mi premara opcion por la cantidad de parametros que maneja), de lo modelos gratuitos es uno de los mejores y ese   modelo en especifico es liviano (1.9 GiB).
- Contiene 3 paginas:
  - Inicio, donde se sube y guardan los pdfs, asu vez se ejecuta una funcion en el backend que genera el retriver (embenddings de los pdfs guardados en la carpeta chroma)
  - Resumen, es una seccion donde contiene resumenes de los pdfs generados por el modelo `llama3.2:1b`.
  - Chatbot, un chat clasico de mensajes entre el assitente y el usuario, contiene una barra lateral donde se ven los archivos y una opcion para eliminarlos de la carpeta, luego un boton `Actualizar` para generar otro retriever, en casos de que se añada otro documento.
- El template del humano contiene los resumenes generados, una variable context (retriever.invoke (pregunta)) y la pregunta.

## Que hay que mejorar.
- Un mejor modelo entregaria mejores respuestas
- Tuve la idea en un inicio de segun el documento identificar la preofesion, el nivel academico o  alguna otra caracteristica del usuario y entregar una respuesta en base a ello.
- Tambien la forma en que probé el modelo fue con articulos cientificos, donde suelen haber muchas formulas y/o graficos, esto es casi incomprensible para el modelo, debido a que la lectura (PyPDFLoader) no reconoce formulas e imagenes, tengo entendido que si existen herramientas para esto.
- El tiempo de ejecucion de las respuesta es lenta, tanto para generar respuesta y para generar el retriver, esto debido a que tiene que buscar en la base de datos, es posible mejorar esto utilizando la GPU o programando en paralelo con la CPU, tambien seria buena idea utillizar mejor el caché.

## Agradecimientos:
Muchas gracias por la oportunidad, me lleve un aprendizaje muy enriquesedor, no habia tenido experiencia usando docker y conectando modelos con streamlit, sinceramente me gustó aprender esto. Muchas gracias, me hubiera encantado seguir y usar todos los dias que me dieron para realizar esto, pero tengo que regresar el computador que utilicé para hacer el proyecto.

Atte: Rodolfo Godoy Arteaga
