# Imagen de la aplicación Streamlit (PMV)
FROM python:3.12.13-slim

WORKDIR /app

# 1) Instalar las librerías
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2) Copiar el código de la aplicación
COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
