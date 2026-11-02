FROM python:3.10-slim

WORKDIR /app

# Copia e instala as dependências (utilizando o seu arquivo req.txt)
COPY req.txt .
RUN pip install --no-cache-dir -r req.txt

# Copia o restante do código da aplicação
COPY . .

EXPOSE 5000
CMD ["python", "app.py"]    