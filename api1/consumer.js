const amqplib = require('amqplib');
const queue = 'tasks';

(async () => {
  try {
    const connection = await amqplib.connect('amqp://localhost');
    const channel = await connection.createChannel();
    await channel.assertQueue(queue);

    console.log('Waiting for messages...');
    channel.consume(queue, (msg) => {
      if (msg !== null) {
        console.log('Received:', msg.content.toString());
        channel.ack(msg);
      }
    });
  } catch (error) {
      console.log('Error:', error);
  }
})();
