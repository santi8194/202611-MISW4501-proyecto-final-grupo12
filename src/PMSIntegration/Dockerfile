# Imagen base liviana
FROM python:3.11-slim

# Variables para evitar problemas de buffering
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo
WORKDIR /app

RUN mkdir -p /app/data

# Copiamos requirements primero (cache eficiente)
COPY requirements.txt .

# Instalamos dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del proyecto
COPY . .

# Exponemos puerto
EXPOSE 8001

# Comando para ejecutar el servicio
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]