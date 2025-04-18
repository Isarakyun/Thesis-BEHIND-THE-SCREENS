FROM python:3.11

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -m nltk.downloader stopwords vader_lexicon wordnet punkt averaged_perceptron_tagger maxent_ne_chunker words wordnet_ic sentiwordnet

# Copy the current directory contents into the container at /app
COPY . .

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=main.py

# Run the application using Gunicorn with uvicorn worker class, 1 worker, and a 1200-second timeout (20 minutes)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--worker-class", "gevent", "--workers", "1", "--threads", "3", "--timeout", "1200", "web:app"]