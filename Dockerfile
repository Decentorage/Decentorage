FROM python:3

# Set up code directory
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# Install Linux dependencies
RUN apt-get update && apt-get install -y libssl-dev 

COPY . .
RUN pip install -r requirements.txt


EXPOSE 5000
CMD ["python", "run.py", "--env", "prod"]