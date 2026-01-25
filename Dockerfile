FROM python:slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Set the image's working directory
WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy required files
COPY pyproject.toml uv.lock* ./
COPY README.md LICENSE.md ./
COPY src/ src/

# Install the pytide package
RUN uv pip install --system .

# Remove the src directory when it's no longer needed
RUN rm -rf src

# Create a non-root user with an explicit UID and adds permission to access the /app folder.
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --no-create-home \
    --uid="${UID}" \
    appuser \
    && chown -R appuser /app
USER appuser

# Execute the script.
CMD ["pytide"]
