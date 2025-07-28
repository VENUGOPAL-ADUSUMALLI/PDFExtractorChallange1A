FROM python:3.11-slim

WORKDIR /Challange_1a
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "simple_pdf_extractor.py"]
