FROM python:3.12-slim

WORKDIR /src/Booking
COPY . /src/Booking

ENV PYTHONPATH=/src
ENV FLASK_APP=api

RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "Booking.asgi:app", "--host", "0.0.0.0", "--port", "80"]
