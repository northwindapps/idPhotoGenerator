FROM public.ecr.aws/lambda/python:3.9

ENV NUMBA_CACHE_DIR=/tmp
ENV XDG_CACHE_HOME=/tmp
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip3 install -r requirements.txt

# 🔥 Pre-download rembg model here (KEY STEP!)
# RUN python3 -c "from rembg import new_session; new_session('isnet-general-use')"

COPY . .

CMD ["app.lambda_handler"]