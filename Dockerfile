FROM python:3.10
WORKDIR /opt/app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN apt update && apt install zip
EXPOSE 8080:8080
COPY . .
CMD ["python3","server.py"]