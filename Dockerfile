# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

FROM python:3.13.2-slim

RUN addgroup --system appgroup && adduser --system --ingroup appgroup --home /home/appuser appuser

# Create working directory and set permissions
WORKDIR /app
COPY . /app
RUN chown -R appuser:appgroup /app

# Set environment variables for Python and user home
ENV PYTHONUNBUFFERED=1 \
    HOME=/home/appuser

RUN pip install --upgrade pip setuptools wheel

# Switch to non-root user
USER appuser

RUN pip install --no-cache-dir --no-build-isolation . --root-user-action=ignore

ENTRYPOINT ["python", "juspay_mcp/stdio.py"]
