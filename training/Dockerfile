# training/Dockerfile
FROM quay.io/jupyter/base-notebook:latest

# Set the working directory
WORKDIR /training

# Copy your requirements
COPY requirements.txt .

RUN pip install -r requirements.txt