import os
import streamlit as st
import pandas as pd
import pymongo
import dotenv

from modules.exceptions import YogaException

dotenv.load_dotenv('.env')

@st.cache_resource
def get_mongo_client():
    DATABASE = "PAM"
    MONGO_PASSWORD = os.environ.get('MONGO_PASSWORD')
    URI = f"mongodb+srv://rc:{MONGO_PASSWORD}@apps.sdrf5qb.mongodb.net/{DATABASE}"   
    client = pymongo.MongoClient(URI)    
    return client

def get_data(query, projection) -> pymongo.cursor.Cursor:
    """Retrieve data from mongo database. Cursor returns dictionaries during iteration."""
    client = st.session_state['mongo_client']
    collection = client.pam.yoga
    items = collection.find(query, projection)    
    return items

def get_all_records():
    """Revise to return all records and display in another function""" 
    records = get_data(query={}, projection={'_id': 0})    
    df = pd.DataFrame(records)
    st.write(df)
    
    
def aggregate_query(pipeline):
    client = st.session_state['mongo_client']
    collection = client.pam.yoga    
    return collection.aggregate(pipeline)
    
    
def get_summary_data() -> dict:
    """"""
    pipeline = [
        {
            '$group': {
                '_id': None, # required
                'total_minutes': {'$sum': '$duration'},
                'total_pay': {'$sum': '$pay'},
                'sessions': {'$count':{}}
            }
        }
    ]
    result = list(aggregate_query(pipeline))
    try:
        data = result[0]
    except IndexError as e:        
        raise YogaException(e)
    return data
    
    
def display_summary_data(data):
    """"""
    total_minutes = data.get('total_minutes', 0)
    total_pay = data.get('total_pay', 0)
    sessions = data.get('sessions', 0)
    st.write(total_minutes)
    st.write(total_pay)
    st.write(sessions)


def main():
    st.header('Yoga Teaching Tracker')
    message_area = st.empty()
    
    if 'mongo_client' not in st.session_state:
        st.session_state['mongo_client'] = get_mongo_client()
    try:   
        summary_data = get_summary_data()
        display_summary_data(summary_data)
    except YogaException as e:
        st.error(f"The app has encountered an error: {e}")

    get_all_records()
    message_area.success('Success!!')
    st.balloons()
    
main()