# PMS Integration Service

Microservicio encargado de simular integración con el PMS.

## Ejecutar local

docker build -t pmsintegration . 

docker run -p 8001:8001 -v $(pwd)/data:/app/data pmsintegration

## Swagger

https://localhost:8001/docs

## Endpoint

POST /confirm-reservation
POST /cancel-reservation
