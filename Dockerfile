# Use the official Python image from Docker Hub
FROM python:3.11-slim

# Set environment variables to prevent Python from writing pyc files to disk
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt to the container's working directory
COPY requirements.txt /app/

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files into the container
COPY . /app/

# Expose the port that Django will run on
EXPOSE 8075

# Command to run when the container starts
CMD ["python", "manage.py", "runserver", "0.0.0.0:8075"]
