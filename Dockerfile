FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    recutils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt awscli

COPY . .

# download->run->upload
CMD aws s3 cp s3://test-34555454545/tasks.rec . && python app.py && aws s3 cp tasks.rec s3://test-34555454545/tasks.rec

