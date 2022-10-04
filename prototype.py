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

    img = Image.open("assets/page_icon.ico")
    st.set_page_config(
        page_title="GAP • Hasso-Plattner-Institut",
        page_icon=img,
        layout="wide",
        menu_items={"About": "htt"},
    )

    hide_hamburger_menu = """
        <style>
            #MainMenu {
                content:url("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/HPI_logo.svg/1200px-HPI_logo.svg.png"); 
                width: 50px;
                height: 50px;
                visibility: visible;      
            }
        </style>
    """

    st.markdown(hide_hamburger_menu, unsafe_allow_html=True)

    st.title("GAP: Gender Analysis for Publications")

    # Connect to SQLite database
    with st.spinner("Opening datasbase connection (This can take a while)..."):
        if "connection" not in st.session_state:
            st.session_state.connection = connect("gap.db", check_same_thread=False)

        # Create cursor object
        if "cursor" not in st.session_state:
            st.session_state.cursor = st.session_state.connection.cursor()

    with st.spinner("Loading filters 1/2..."):

        # TODO: Check if all session states are still needed
        if "df_compare" not in st.session_state:
            st.session_state.df_compare = [pd.DataFrame(), pd.DataFrame()]
        if "y_columns" not in st.session_state:
            st.session_state.y_columns = []
        if "min_max" not in st.session_state:
            sql = """SELECT min(Year),max(Year) FROM AllTogether;"""
            st.session_state.min_max = query_action(sql, "check")[0]
        if "year_range" not in st.session_state:
            st.session_state.year_range = (2000, 2022)
        if "widget_data_representation" not in st.session_state:
            st.session_state.widget_data_representation = "Absolute numbers"

        if "widget_venue" not in st.session_state:
            st.session_state.widget_venue = ""
        if "widget_count" not in st.session_state:
            st.session_state.widget_count = ""
        if "widget_cont" not in st.session_state:
            st.session_state.widget_cont = []
        if "widget_pub_type" not in st.session_state:
            st.session_state.widget_pub_type = ""
        if "widget_auth_pos" not in st.session_state:
            st.session_state.widget_auth_pos = ""
        if "widget_data_representation" not in st.session_state:
            st.session_state.widget_data_representation = "Absolute numbers"
        if "logtxtbox" not in st.session_state:
            st.session_state.logtxtbox = ""

        if "ui_widget_venue" not in st.session_state:
            st.session_state.ui_widget_venue = ""
        if "ui_widget_count" not in st.session_state:
            st.session_state.ui_widget_count = ""
        if "ui_widget_cont" not in st.session_state:
            st.session_state.ui_widget_cont = ""
        if "ui_widget_pub_type" not in st.session_state:
            st.session_state.ui_widget_pub_type = ""
        if "ui_widget_auth_pos" not in st.session_state:
            st.session_state.ui_widget_auth_pos = ""

        if "line_graph_data" not in st.session_state:
            st.session_state.line_graph_data = None
        if "graph_years" not in st.session_state:
            st.session_state.graph_years = None

    # query = st.session_state.cursor.execute('''
    # SELECT anzahl, COUNT(*) as anzahl2
    # FROM
    # (SELECT Venue, COUNT(*) as anzahl FROM AllTogether
    # GROUP BY Venue)
    # WHERE anzahl < 51
    # GROUP BY anzahl
    # ORDER BY anzahl DESC
    # ''')
    # print('----------------------------------')
    # print(query.fetchall())

    with st.spinner("Loading filters 2/2..."):
        gl.display_filters(st.session_state.cursor)

    if (
        "graph" not in st.session_state
        or st.session_state.graph == None
        or not st.session_state.graph.data
    ):
        st.markdown(
            "<h5 style='text-align: center;'>You have not selected any graphs yet </h5>",
            unsafe_allow_html=True,
        )

        image = Image.open("assets/no_data.png")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.write("")

        with col2:
            st.image(image, use_column_width=True)

        with col3:
            st.write("")
    else:
        col1, col2 = st.columns([4, 1])
        widget_data_representation = col2.radio(
            "Select if the data will be shown in percentage or absolute numbers:",
            ["Absolute numbers", "Relative numbers"],
            index=0,
        )  # on_change=change_data_representation()
        if widget_data_representation != st.session_state.widget_data_representation:
            st.session_state.widget_data_representation = widget_data_representation
            gl.populate_graph(
                st.session_state.connection,
                st.session_state.widget_venue,
                st.session_state.widget_count,
                st.session_state.widget_cont,
                st.session_state.widget_pub_type,
                st.session_state.widget_auth_pos,
            )
        col1.plotly_chart(st.session_state.graph, use_container_width=True)

    gl.display_graph_checkboxes()

    gs.display_general_statistics(st.session_state.cursor)

    display_footer()


def display_footer():
    st.header("")
    st.markdown(
        '<hr style="height:1px;border:none;color:#D3D3D3;background-color:#D3D3D3;"/>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "<h6 style='text-align: center;'>Presented by <a href=\"https://hpi.de/naumann/home.html\" style=\"color: #b1073b\">HPI Information Systems Group</a></h6>",
        unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2, 1, 2])
    col1.markdown("")
    col2.image("assets/hpi_logo.png")
    col3.markdown("")

    st.header("")
    st.markdown(
        "<style>a {display: grid; justify-content: center;} </style>  <a href='https://hpi.de/impressum.html' style='color: #b1073b'>Imprint</a> <a href='https://hpi.de/datenschutz.html' style='color: #b1073b'>Privacy policy</a>",
        unsafe_allow_html=True,
    )

    hide_streamlit_style = """
        <style>
        footer {visibility: hidden;}
        footer:after {
            content:'Made by HPI Information Systems Group'; 
            visibility: visible;
            display: block;
            position: relative;
            #background-color: red;
            padding: 5px;
            top: 2px;
        }
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)


def query_action(sql, action="run"):
    # global cursor
    # Executing the query
    st.session_state.cursor.execute(sql)

    if action != "run":
        store = {}
        # Fetching rows from the result table
        result = st.session_state.cursor.fetchall()
        if action == "check":
            return result
        for row in result:
            store[row[0]] = row[1]
        return store


if __name__ == "__main__":
    main()
    # Closing the connection
    # st.session_state.connection.close()
