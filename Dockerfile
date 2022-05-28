FROM python:3.9.10
ENV username="CLaaS_Server"
RUN useradd ${username}

WORKDIR /home/${username}

RUN python -m venv venv

RUN apt-get update && apt-get install -y python3-opencv
RUN pip install opencv-python

RUN venv/bin/pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu113
RUN venv/bin/pip install torchmetrics==0.8.2
RUN venv/bin/pip install pytorchcv==0.0.67
# RUN venv/bin/pip install opencv-python-headless

COPY requirements.txt requirements.txt
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn cryptography

COPY application application
COPY main.py boot.sh ./
RUN mkdir files

COPY .flaskenv .env ./
RUN chmod +x boot.sh

ENV FLASK_APP main.py

RUN chown -R ${username}:${username} ./
USER ${username}

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]