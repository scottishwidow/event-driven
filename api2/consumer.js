const amqplib = require('amqplib');
const axios = require('axios');
const queue = 'tasks';
const maxRetries = 3;

(async () => {
    try {
        const connection = await amqplib.connect('amqp://rabbitmq');
        const channel = await connection.createChannel();
        await channel.assertQueue(queue, { durable: true });
        channel.prefetch(1);

        console.log('Consumer 2 waiting for messages...');

        channel.consume(queue, async (msg) => {
            if (msg !== null) {
                try {
                    const task = JSON.parse(msg.content.toString());
                    console.log('Received task for notification:', task);

                    // Simulate sending a notification
                    console.log(`Notification: Task [${task.task_name}] has been processed.`);

                    // Update task status to 'completed'
                    await axios.patch(`http://main-api/tasks/${task.task_id}/status`, { status: 'completed' });

                    channel.ack(msg);
                } catch (error) {
                    console.error(`Failed to send notification: ${error.message}`);
                    let retries = msg.properties.headers['x-retry-count'] || 0;

                    if (retries < maxRetries) {
                        channel.nack(msg, false, false); // Requeue the message
                        msg.properties.headers['x-retry-count'] = retries + 1;
                    } else {
                        console.error(`Notification task ${msg.content.toString()} failed after ${maxRetries} retries.`);
                        channel.ack(msg); // Send to DLQ or log for further investigation
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error:', error);
    }
})();

