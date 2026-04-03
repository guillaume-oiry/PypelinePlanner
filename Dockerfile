FROM python:3.13-slim

RUN apt-get update && apt-get install --no-install-recommends -y \
        build-essential && \
        apt-get install -y wget git && \
        apt-get clean && rm -rf /var/lib/apt/lists/*

ADD https://astral.sh/uv/install.sh /install.sh
RUN chmod -R 655 /install.sh && /install.sh && rm /install.sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

COPY ./pyproject.toml .
RUN uv sync

COPY . .

EXPOSE 8888

CMD ["uv", "run", "jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
