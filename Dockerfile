FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 DADOS_DIR=/dados TZ=America/Sao_Paulo
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd -m escola && mkdir /dados && chown escola /dados
USER escola
VOLUME /dados
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/login')"
CMD ["python", "app.py"]
