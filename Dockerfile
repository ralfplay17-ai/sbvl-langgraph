FROM langflowai/langflow:latest

RUN pip install --no-cache-dir \
	pip install plotly pandas \
    pyswarms==1.3.0 \
    yfinance==0.2.28 \
    newsapi-python==0.2.7 \
    pandas \
    numpy \
    scipy \
    requests

RUN mkdir -p /app/flows

COPY sistema_bvl.json /app/flows/sistema_bvl.json

WORKDIR /app

EXPOSE 7860

CMD ["langflow", "run", "--host", "0.0.0.0", "--port", "7860"]
