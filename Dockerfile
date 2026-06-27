FROM ubuntu:22.04

# This fix: libGL error: No matching fbConfigs or visuals found
ENV LIBGL_ALWAYS_INDIRECT=1
# Suppress tzdata interactive prompt
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC
# Install Python 3, PyQt5
RUN apt-get update && apt-get install -y python3-opencv python3-pip python3-pyqt5
# Create and set workdir
WORKDIR /app
# Copy source file into workdir
COPY ./src/ ./

RUN pip3 install -r requirements.txt

CMD ["python3", "main.py"]
