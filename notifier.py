import pika

def callback(ch, method, properties, body):
    print(f"Recebi uma nova tarefa: {body}")

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='task_queue')

channel.basic_consume(queue='task_queue', on_message_callback=callback, auto_ack=True)

print('Notificador aguardando mensagens. Para sair pressione CTRL+C')
channel.start_consuming()
