FROM langflowai/langflow:latest

RUN pip install --no-cache-dir \
    plotly \
    pyswarms==1.3.0 \
    yfinance==0.2.28 \
    newsapi-python==0.2.7 \
    pandas \
    numpy \
    scipy \
    requests \
    streamlit>=1.35.0

RUN mkdir -p /app/flows /app/data_bvl/data

COPY sistema_bvl.json /app/flows/sistema_bvl.json
COPY app.py /app/app.py
COPY data_bvl/ /app/data_bvl/
COPY start.sh /app/start.sh
USER root
RUN chmod +x /app/start.sh

WORKDIR /app

ENV LANGFLOW_LOAD_FLOWS_PATH=/app/flows

EXPOSE 7860 8501

CMD ["/app/start.sh"]
