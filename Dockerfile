FROM python:3.9

ENV HOME=/opt/opt

ENV DEPLOY=1

WORKDIR $HOME

COPY requirements.txt $HOME

RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

COPY . $HOME

EXPOSE 80

CMD ["sh", "start.sh"]
