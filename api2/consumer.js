const amqplib = require('amqplib');
const queue = 'tasks';

(async () => {
    try {
        const connection = await amqplib.connect('amqp://rabbitmq');
        const channel = await connection.createChannel();
        await channel.assertQueue(queue);

        console.log('Consumer 2 waiting for messages...');
        channel.consume(queue, (msg) => {
            if (msg !== null) {
                console.log('Consumer 2 received:', msg.content.toString());
                channel.ack(msg);
            }
        });
    } catch (error) {
        console.error('Error:', error);
    }
})();
