from locust import HttpUser, task, between

class TodoUser(HttpUser):
    wait_time = between(1,2)
    
    @task
    def get_todos(self):
        self.client.get("/todos")
        
    @task
    def create_todo(self):
        self.client.post("/todos", json={"title":"Loaded Test Todo", "completed": False})
        
# locust -f locustfile.py --host=http://localhost:8000