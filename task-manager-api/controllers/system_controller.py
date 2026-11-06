from datetime import datetime


class SystemController:
    def index(self):
        return {'message': 'Task Manager API', 'version': '1.0'}

    def health(self):
        # Hora local, como no original.
        return {'status': 'ok', 'timestamp': str(datetime.now())}
