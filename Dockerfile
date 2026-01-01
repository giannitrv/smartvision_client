FROM ubuntu:latest

# This fix: libGL error: No matching fbConfigs or visuals found
ENV LIBGL_ALWAYS_INDIRECT=1
# Install Python 3, PyQt5
RUN apt-get update && apt-get install -y python3-opencv python3-pip python3-pyqt5
# Create and set workdir
WORKDIR /app
# Copy source file into workdir
COPY ./src/ ./

#RUN pip install -r requirements.txt

CMD ["python3", "main.py"]
