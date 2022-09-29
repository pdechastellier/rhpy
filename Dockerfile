FROM python:3.11.0rc2-slim

## wget not included in slim image
RUN apt-get -y update
RUN apt-get -y install wget gnupg

## install google chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /usr/share/keyrings/google-chrome.gpg
RUN sh -c 'echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'

RUN apt-get -y update
RUN apt-get install -y google-chrome-stable

## install chromedriver
RUN apt-get install -yqq unzip
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`wget -qO- chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/
ENV DISPLAY=:99

COPY requirements.txt /wd/
COPY src/  /wd/src/
WORKDIR /wd

RUN pip install --no-cache-dir -r /wd/requirements.txt --upgrade
CMD ["python", "./src/cli-parser.py"]