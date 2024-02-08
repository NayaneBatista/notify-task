from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import pika

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
db = SQLAlchemy(app)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(120))
    status = db.Column(db.String(20), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status
        }

def send_message_to_queue(task):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='task_queue')

    if isinstance(task, Task):
        body = str(task.to_dict())
    else: 
        body = str(task)

    channel.basic_publish(exchange='', routing_key='task_queue', body=body)
    connection.close()

@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.json
    task = Task(title=data['title'], description=data['description'], status=data['status'])
    db.session.add(task)
    db.session.commit()
    send_message_to_queue(task)
    return jsonify(task.to_dict()), 201

@app.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()
    return jsonify([task.to_dict() for task in tasks])

@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = db.session.get(Task, task_id)
    if task is None:
        return jsonify({'message': 'Tarefa não encontrada'}), 404

    data = request.json
    task.title = data.get('title', task.title)
    task.description = data.get('description', task.description)
    task.status = data.get('status', task.status)

    db.session.commit()
    send_message_to_queue(task)

    return jsonify(task.to_dict()), 200

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = Task.query.get(task_id)
    if task is None:
        return jsonify({'message': 'Tarefa não encontrada'}), 404

    db.session.delete(task)
    db.session.commit()
    send_message_to_queue({'id': task_id, 'action': 'delete'})

    return jsonify({'message': 'Tarefa deletada com sucesso'}), 200

if __name__ == '__main__':
    app.run(debug=True)
