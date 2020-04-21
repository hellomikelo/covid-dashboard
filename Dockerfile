# Dockerfile for building the Streamlit app
# Note: Docker installs from top to bottom and skips steps if process is already complete and is not modified.

# pull miniconda image
FROM python:3.6

# copy local files into container
COPY app.py /tmp/
COPY requirements.txt /tmp/
COPY geojson /tmp/geojson

ENV PORT 8080

# change directory
WORKDIR /tmp

# install dependencies
RUN apt-get update && apt-get install -y vim
RUN pip install -r requirements.txt

# run commands
CMD ["streamlit", "run", "app.py"]
