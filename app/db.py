import os
import psycopg

def connect():
    return psycopg.connect(os.environ['DATABASE_URL'], autocommit=True)

def event(conn, camera_id, direction):
    with conn.cursor() as cur:
        cur.execute('INSERT INTO count_events(camera_id,direction) VALUES (%s,%s)', (camera_id,direction))

def status(conn, camera_id, state, detail=''):
    with conn.cursor() as cur:
        cur.execute('''INSERT INTO camera_status(camera_id,status,detail) VALUES (%s,%s,%s)
          ON CONFLICT(camera_id) DO UPDATE SET status=EXCLUDED.status,
          detail=EXCLUDED.detail,last_seen=NOW()''', (camera_id,state,detail))
