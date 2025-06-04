FROM public.ecr.aws/lambda/python:3.12

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip3 install -r requirements.txt

COPY . .

CMD ["app.lambda_handler"]