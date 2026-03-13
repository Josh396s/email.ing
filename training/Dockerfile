# training/Dockerfile
FROM quay.io/jupyter/base-notebook:latest

# Set the working directory
WORKDIR /home/josh/work

# Copy your requirements
COPY requirements.txt .

# Install your specific ML libraries
RUN pip install --no-cache-dir -r requirements.txt