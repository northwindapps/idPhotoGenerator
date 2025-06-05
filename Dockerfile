FROM public.ecr.aws/lambda/python:3.9

ENV NUMBA_CACHE_DIR=/tmp
ENV XDG_CACHE_HOME=/tmp
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip3 install -r requirements.txt

COPY . .

# Explicitly ensure the ONNX file is copied (if not already in your repo root)
# COPY u2net_human_seg.onnx /var/task/u2net_human_seg.onnx

CMD ["app.lambda_handler"]

# FROM python:3.9-slim

# WORKDIR /app

# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# COPY . .

# ENV FLASK_APP=app.py
# CMD ["flask", "run", "--host=0.0.0.0"]
