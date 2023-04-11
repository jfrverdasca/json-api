FROM python:3.11.0-alpine3.16
ADD . /server
WORKDIR /server
RUN pip3 install -r requirements.txt

# Cannot simply run the command to run the python application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]