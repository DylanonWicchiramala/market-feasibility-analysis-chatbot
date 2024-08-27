# Use an official Python runtime as a parent image
FROM python:3.11.9-slim

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY --chown=user . /app

RUN pip install --no-cache-dir --upgrade pip

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5050 available to the world outside this container
EXPOSE 8080

# Run api.py when the container launches
CMD gunicorn --bind :8080 api:app --timeout 600