FROM python:3.11-slim

WORKDIR /runner
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
# Copy sandboxed runner
COPY runner.py runner.py

# Create a non-root user to run the service
RUN addgroup --system runner && adduser --system --ingroup runner runner
USER runner

CMD ["python", "runner.py"]
