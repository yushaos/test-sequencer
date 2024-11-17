from threading import Thread
import time
import queue
from multiprocessing import Process
from scheduler import Scheduler

class StepExecutionThread(Thread):
    def __init__(self, scheduler, step):
        super().__init__()
        self.scheduler = scheduler
        self.step = step
        self.result = None
        self.error = None
        self.completed = False
        
    def run(self):
        try:
            self.result = self.scheduler.execute_step(self.step)
            self.completed = True
        except Exception as e:
            self.error = e
            self.completed = True

def run_steps_worker(steps, step_queue, result_queue):
    total_steps = sum(len([s for s in section if s['enable']]) 
                     for section in steps.values())
    current_step = 0
    scheduler = Scheduler()
    scheduler.steps = steps

    for section, section_steps in steps.items():
        result_queue.put(('section', section))
        
        for step_index, step in enumerate(section_steps):
            if not step['enable']:
                continue

            result_queue.put(('step_start', {
                'current': current_step,
                'total': total_steps,
                'name': step['step_name'],
                'list_index': current_step
            }))

            try:
                start_time = time.time()
                step_thread = StepExecutionThread(scheduler, step)
                step_thread.start()
                
                while not step_thread.completed:
                    try:
                        if not step_queue.empty() and step_queue.get_nowait() == 'end':
                            step_thread.join(timeout=1.0)
                            result_queue.put(('end', None))
                            return False
                    except queue.Empty:
                        pass
                    time.sleep(0.1)
                
                step_thread.join()
                
                if step_thread.error:
                    raise step_thread.error
                
                if step_thread.result is not True:
                    result_queue.put(('error', f"Step '{step['step_name']}' did not return True"))
                    return False
                
                duration = time.time() - start_time
                
                result_queue.put(('step_complete', {
                    'current': current_step,
                    'total': total_steps,
                    'name': step['step_name'],
                    'result': True,
                    'duration': duration
                }))

            except Exception as e:
                result_queue.put(('step_error', {
                    'current': current_step,
                    'total': total_steps,
                    'name': step['step_name'],
                    'error': str(e)
                }))
                return False
            
            current_step += 1

    result_queue.put(('complete', None))
    return True 