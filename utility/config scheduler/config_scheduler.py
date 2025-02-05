import asyncio
import json
import time
from dataclasses import dataclass
from typing import List, Dict, Set
from functools import partial

@dataclass
class Task:
    id: str
    dependencies: Set[str]
    status: str = "pending"  # pending, running, completed, failed
    
class TaskScheduler:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.load_config()
        self.completed_tasks: Set[str] = set()
        self.failed_tasks: Set[str] = set()
        
    def load_config(self):
        with open("config_scheduler.json") as f:
            config = json.load(f)
            for task_id, dependencies in config["tasks"].items():
                self.tasks[task_id] = Task(
                    id=task_id,
                    dependencies=set(dependencies)
                )
    
    def get_ready_tasks(self) -> List[Task]:
        """Return tasks whose dependencies are all completed."""
        ready_tasks = []
        for task in self.tasks.values():
            if (task.status == "pending" and 
                task.dependencies.issubset(self.completed_tasks) and
                task.id not in self.failed_tasks):
                ready_tasks.append(task)
        return ready_tasks
    
    async def execute_task(self, task: Task):
        """Execute a single task with timeout."""
        print(f"Starting task: {task.id}")
        task.status = "running"
        
        try:
            # Get function dynamically from globals
            task_function = globals()[task.id]
            
            # Create a coroutine for the task function
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, task_function),
                timeout=20
            )
            
            if result is True:
                task.status = "completed"
                self.completed_tasks.add(task.id)
                print(f"Completed task: {task.id}")
            else:
                task.status = "failed"
                self.failed_tasks.add(task.id)
                print(f"Task failed: {task.id} (did not return True)")
                
        except asyncio.TimeoutError:
            task.status = "failed"
            self.failed_tasks.add(task.id)
            print(f"Task failed: {task.id} (timeout)")
        except Exception as e:
            task.status = "failed"
            self.failed_tasks.add(task.id)
            print(f"Task failed: {task.id} (error: {str(e)})")
    
    async def run(self):
        """Main execution loop."""
        while len(self.completed_tasks) + len(self.failed_tasks) < len(self.tasks):
            ready_tasks = self.get_ready_tasks()
            if not ready_tasks:
                if self.failed_tasks:
                    print("Some tasks failed, cannot complete all tasks:")
                    for task_id in self.failed_tasks:
                        print(f"- {task_id}")
                    break
                await asyncio.sleep(0.1)
                continue
                
            # Launch all ready tasks in parallel
            await asyncio.gather(
                *(self.execute_task(task) for task in ready_tasks)
            )
        
        if not self.failed_tasks:
            print("\nAll tasks completed successfully!")
        else:
            print("\nExecution finished with failures:")
            print(f"Completed tasks: {len(self.completed_tasks)}")
            print(f"Failed tasks: {len(self.failed_tasks)}")

# Task functions
def task1():
    print("Starting task1")
    time.sleep(3)
    return True

def task2():
    print("Starting task2")
    time.sleep(3)
    return True

def task3():
    print("Starting task3")
    time.sleep(3)
    return True

def task4():
    print("Starting task4")
    time.sleep(3)
    return True

def task5():
    print("Starting task5")
    time.sleep(3)
    return True

def task6():
    print("Starting task6")
    time.sleep(3)
    return True

def task7():
    print("Starting task7")
    time.sleep(3)
    return True

def task8():
    print("Starting task8")
    time.sleep(3)
    return True

def task9():
    print("Starting task9")
    time.sleep(3)
    return True

def task10():
    print("Starting task10")
    time.sleep(3)
    return True

async def main():
    scheduler = TaskScheduler()
    await scheduler.run()

if __name__ == "__main__":
    asyncio.run(main())