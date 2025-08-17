FROM python:3.11-slim
WORKDIR /chatbot


COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt


COPY . /chatbot

# instalar Ollama

# exponer puertos
EXPOSE 8000

# levantar Ollama y ejecutar tu script
#CMD ["python", "chatbot.py"]
CMD ["tail", "-f", "/dev/null"]