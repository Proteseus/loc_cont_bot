# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /usr/src/app

ADD . /usr/src/app/

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install schedule

# Run scheduler.py when the container launches
CMD ["python", "scheduler.py"]
