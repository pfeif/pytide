FROM python:slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install package requirements using pip with caching disabled
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

# Set the image's working directory and copy the program files except those in .dockerignore into
# the container
WORKDIR /app
COPY . /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder.
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --no-create-home \
    --uid="${UID}" \
    appuser \
    && chown -R appuser /app
USER appuser

# Execute the script. If needed, append command line arguments.
CMD ["python", "./pytide/pytide.py"]
