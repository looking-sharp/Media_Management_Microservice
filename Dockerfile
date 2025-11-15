FROM python:3.9-slim-buster
WORKDIR /Media_Management_Microservice
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-u", "app.py"]