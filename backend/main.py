from fastapi import FastAPI
from routers import game_router
from services import game_service
from contextlib import asynccontextmanager
import multiprocessing

# --- constants ---
NUM_WORKERS = 8   # the number of engine instances
MAX_SESSIONS = 8  # concurrent session cap  

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
    print('Server startup complete')

    yield

    # --- shutdown logic ---
    print('Server is shutting down...')
    manager.shutdown()
    print('Server shutdown complete')

app = FastAPI(lifespan=lifespan)
app.include_router(game_router.router, prefix='/game')

@app.get('/')
async def root():
    print('Server is running!')
    return {'message': 'Server is running!'}