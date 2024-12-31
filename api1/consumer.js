const amqplib = require('amqplib');
const queue = 'tasks';

(async () => {
    try {
        const connection = await amqplib.connect('amqp://rabbitmq');
        const channel = await connection.createChannel();
        await channel.assertQueue(queue);

        console.log('Consumer 1 waiting for messages...');
        channel.consume(queue, (msg) => {
            if (msg !== null) {
                const task = JSON.parse(msg.content.toString());
                console.log('Processing task:', task);

                console.log(`Task [${task.task_name}] is now in progress.`);

                channel.ack(msg);
            }
        });
    } catch (error) {
        console.error('Error:', error);
    }
})();
