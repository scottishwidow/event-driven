from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import pika
import os
import json

app = FastAPI()

DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
RABBITMQ_QUEUE = 'tasks'

class Task(BaseModel):
    user_id: int
    task_name: str
    description: str

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

@app.post("/tasks")
def create_task(task: Task):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO tasks (user_id, task_name, description) VALUES (%s, %s, %s) RETURNING id;",
            (task.user_id, task.task_name, task.description)
        )
        task_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=RABBITMQ_QUEUE)
        channel.basic_publish(
            exchange='',
            routing_key=RABBITMQ_QUEUE,
            body=json.dumps(task.dict())
        )
        connection.close()

        return {"message": "Task created successfully.", "task_id": task_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
