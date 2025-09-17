from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import game_router
from services import game_service
from contextlib import asynccontextmanager
import multiprocessing
import os
import threading
import time
import uuid

from dotenv import load_dotenv
load_dotenv()

# --- constants ---
NUM_WORKERS = int(os.getenv('NUM_WORKERS', '8'))     # the number of engine instances
MAX_SESSIONS = int(os.getenv('MAX_SESSIONS', '8'))   # concurrent session cap  
PRUNE_INTERVAL = 300    # 5 minutes
WORKER_TIMEOUT = 10     # time for workers to respond to prune task

def trigger_prune(app_state):
    """Dispatches a prune task to all workers and updates global state."""

    print('Background task: starting periodic session prune...')

    # unpack the necessary shared state objects
    session_count = app_state.session_count
    worker_load = app_state.worker_load
    task_queues = app_state.task_queues
    results_dict = app_state.results_dict
    session_count_lock = app_state.session_count_lock

    # dispatch a 'prune_sessions' task to all workers
    prune_task_ids = {}
    for i in range(NUM_WORKERS):
        task_id = uuid.uuid4().hex
        prune_task_ids[i] = task_id
        task_queues[i].put((task_id, 'prune_sessions', {}))

    # wait for all workers to respond
    pruned_counts = {}  # map worker_id to its pruned_count
    start_time = time.time()
    while len(pruned_counts) < NUM_WORKERS:
        if time.time() - start_time > WORKER_TIMEOUT:
            print('Timed out waiting for workers to prune')
            return
        
        # check for results from workers that haven't responded yet
        for worker_id, task_id in prune_task_ids.items():
            if worker_id not in pruned_counts and task_id in results_dict:
                status, result_data = results_dict.pop(task_id)

                if status == 'ok':
                    pruned_counts[worker_id] = result_data
                else:
                    # if a worker fails, assume it pruned 0
                    pruned_counts[worker_id] = 0

        time.sleep(0.01)

    # atomically update global counters
    total_pruned = 0
    with session_count_lock:
        for worker_id, count in pruned_counts.items():
            if count > 0:
                worker_load[worker_id] -= count

                # ensure worker_load can never go below 0
                if worker_load[worker_id] < 0:
                    worker_load[worker_id] = 0

                total_pruned += count
        
        # decrement global sessions count
        session_count.value -= total_pruned
        if session_count.value < 0:
            session_count.value = 0

        if total_pruned > 0:
            print(f'Background task: Pruned {total_pruned} inactive session(s)')
        else:
            print('No inactive sessions to prune')

def run_periodic_pruning(app_state, shutdown_event):
    """Runs in background at a 5-minute interval, triggers session pruning task dispatch."""

    while not shutdown_event.is_set():
        shutdown_event.wait(PRUNE_INTERVAL)

        if not shutdown_event.is_set():
            trigger_prune(app_state)

@asynccontextmanager
async def lifespan(app: FastAPI):
    manager = multiprocessing.Manager()

    # --- create shared state / communication objects ---
    app.state.results_dict = manager.dict()          # where workers put their results
    app.state.session_map = manager.dict()           # maps session_ids to their assigned worker
    app.state.session_count = manager.Value('i', 0)  # tracks global session count
    app.state.session_count_lock = manager.Lock()

    # tracks num. of active games on each worker
    app.state.worker_load = manager.list([0] * NUM_WORKERS)

    # list of queues, one for each worker to receives tasks on
    task_queues = [multiprocessing.Queue() for _ in range(NUM_WORKERS)]
    app.state.task_queues = task_queues

    # --- create and start worker processes ---
    workers = []
    for i in range(NUM_WORKERS):
        process = multiprocessing.Process(
            target=game_service.run_worker,
            args=(task_queues[i], app.state.results_dict),
            daemon=True
        )
        workers.append(process)
        process.start()

    app.state.workers = workers
    print(f'{NUM_WORKERS} chess worker processes started')

    # --- start background pruning thread ---
    shutdown_event = threading.Event()
    pruning_thread = threading.Thread(
        target=run_periodic_pruning,
        args=(app.state, shutdown_event),
        daemon=True,
    )
    pruning_thread.start()
    print(f'Background pruning task started. Interval: {PRUNE_INTERVAL} seconds.')

    print('Server startup complete')

    yield

    # --- shutdown logic ---
    print('Server is shutting down...')
    shutdown_event.set() # signal for pruning thread to stop
    manager.shutdown()
    print('Server shutdown complete')

app = FastAPI(lifespan=lifespan)

origins = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'https://quieceros.com',
    'https://www.quieceros.com',
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(game_router.router, prefix='/game')

@app.get('/')
async def root():
    print('Server is running!')
    return {'message': 'Server is running!'}