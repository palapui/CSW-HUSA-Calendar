import datetime
import json
import os
import streamlit as st
from streamlit_calendar import calendar

# 1. Page Configuration
st.set_page_config(
    page_title="CSW HUSA Calendar", page_icon="📅", layout="wide"
)

# 2. App Header
st.title("📅 CSW HUSA Calendar")

# --- FILE STORAGE FUNCTIONS ---
EVENTS_FILE = "events.json"


def load_events():
  if os.path.exists(EVENTS_FILE):
    try:
      with open(EVENTS_FILE, "r") as f:
        return json.load(f)
    except Exception:
      return []
  else:
    today_str = str(datetime.date.today())
    default_events = [{
        "title": "🚀 CSW HUSA Event",
        "start": f"{today_str}T09:00:00",
        "end": f"{today_str}T10:00:00",
        "allDay": False,
    }]
    save_events(default_events)
    return default_events


def save_events(events_list):
  with open(EVENTS_FILE, "w") as f:
    json.dump(events_list, f, indent=4)


# Load events into session state
if "events" not in st.session_state:
  st.session_state.events = load_events()

if "selected_click_date" not in st.session_state:
  st.session_state.selected_click_date = str(datetime.date.today())

# --- TAB LAYOUT (Perfect for mobile scrolling fix) ---
tab_calendar, tab_manage = st.tabs(["📅 Calendar View", "✍️ Add & Manage Events"])

with tab_calendar:
  st.subheader("Monthly Grid")

  calendar_options = {
      "editable": True,
      "selectable": True,
      "initialView": "dayGridMonth",
      "headerToolbar": {
          "left": "prev,next today",
          "center": "title",
          "right": "dayGridMonth,timeGridWeek",
      },
      "height": "auto",  # Allows calendar to adapt cleanly
  }

  calendar_result = calendar(
      events=st.session_state.events,
      options=calendar_options,
      key="my_visual_calendar",
  )

  if calendar_result and "dateClick" in calendar_result:
    st.session_state.selected_click_date = calendar_result["dateClick"]["date"][
        :10
    ]
  elif calendar_result and "eventClick" in calendar_result:
    st.session_state.selected_click_date = calendar_result["eventClick"][
        "event"
    ]["start"][:10]

  # Quick day preview right under the calendar
  active_date = st.session_state.selected_click_date
  st.info(f"📌 **Selected Date:** {active_date}")

  day_events = []
  for ev in st.session_state.events:
    ev_start = ev["start"][:10]
    ev_end = ev["end"][:10] if "end" in ev else ev_start
    if ev_start <= active_date <= ev_end:
      day_events.append(ev)

  if day_events:
    for ev in day_events:
      st.write(f"• **{ev['title']}** (*{ev['start']} to {ev['end']}*)")
  else:
    st.write("No events scheduled for this day.")

with tab_manage:
  st.subheader("Add New Event")

  active_date = st.session_state.selected_click_date
  try:
    default_date = datetime.date.fromisoformat(active_date)
  except ValueError:
    default_date = datetime.date.today()

  c1, c2 = st.columns(2)
  with c1:
    start_date = st.date_input(
        "Start Date", value=default_date, key="start_d"
    )
  with c2:
    end_date = st.date_input("End Date", value=default_date, key="end_d")

  is_same_day = start_date == end_date
  start_time, end_time = None, None

  if is_same_day:
    st.write("🕒 **Same-day times:**")
    t1, t2 = st.columns(2)
    with t1:
      start_time = st.time_input(
          "Start Time", value=datetime.time(9, 0), key="start_t"
      )
    with t2:
      end_time = st.time_input(
          "End Time", value=datetime.time(10, 0), key="end_t"
      )

  with st.form("event_form", clear_on_submit=True):
    event_title = st.text_input("Event Name / Description")
    submitted = st.form_submit_button("Add to Calendar")

    if submitted and event_title:
      if start_date > end_date:
        st.error("Start date cannot be after the end date!")
      else:
        if is_same_day:
          start_iso = f"{start_date}T{start_time.strftime('%H:%M:%S')}"
          end_iso = f"{end_date}T{end_time.strftime('%H:%M:%S')}"
          is_all_day = False
        else:
          next_day = end_date + datetime.timedelta(days=1)
          start_iso = str(start_date)
          end_iso = str(next_day)
          is_all_day = True

        new_event = {
            "title": event_title,
            "start": start_iso,
            "end": end_iso,
            "allDay": is_all_day,
        }

        st.session_state.events.append(new_event)
        save_events(st.session_state.events)
        st.success(f"Added '{event_title}'!")
        st.rerun()

  st.divider()
  st.subheader("Manage / Delete Events")

  if st.session_state.events:
    event_titles = [ev["title"] for ev in st.session_state.events]
    event_to_delete = st.selectbox(
        "Select event to delete:", options=event_titles
    )

    if st.button("Delete Selected Event", type="primary"):
      st.session_state.events = [
          ev for ev in st.session_state.events if ev["title"] != event_to_delete
      ]
      save_events(st.session_state.events)
      st.success(f"Deleted '{event_to_delete}'!")
      st.rerun()
  else:
    st.write("No events to delete.")