FROM python:3.10
WORKDIR /app


ADD . .
RUN pip3 install --upgrade pip
RUN pip3 install --upgrade setuptools
RUN pip3 install -r requirements.txt
ENTRYPOINT ["python3", "main.py"]