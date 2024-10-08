# Use an official Python runtime as a parent image
FROM python:3.11.5

# Set the working directory in the container to /app
WORKDIR /app

# Add the current directory contents into the container at /app
ADD . /app

# Copy the .env file into the container
COPY .env .env

# # System dependencies for MySQL
# RUN apt-get update && apt-get install -y default-libmysqlclient-dev
# RUN apt-get install libpq-dev

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Define an environment variable for the SQLite database path
ENV DB_PATH /app/db/database.db

# Make port 80 available to the world outside this container
EXPOSE 80

# Run bot.py when the container launches
CMD ["python", "ptb20.py"]