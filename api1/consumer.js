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

        console.log('Consumer 1 waiting for messages...');

        channel.consume(queue, async (msg) => {
            if (msg !== null) {
                try {
                    const task = JSON.parse(msg.content.toString());
                    console.log('Processing task:', task);

                    // Update task status to 'in-progress'
                    await axios.patch(`http://main-api/tasks/${task.task_id}/status`, { status: 'in-progress' });

                    // Simulate task processing
                    console.log(`Task [${task.task_name}] is now in progress.`);
                    channel.ack(msg);
                } catch (error) {
                    console.error(`Failed to process task: ${error.message}`);
                    let retries = (msg.properties.headers && msg.properties.headers['x-retry-count']) || 0;

                    if (retries < maxRetries) {
                        msg.properties.headers = msg.properties.headers || {};
                        msg.properties.headers['x-retry-count'] = retries + 1;
                        channel.nack(msg, false, true); // Requeue the message
                    } else {
                        console.error(`Task ${msg.content.toString()} failed after ${maxRetries} retries.`);
                        channel.ack(msg); // Send to DLQ or log for further investigation
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error:', error);
    }
})();

