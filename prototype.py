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




def main():
    global logtxt

    img = Image.open('assets/page_icon.ico')
    st.set_page_config(
        page_title='GAP • Hasso-Plattner-Institut', page_icon=img, layout="wide")

    st.title('GAP: Gender Analysis for Publications')

    # Connect to SQLite database
    with st.spinner('Opening datasbase connection (This can take a while)...'):
        if 'connection' not in st.session_state:
            st.session_state.connection = connect('gap.db', check_same_thread=False)

        # Create cursor object
        if 'cursor' not in st.session_state:
            st.session_state.cursor = st.session_state.connection.cursor()

    with st.spinner('Loading filters...'):
        if 'df_compare' not in st.session_state:
            st.session_state.df_compare = [pd.DataFrame(), pd.DataFrame()]
        if 'y_columns' not in st.session_state:
            st.session_state.y_columns = []
        if 'min_max' not in st.session_state:
            sql = '''SELECT min(Year),max(Year) FROM AllTogether;'''
            st.session_state.min_max = query_action(sql, 'check')[0]
        if 'year_range' not in st.session_state:
            st.session_state.year_range = [
                2000, 2022]
        if 'pyr' not in st.session_state:
            st.session_state.pyr = [
                2000, 2022]
        if 'data_representation' not in st.session_state:
            st.session_state.data_representation = 'Absolute numbers'

    st.subheader("Filters")
    with st.spinner('Loading filters...'):
        widget_venue, widget_count, widget_cont, widget_pub_type, widget_auth_pos, logtxtbox = gl.display_filters(
            st.session_state.cursor)

    col1, col2 = st.columns([1, 3])
    button = col1.button('Submit and Compare')
    if button:
        gl.populate_graph(st.session_state.connection,
                          widget_venue, widget_count, widget_cont, widget_pub_type, widget_auth_pos)

    if st.session_state.year_range != st.session_state.pyr:
        col2.markdown('<span style="color: orange;">Warning: The year range has changed. Clicking "Submit and Compare" will delete the previous graph history. We are working on improvements</span>', unsafe_allow_html=True)
    gl.display_graph_checkboxes()

    gs.display_general_statistics(st.session_state.cursor)
    display_footer()
    

def display_footer():
    st.title("")
    st.markdown('<hr style="height:1px;border:none;color:#D3D3D3;background-color:#D3D3D3;"/>',
                unsafe_allow_html=True)
    st.markdown(
        "<h6 style='text-align: center;'>Presented to you by <a href=\"https://hpi.de/naumann/home.html\" style=\"color: #fe4c4a\">HPI Information Systems Group</a></h6>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2, 1, 2])
    col1.markdown("")
    col2.image('assets/hpi_logo.png')
    col3.markdown("")

    st.title("")
    col1, col2 = st.columns(2)
    col1.markdown("<a href='https://hpi.de/impressum.html' style='color: #fe4c4a'>Imprint</a>", unsafe_allow_html=True)
    col2.markdown("<a href='https://hpi.de/datenschutz.html' style='color: #fe4c4a'>Privacy policy</a>", unsafe_allow_html=True)


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
    #global cursor
    # Executing the query
    st.session_state.cursor.execute(sql)

    if (action != 'run'):
        store = {}
        # Fetching rows from the result table
        result = st.session_state.cursor.fetchall()
        if(action == 'check'):
            return result
        for row in result:
            store[row[0]] = row[1]
        return(store)


if __name__ == "__main__":
    main()
    # Closing the connection
    #st.session_state.connection.close()
