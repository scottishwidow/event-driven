from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import pika
import os
import json
import logging
from datetime import datetime

app = FastAPI()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

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

class TaskStatusUpdate(BaseModel):
    status: str

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME
    )

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
        cur.execute("SELECT id FROM users WHERE id = %s;", (task.user_id,))
        if cur.fetchone() is None:
            raise HTTPException(status_code=400, detail="User ID does not exist.")

        cur.execute(
            "INSERT INTO tasks (user_id, task_name, description) VALUES (%s, %s, %s) RETURNING id;",
            (task.user_id, task.task_name, task.description)
        )
        task_id = cur.fetchone()[0]
        conn.commit()

        cur.execute(
            "INSERT INTO audit_logs (action, task_id, performed_by) VALUES (%s, %s, %s);",
            ("created", task_id, task.user_id)
        )
        conn.commit()
        cur.close()
        conn.close()

        connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        channel.basic_publish(
            exchange='',
            routing_key=RABBITMQ_QUEUE,
            body=json.dumps({"task_id": task_id, **task.dict()})
        )
        connection.close()

        logging.info(f"Task {task_id} created and sent to RabbitMQ.")
        return {
            "message": "Task created successfully.",
            "task_id": task_id,
            "status": "pending",
            "estimated_completion_time": "2 minutes"
        }
    except Exception as e:
        logging.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/tasks/{task_id}/status")
def update_task_status(task_id: int, task_status: TaskStatusUpdate):
    try:
        status = task_status.status
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE tasks SET status = %s, updated_at = NOW() WHERE id = %s;", (status, task_id))
        conn.commit()
        cur.close()
        conn.close()
        return {"message": "Task status updated successfully."}
    except Exception as e:
        logging.error(f"Error updating task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

