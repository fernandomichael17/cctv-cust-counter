import logging
import os
import time
import cv2
from ultralytics import YOLO
from .db import connect, event, status
from .crossing import CrossingCounter

log = logging.getLogger(__name__)

def run_camera(camera):
    cid = camera['id']
    url = os.getenv(camera['env'])
    if not url:
        log.error('%s: missing environment variable %s', cid, camera['env'])
        return
    model = YOLO(os.getenv('MODEL', 'yolo11n.pt'))
    stride = max(1, int(os.getenv('FRAME_STRIDE', '3')))
    width = int(os.getenv('PROCESS_WIDTH', '960'))
    device = os.getenv('DEVICE', 'cpu')
    margin = float(os.getenv('CROSSING_MARGIN', '0.025'))
    conn = None
    while True:
        cap = None
        try:
            if conn is None or conn.closed:
                conn = connect()
            cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
            if not cap.isOpened():
                raise RuntimeError('RTSP stream could not be opened')
            counter = CrossingCounter(*camera['line'], camera['inside_side'], margin)
            frame_no = 0
            status(conn, cid, 'online')
            last_heartbeat = time.monotonic()
            while True:
                ok, frame = cap.read()
                if not ok:
                    raise RuntimeError('RTSP read failed')
                frame_no += 1
                if frame_no % stride:
                    continue
                h, w = frame.shape[:2]
                if w > width:
                    frame = cv2.resize(frame, (width, round(h*width/w)))
                result = model.track(frame, persist=True, tracker='bytetrack.yaml',
                                     classes=[0], conf=float(os.getenv('MIN_CONF', '0.35')),
                                     device=device, verbose=False)[0]
                tracks = []
                if result.boxes is not None and result.boxes.id is not None:
                    boxes = result.boxes.xyxy.cpu().numpy()
                    ids = result.boxes.id.int().cpu().tolist()
                    fh, fw = frame.shape[:2]
                    for tid, box in zip(ids, boxes):
                        x1,y1,x2,y2 = box
                        tracks.append((tid, float((x1+x2)/2/fw), float(y2/fh)))
                for direction in counter.update(tracks):
                    event(conn, cid, direction)
                    log.info('%s %s', cid, direction)
                if time.monotonic() - last_heartbeat >= 10:
                    status(conn, cid, 'online')
                    last_heartbeat = time.monotonic()
        except Exception as exc:
            log.exception('%s: worker failed', cid)
            try:
                if conn is None or conn.closed: conn = connect()
                status(conn, cid, 'offline', str(exc)[:200])
            except Exception:
                log.exception('%s: cannot update status', cid)
            time.sleep(5)
        finally:
            if cap is not None: cap.release()
