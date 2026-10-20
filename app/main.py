import logging
import multiprocessing as mp
from pathlib import Path
import yaml
from .worker import run_camera

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    cameras = yaml.safe_load(Path('config/cameras.yaml').read_text())['cameras']
    if len({c['id'] for c in cameras}) != len(cameras):
        raise ValueError('Camera IDs must be unique')
    processes = []
    for camera in cameras:
        p = mp.Process(target=run_camera, args=(camera,), name=camera['id'])
        p.start()
        processes.append(p)
    try:
        for p in processes: p.join()
    except KeyboardInterrupt:
        for p in processes: p.terminate()
        for p in processes: p.join()
