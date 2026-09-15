import datetime
import json
import os
import streamlit as st
from streamlit_calendar import calendar

# 1. Page Configuration
st.set_page_config(
    page_title="CSW HUSA Calendar", page_icon="📅", layout="wide"
)

# Custom Google Calendar-inspired styling + Mobile touch-scrolling fix
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        stTabs [data-baseweb="tab-list"] {
            gap: 10px;
        }
        /* Fixes mobile touch scrolling in week and day time grids */
        .fc-scroller {
            overflow-y: auto !important;
            -webkit-overflow-scrolling: touch !important;
        }
    </style>
""",
    unsafe_allow_html=True,
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
        "backgroundColor": "#1a73e8",
        "borderColor": "#1a73e8",
        "extendedProps": {"notes": "Welcome to your new calendar!"},
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

# --- TAB LAYOUT ---
tab_calendar, tab_manage = st.tabs(["📅 Calendar View", "✍️ Add & Manage Events"])

with tab_calendar:
  st.subheader("Calendar Grid")

  # Fixed height and explicit time bounds ensure all 24 hours show up and scroll properly
  calendar_options = {
      "editable": True,
      "selectable": True,
      "initialView": "dayGridMonth",
      "headerToolbar": {
          "left": "prev,next today",
          "center": "title",
          "right": "dayGridMonth,timeGridWeek,timeGridDay",
      },
      "buttonText": {
          "today": "Today",
          "month": "Month",
          "week": "Week",
          "day": "Day",
      },
      "navLinks": True,
      "nowIndicator": True,
      "dayMaxEvents": True,
      "height": "650px",  # Fixed height enables the inner time scrollbar
      "slotMinTime": "00:00:00",  # Starts the day at midnight
      "slotMaxTime": "24:00:00",  # Ends the day at midnight
      "scrollTime": "08:00:00",  # Automatically scrolls to 8 AM when opening Week/Day view
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
  elif calendar_result and "select" in calendar_result:
    st.session_state.selected_click_date = calendar_result["select"][
        "start"
    ][:10]
  elif calendar_result and "eventClick" in calendar_result:
    st.session_state.selected_click_date = calendar_result["eventClick"][
        "event"
    ]["start"][:10]

  active_date = st.session_state.selected_click_date
  st.info(f"📌 **Selected Date:** {active_date}")

  day_events = []
  for ev in st.session_state.events:
    ev_start = ev["start"][:10]
    if ev.get("allDay", False):
      try:
        raw_end_dt = datetime.date.fromisoformat(ev["end"][:10])
        ev_end = str(raw_end_dt - datetime.timedelta(days=1))
      except ValueError:
        ev_end = ev["start"][:10]
    else:
      ev_end = ev["end"][:10]

    if ev_start <= active_date <= ev_end:
      day_events.append((ev, ev_start, ev_end))

  if day_events:
    for ev, s_date, e_date in day_events:
      notes = ev.get("extendedProps", {}).get("notes", "No notes provided.")
      date_str = (
          f"{s_date}" if s_date == e_date else f"{s_date} to {e_date}"
      )
      st.write(
          f"• **{ev['title']}** (*{date_str}*)\n  💬 *Notes:* {notes}"
      )
  else:
    st.write("No events scheduled for this day.")

with tab_manage:
  sub_add, sub_edit_del = st.tabs(["➕ Add New", "✏️ Edit / Delete"])

  with sub_add:
    st.subheader("Add New Event")

    active_date = st.session_state.selected_click_date
    try:
      default_date = datetime.date.fromisoformat(active_date)
    except ValueError:
      default_date = datetime.date.today()

    add_mode = st.radio(
        "Event Duration Type",
        ["Single Day (with times)", "All-Day / Multi-Day"],
        key="add_mode_radio",
    )

    start_date, end_date = default_date, default_date
    start_time, end_time = datetime.time(9, 0), datetime.time(10, 0)
    is_all_day = False

    if add_mode == "Single Day (with times)":
      start_date = st.date_input("Date", value=default_date, key="add_d")
      end_date = start_date
      t1, t2 = st.columns(2)
      with t1:
        start_time = st.time_input(
            "Start Time", value=datetime.time(9, 0), key="add_st"
        )
      with t2:
        end_time = st.time_input(
            "End Time", value=datetime.time(10, 0), key="add_et"
        )
      is_all_day = False
    else:
      c1, c2 = st.columns(2)
      with c1:
        start_date = st.date_input(
            "Start Date", value=default_date, key="add_sd"
        )
      with c2:
        end_date = st.date_input("End Date", value=default_date, key="add_ed")
      is_all_day = True

    with st.form("add_event_form", clear_on_submit=True):
      event_title = st.text_input("Event Name / Description")
      event_notes = st.text_area("Notes / Details")
      submitted = st.form_submit_button("Add to Calendar")

      if submitted and event_title:
        if start_date > end_date:
          st.error("Start date cannot be after the end date!")
        else:
          if is_all_day:
            next_day = end_date + datetime.timedelta(days=1)
            start_iso = str(start_date)
            end_iso = str(next_day)
          else:
            start_iso = f"{start_date}T{start_time.strftime('%H:%M:%S')}"
            end_iso = f"{end_date}T{end_time.strftime('%H:%M:%S')}"

          new_event = {
              "title": event_title,
              "start": start_iso,
              "end": end_iso,
              "allDay": is_all_day,
              "backgroundColor": "#1a73e8",
              "borderColor": "#1a73e8",
              "extendedProps": {"notes": event_notes},
          }

          st.session_state.events.append(new_event)
          save_events(st.session_state.events)
          st.success(f"Added '{event_title}'!")
          st.rerun()

  with sub_edit_del:
    st.subheader("Edit or Delete Events")

    if st.session_state.events:
      event_titles = [ev["title"] for ev in st.session_state.events]
      selected_title = st.selectbox(
          "Select event to modify:", options=event_titles, key="mod_select"
      )

      current_idx = next(
          (
              i
              for i, ev in enumerate(st.session_state.events)
              if ev["title"] == selected_title
          ),
          0,
      )
      current_ev = st.session_state.events[current_idx]

      if current_ev:
        try:
          ex_start_dt = datetime.datetime.fromisoformat(current_ev["start"])
          ex_start_date = ex_start_dt.date()
          ex_start_time = ex_start_dt.time()
        except ValueError:
          ex_start_date = datetime.date.today()
          ex_start_time = datetime.time(9, 0)

        try:
          if current_ev.get("allDay", False):
            ex_end_dt = datetime.date.fromisoformat(
                current_ev["end"][:10]
            ) - datetime.timedelta(days=1)
            ex_end_time = datetime.time(10, 0)
          else:
            ex_end_dt = datetime.datetime.fromisoformat(
                current_ev["end"]
            ).date()
            ex_end_time = datetime.datetime.fromisoformat(
                current_ev["end"]
            ).time()
        except ValueError:
          ex_end_dt = datetime.date.today()
          ex_end_time = datetime.time(10, 0)

        initial_index = 1 if current_ev.get("allDay", False) else 0

        edit_mode = st.radio(
            "Event Duration Type",
            ["Single Day (with times)", "All-Day / Multi-Day"],
            index=initial_index,
            key=f"edit_mode_{current_idx}",
        )

        new_title = st.text_input(
            "Update Event Name",
            value=current_ev["title"],
            key=f"edit_title_{current_idx}",
        )

        new_start_date, new_end_date = ex_start_date, ex_end_dt
        new_start_time, new_end_time = ex_start_time, ex_end_time
        is_all_day_edit = False

        if edit_mode == "Single Day (with times)":
          new_start_date = st.date_input(
              "Date", value=ex_start_date, key=f"edit_d_{current_idx}"
          )
          new_end_date = new_start_date
          et1, et2 = st.columns(2)
          with et1:
            new_start_time = st.time_input(
                "Start Time", value=ex_start_time, key=f"edit_st_{current_idx}"
            )
          with et2:
            new_end_time = st.time_input(
                "End Time", value=ex_end_time, key=f"edit_et_{current_idx}"
            )
          is_all_day_edit = False
        else:
          ec1, ec2 = st.columns(2)
          with ec1:
            new_start_date = st.date_input(
                "New Start Date",
                value=ex_start_date,
                key=f"edit_sd_{current_idx}",
            )
          with ec2:
            new_end_date = st.date_input(
                "New End Date", value=ex_end_dt, key=f"edit_ed_{current_idx}"
            )
          is_all_day_edit = True

        current_notes = current_ev.get("extendedProps", {}).get("notes", "")
        new_notes = st.text_area(
            "Update Notes",
            value=current_notes,
            key=f"edit_notes_{current_idx}",
        )

        if st.button("Save Changes", type="primary", key=f"save_edit_{current_idx}"):
          if new_start_date > new_end_date:
            st.error("Start date cannot be after the end date!")
          else:
            if is_all_day_edit:
              next_day = new_end_date + datetime.timedelta(days=1)
              start_iso = str(new_start_date)
              end_iso = str(next_day)
              is_all_day = True
            else:
              start_iso = (
                  f"{new_start_date}T{new_start_time.strftime('%H:%M:%S')}"
              )
              end_iso = f"{new_end_date}T{new_end_time.strftime('%H:%M:%S')}"
              is_all_day = False

            current_ev["title"] = new_title
            current_ev["start"] = start_iso
            current_ev["end"] = end_iso
            current_ev["allDay"] = is_all_day
            current_ev["backgroundColor"] = "#1a73e8"
            current_ev["borderColor"] = "#1a73e8"

            if "extendedProps" not in current_ev:
              current_ev["extendedProps"] = {}
            current_ev["extendedProps"]["notes"] = new_notes

            save_events(st.session_state.events)
            st.success(f"Updated '{new_title}' successfully!")
            st.rerun()

        st.divider()
        if st.button(
            f"Delete '{selected_title}'",
            type="primary",
            key=f"del_btn_{current_idx}",
        ):
          st.session_state.events = [
              ev
              for ev in st.session_state.events
              if ev["title"] != selected_title
          ]
          save_events(st.session_state.events)
          st.success(f"Deleted '{selected_title}'!")
          st.rerun()
    else:
      st.write("No events available to edit or delete.")
