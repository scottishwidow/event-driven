from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import psycopg2
import pika
import os

app = FastAPI()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', 5432)
DB_USER = os.getenv('DB_USER', postgres)
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
DB_NAME = os.getenv('DB_NAME', 'exampledb')

RABBITMQ_HOST= os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_QUEUE = 'tasks'

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME
    )
    return conn

@app.get("/db")
def test_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.close()
        conn.close()
        return {"message": "Database connection successful."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/publish")
def publich_message(message: str):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=RABBITMQ_QUEUE)
        channel.basic_publish(exchange='', routing_key=RABBITMQ_QUEUE, body=message)
        connection.close()
        return {"message": "Message published."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
