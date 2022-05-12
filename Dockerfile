FROM python:3.9.10
ENV username="CLaaS_Server"
RUN useradd ${username}

WORKDIR /home/${username}

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu113
RUN venv/bin/pip install gunicorn pymysql cryptography

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