# Payment Service

Microservicio encargado de simular pagos

## Ejecutar local

docker build -t paymentservice .

docker run -p 8000:8000 -v $(pwd)/data:/app/data paymentservice

## Swagger

https://localhost:8000/docs

## Endpoint

POST /process-payment
POST /refund