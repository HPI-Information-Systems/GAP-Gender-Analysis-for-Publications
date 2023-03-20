FROM python:3.9.13
EXPOSE 6501
WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN pip3 install -r requirements.txt
COPY . /app
CMD streamlit run prototype.py --server.port 6501
