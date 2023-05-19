FROM python:3.9

ENV HOME=/opt/opt

ENV DEPLOY=1

WORKDIR $HOME

COPY requirements.txt $HOME

RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

RUN python -c "import synonyms"

RUN python -c "import pycorrector; pycorrector.correct('少先队员因该为老人让坐'); pycorrector.en_correct('falut text')"

RUN pip install imageio[ffmpeg]

ENV IMAGEIO_FFMPEG_EXE=/usr/local/lib/python3.9/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux64-v4.2.2

COPY . $HOME

EXPOSE 80

CMD ["sh", "start.sh"]
