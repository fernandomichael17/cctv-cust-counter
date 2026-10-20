import os
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import plotly.express as px
import psycopg
import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title='Mall Visitor Analytics', layout='wide')
st.title('Mall Visitor Analytics')
st_autorefresh(interval=5000, key='refresh')
TZ = os.getenv('MALL_TIMEZONE', 'Asia/Jakarta')
zone = ZoneInfo(TZ)
now = datetime.now(zone)
day_start = now.replace(hour=0,minute=0,second=0,microsecond=0)

try:
    with psycopg.connect(os.environ['DATABASE_URL']) as conn:
        events = pd.read_sql_query('''SELECT camera_id, direction, observed_at
            FROM count_events WHERE observed_at >= %s AND observed_at < %s
            ORDER BY observed_at''', conn, params=(day_start, now))
        statuses = pd.read_sql_query('SELECT camera_id,status,last_seen FROM camera_status ORDER BY camera_id', conn)
except Exception as e:
    st.error(f'Database unavailable: {e}')
    st.stop()

entered = int((events.direction == 'IN').sum()) if not events.empty else 0
exited = int((events.direction == 'OUT').sum()) if not events.empty else 0
baseline = int(os.getenv('OPENING_OCCUPANCY', '0'))
a,b,c = st.columns(3)
a.metric('Masuk hari ini', f'{entered:,}')
b.metric('Keluar hari ini', f'{exited:,}')
c.metric('Estimasi di dalam', f'{baseline + entered - exited:,}')
st.caption('Estimasi okupansi memerlukan baseline pembukaan yang benar dan semua akses terhitung.')

if not events.empty:
    events['hour'] = pd.to_datetime(events.observed_at, utc=True).dt.tz_convert(TZ).dt.floor('h')
    hourly = events.groupby(['hour','direction']).size().reset_index(name='people')
    st.plotly_chart(px.line(hourly, x='hour', y='people', color='direction', markers=True,
                           title='Lalu lintas per jam'), use_container_width=True)
    st.subheader('Per kamera')
    counts = events.groupby(['camera_id','direction']).size().unstack(fill_value=0)
    st.dataframe(counts, use_container_width=True)
else:
    st.info('Belum ada event hari ini.')
st.subheader('Status kamera')
if not statuses.empty:
    statuses['last_seen'] = pd.to_datetime(statuses.last_seen, utc=True)
    statuses['health'] = statuses.apply(lambda r: 'online' if r['status']=='online' and
        (pd.Timestamp.now(tz='UTC') - r['last_seen']).total_seconds() < 30 else 'offline/stale', axis=1)
    st.dataframe(statuses, use_container_width=True, hide_index=True)
else:
    st.info('Belum ada heartbeat kamera.')
