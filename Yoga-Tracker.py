import os
import streamlit as st
import pandas as pd
import pymongo
import datetime
import dotenv

from modules.exceptions import YogaException


def aggregate_query(pipeline, client: pymongo.MongoClient):
    """Runs an aggregation query"""    
    collection = client.pam.yoga    
    return collection.aggregate(pipeline)


def display_message(msg: str, msg_type: str):
    """
    Display a message at the top of the app in the 'message_area' declared in main() using st.empty()
    msg_type: error, info, success, warning
    """
    message_area = st.session_state['message_area']
    method = getattr(message_area, msg_type)
    method(msg)    


def display_new_record_form(client: pymongo.MongoClient):
    """Displays the form used to enter new records."""
    with st.form("add_record_form"):
        st.header("Add New Record")
        st.date_input("Date", value=None, min_value=None, max_value=None, key="date_new", help=None, on_change=None, args=None, kwargs=None)
        st.number_input("Minutes", min_value=1, max_value=600, value=75, step=None, format=None, key="minutes_new", help=None, on_change=None)
        st.number_input("Pay", min_value=0, max_value=1000, value=30, step=None, format=None, key="pay_new", help=None, on_change=None)
        st.selectbox("Studio", ["Mindful Motion"], index=0, key="studio_new", help=None, on_change=None)
        st.selectbox("Type", get_yoga_class_types(client), index=0, key="class_new", help=None, on_change=None)
        st.number_input("Students", min_value=1, max_value=1000, value=2, step=None, format=None, key="students_new", help=None, on_change=None)        
        st.form_submit_button("Submit", on_click=process_new_record, kwargs={'client': client})     
            

def display_summary_data(data):
    """Disply summary of classes, hours, income and students in a dataframe"""
    total_minutes = data.get('total_minutes', 0)
    total_pay = data.get('total_pay', 0)
    sessions = data.get('sessions', 0)
    students = data.get('total_students', 0)
    data = [
        {"Classes": sessions, "Hours": f"{total_minutes / 60:.2f}", "Income": f"${total_pay:.2f}", "Students": students}        
    ]
    df = pd.DataFrame(data, index=['Totals'])
    st.header("Totals")
    df    
    
@st.cache_resource
def get_mongo_client(URI):
    """Returns a cached pymongo client that can be used in all sessions, threads, etc"""   
    return pymongo.MongoClient(URI)
    
    
def get_summary_data(client) -> dict:
    """Returns a dictionary with summary data for all classes taught."""
    pipeline = [
        {
            '$group': {
                '_id': None, # _id is required
                'total_minutes': {'$sum': '$duration'},
                'total_pay': {'$sum': '$pay'},
                'sessions': {'$count':{}},
                'total_students': {'$sum': '$students'}
            }
        }
    ]
    result = list(aggregate_query(pipeline, client))
    try:
        data = result[0]
    except IndexError as e:        
        raise YogaException(e)
    return data


def get_yoga_class_types(client: pymongo.MongoClient) -> list:
    """Get all class types for 'class' selectbox used for adding new records"""    
    collection = client.pam.class_types
    items= collection.find({}, {'_id': 0})
    return sorted([d.get('type') for d in items])
    

def insert_record(data: dict, client: pymongo.MongoClient):
    """""" 
    # data = {'date': datetime.datetime.now(), 'duration': 75, 'studio': "Mindful Motion", "type": 'Test', 'pay': 30, students: 101}    
    collection = client.pam.yoga
    try:    
        id = collection.insert_one(data).inserted_id
        return id
    except Exception as e:
        print(e)


def process_new_record(client: pymongo.MongoClient):
    """Collect form information and call insert_record() to add a new record into the database"""    
    minutes = st.session_state.minutes_new
    pay = st.session_state.pay_new
    studio = st.session_state.studio_new
    class_type = st.session_state.class_new
    students = st.session_state.students_new 
    date = datetime.datetime.combine(st.session_state.date_new, datetime.time(hour=0, minute=0, second=0))
    data = {'date': date, 'duration': minutes, 'studio': studio, "type": class_type, 'pay': pay, 'students': students}
    _id = insert_record(data, client)
    if _id:        
        st.balloons()        
    else:
        display_message('Error inserting record', 'error')
    

def main():
    dotenv.load_dotenv('.env')
    URI = os.environ.get('URI')    
    if not URI:
        message = 'Failed to get MongoDB URI from environment variables'
        st.error(message)
        raise ValueError(message)
        
    st.set_page_config(page_title='Yoga Tracker', page_icon="🙏", layout="centered", initial_sidebar_state="auto", menu_items=None)
    st.title('Yoga Teaching Tracker 🙏')    
    st.session_state['message_area'] = st.empty()    
    client = get_mongo_client(URI)
    try:   
        summary_data = get_summary_data(client)
        display_summary_data(summary_data)
    except YogaException as e:
        st.error(f"The app has encountered an error: {e}")

    display_new_record_form(client)
 
    
main()