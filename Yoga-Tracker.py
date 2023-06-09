import os
import streamlit as st
import pandas as pd
import pymongo
import datetime
import dotenv

from modules.exceptions import YogaException


def aggregate_query(pipeline):
    """Runs an aggregation query"""
    client = st.session_state['mongo_client']
    collection = client.pam.yoga    
    return collection.aggregate(pipeline)


def display_new_record_form():
    """Displays the form used to enter new records."""
    with st.form("add_record_form"):
        st.header("Add a New Record")
        st.date_input("Date", value=None, min_value=None, max_value=None, key="date_new", help=None, on_change=None, args=None, kwargs=None)
        st.number_input("Minutes", min_value=1, max_value=600, value=75, step=None, format=None, key="minutes_new", help=None, on_change=None)
        st.number_input("Pay", min_value=0, max_value=1000, value=30, step=None, format=None, key="pay_new", help=None, on_change=None)
        st.selectbox("Studio", ["Mindful Motion"], index=0, key="studio_new", help=None, on_change=None)
        st.selectbox("Type", ["Restorative", "Test"], index=0, key="class_new", help=None, on_change=None)
        st.number_input("Students", min_value=1, max_value=1000, value=2, step=None, format=None, key="students_new", help=None, on_change=None)        
        st.form_submit_button("Submit", on_click=process_new_record)        
            
            
def process_new_record():
    """Collect form information and insert a new record into the database"""    
    minutes = st.session_state.minutes_new
    pay = st.session_state.pay_new
    studio = st.session_state.studio_new
    class_type = st.session_state.class_new
    students = st.session_state.students_new 
    date = datetime.datetime.combine(st.session_state.date_new, datetime.time(hour=0, minute=0, second=0))
    data = {'date': date, 'duration': minutes, 'studio': studio, "type": class_type, 'pay': pay, 'students': students}
    _id = insert_record(data)
    if _id:
        display_message('Success! New record added...', 'info')
        st.balloons()        
    else:
        display_message('Error inserting record', 'error')

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
    st.header("Summary")
    df


def get_all_records_as_dataframe() -> pd.DataFrame:
    """Revise to return all records and display in another function""" 
    records = get_data(query={}, projection={'_id': 0})    
    return pd.DataFrame(records)


def get_data(query, projection) -> pymongo.cursor.Cursor:
    """Retrieve data from mongo database. Cursor returns dictionaries during iteration."""
    client = st.session_state['mongo_client']
    collection = client.pam.yoga
    items = collection.find(query, projection)    
    return items   

@st.cache_resource
def get_mongo_client():
    URI = os.environ.get('URI')
    return pymongo.MongoClient(URI)
    
    
def get_summary_data() -> dict:
    """"""
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
    result = list(aggregate_query(pipeline))
    try:
        data = result[0]
    except IndexError as e:        
        raise YogaException(e)
    return data
    

def insert_record(data: dict):
    """""" 
    # data = {'date': datetime.datetime.now(), 'duration': 75, 'studio': "Mindful Motion", "type": 'Test', 'pay': 30, students: 101}
    client = st.session_state['mongo_client']
    collection = client.pam.yoga
    try:    
        id = collection.insert_one(data).inserted_id
        return id
    except Exception as e:
        print(e)  



def display_message(msg: str, msg_type: str):
    """
    Display a message at the top of the app in the 'message_area' declared in main() using st.empty()
    msg_type: error, info, success, warning
    """
    message_area = st.session_state['message_area']
    method = getattr(message_area, msg_type)
    method(msg) 
    

def main():
    dotenv.load_dotenv('.env')
    st.title('Yoga Teaching Tracker 🙏')
    message_area = st.empty()
    st.session_state['message_area'] = message_area
    
    if 'mongo_client' not in st.session_state:
        st.session_state['mongo_client'] = get_mongo_client()
    try:   
        summary_data = get_summary_data()
        display_summary_data(summary_data)
    except YogaException as e:
        st.error(f"The app has encountered an error: {e}")

    display_new_record_form()
    # all_df = get_all_records_as_dataframe()
    display_message('testing....', 'info')
    
    
main()