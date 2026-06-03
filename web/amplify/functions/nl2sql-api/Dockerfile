# Build context: repository root (see backend.ts imageAsset)
FROM public.ecr.aws/lambda/python:3.12

WORKDIR ${LAMBDA_TASK_ROOT}

# Layer cache: deps before app code
COPY requirements.txt requirements.txt
COPY api/requirements.txt api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

COPY api/ api/
COPY src/ src/
COPY schema/ schema/
COPY config/snowflake_config.py config/snowflake_config.py

ENV LAMBDA_APP_MODULE=api.main
ENV PYTHONUNBUFFERED=1
CMD ["api.lambda_handler.handler"]
