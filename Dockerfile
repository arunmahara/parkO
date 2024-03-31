FROM python:3.10
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /park
COPY . /park
RUN pip install -r requirements.txt
EXPOSE 8000
CMD python manage.py migrate && python manage.py runserver 0.0.0.0:8000


# sudo docker build -t park .
# sudo docker run -dp 8000:8000 park