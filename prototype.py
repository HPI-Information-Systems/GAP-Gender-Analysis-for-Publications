import pandas as pd
from sqlite3 import Connection, connect
from datetime import datetime
import streamlit as st
import numpy as np
import os
from PIL import Image

from utils import log
import graph_logic as gl
import general_statistics as gs

# Connect to SQLite database
conn = connect('gap.db')

# Create cursor object
cursor = conn.cursor()


def main():
    global logtxt

    img = Image.open('assets/page_icon.ico')
    st.set_page_config(page_title='GAP • Hasso-Plattner-Institut', page_icon=img, layout="wide")

    st.title('Gender Analysis for Publications')

    if 'df_compare' not in st.session_state:
        st.session_state.df_compare = [pd.DataFrame(), pd.DataFrame()]
    if 'y_columns' not in st.session_state:
        st.session_state.y_columns = []
    if 'min_max' not in st.session_state:
        sql = '''SELECT min(Year),max(Year) FROM AllTogether;'''
        st.session_state.min_max = query_action(sql, 'check')[0] 
    if 'year_range' not in st.session_state:
        st.session_state.year_range = [
            st.session_state.min_max[0], st.session_state.min_max[1]]
    if 'data_representation' not in st.session_state:
        st.session_state.data_representation = 'Absolute numbers'
    
    st.subheader("Number of conference publications per year")
    widget_venue, widget_count, widget_cont, widget_pub_type, widget_auth_pos, logtxtbox = gl.display_filters(cursor)
    
    if st.button('Submit and Compare'):
        gl.populate_graph(conn,
            widget_venue, widget_count, widget_cont, widget_pub_type, widget_auth_pos)
    gl.display_graph_checkboxes()

    gs.display_general_statistics(cursor)
    st.title("")
    st.markdown('<hr style="height:1px;border:none;color:#D3D3D3;background-color:#D3D3D3;"/>', unsafe_allow_html=True)
    st.markdown(
            "<h6 style='text-align: center;'>Presented to you by <a href=\"https://hpi.de/naumann/home.html\" style=\"color: #fe4c4a\">HPI Information Systems Group</a></h6>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2,1,2])
    col1.markdown("")
    col2.image('assets/hpi_logo.png')
    col3.markdown("")


    hide_streamlit_style = '''
            <style>
            footer {visibility: hidden;}
            footer:after {
	            content:'Made by HPI Information Systems Group'; 
	            visibility: visible;
                display: block;
                position: reslative;
                #background-color: red;
                padding: 5px;
                top: 2px;
            }
            </style>
            '''
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)


def query_action(sql, action='run'):
    global cursor
    # Executing the query
    cursor.execute(sql)

    if (action != 'run'):
        store = {}
        # Fetching rows from the result table
        result = cursor.fetchall()
        if(action == 'check'):
            return result
        for row in result:
            store[row[0]] = row[1]
        return(store)


if __name__ == "__main__":
    main()
    # Closing the connection
    conn.close()
