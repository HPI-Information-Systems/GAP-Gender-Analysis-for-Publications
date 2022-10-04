FROM python:3.10.4
EXPOSE 6501
WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN pip3 install -r requirements.txt
COPY . /app
CMD streamlit run prototype.py --server.port 6501
