FROM python:3.9

ENV HOME=/opt/opt

ENV DEPLOY=1

WORKDIR $HOME

COPY requirements.txt $HOME

RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

RUN pip install imageio[ffmpeg]

ENV IMAGEIO_FFMPEG_EXE=/usr/local/lib/python3.9/site-packages/imageio_ffmpeg/binaries/ffmpeg-linuxaarch64-v4.2.2

COPY . $HOME

EXPOSE 80

CMD ["sh", "start.sh"]
