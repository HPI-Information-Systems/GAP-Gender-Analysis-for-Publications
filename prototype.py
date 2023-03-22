from sqlite3 import connect

import pandas as pd
import streamlit as st
from PIL import Image

import general_statistics as gs
import graph_logic as gl

class GraphData:
    def __init__(self, name, isVisible, absoluteData, relativeData, color):
        self.name = name
        self.isVisible = isVisible
        self.absoluteData = absoluteData
        self.relativeData = relativeData
        self.color = color


def main():
    global logtxt

    # Basic page configurations
    img = Image.open("assets/page_icon.ico")
    st.set_page_config(
        page_title="GAP • Hasso-Plattner-Institut",
        page_icon=img,
        layout="wide",
    )

    st.title("GAP: Gender Analysis for Publications")
    st.markdown(
        "The GAP-Tool allows users to explore the gender diversity in computer science publications. By choosing different venues, countries, research areas, one can highlight differences within the community.  \n  *Please note*: The gender-data used by this tool are based on GenderAPI, which automatically classifies authors based on their first names. Thus, we distinguish only female and male gender and cannot reflect the full gender spectrum. Further, country information is based on the currently known affiliation from DBLP. It does not reflect the nationality of the author nor necessarily the affiliation of the author at the time of publication."
    )

    # Connect to SQLite database
    with st.spinner("Opening datasbase connection (This can take a while)..."):
        if "connection" not in st.session_state:
            st.session_state.connection = connect("gap.db", check_same_thread=False)

        # Create cursor object
        if "cursor" not in st.session_state:
            st.session_state.cursor = st.session_state.connection.cursor()

    # Initialize all the necessary session states
    with st.spinner("Initializing..."):

        if "y_columns" not in st.session_state:
            st.session_state.y_columns = []
        if "min_max" not in st.session_state:
            sql = """SELECT min(Year),max(Year) - 1 FROM AllTogether;"""
            st.session_state.min_max = query_action(sql, "check")[0]
        if "year_range" not in st.session_state:
            st.session_state.year_range = (1980, 2022)
        if "widget_data_representation" not in st.session_state:
            st.session_state.widget_data_representation = "Absolute numbers"

        if "widget_venues" not in st.session_state:
            st.session_state.widget_venues = ""
        if "widget_countries" not in st.session_state:
            st.session_state.widget_countries = ""
        if "widget_continents" not in st.session_state:
            st.session_state.widget_continents = []
        if "widget_publication_types" not in st.session_state:
            st.session_state.widget_publication_types = ""
        if "widget_author_position" not in st.session_state:
            st.session_state.widget_author_position = ""
        if "widget_research_areas" not in st.session_state:
            st.session_state.widget_research_areas = ""
        if "country_continent_dataframe" not in st.session_state:
            st.session_state.country_continent_dataframe = pd.DataFrame()
        if "is_first_run" not in st.session_state:
            st.session_state.is_first_run = True
        if "is_first_submit" not in st.session_state:
            st.session_state.is_first_submit = True

        if "graph_years" not in st.session_state:
            st.session_state.graph_years = None

        # Get all the filters out of the pre-calculated filter csv files
        with st.spinner("Loading filters..."):
            gl.display_filters()

    # If there is no graph created yet, display a placeholder
    if "graph" not in st.session_state or st.session_state.graph == None or not st.session_state.graph.data:

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

    # If there is data already, start process of showing the chart
    else:
        col1, col2 = st.columns([4, 1])

        # Show the data representation at the side
        widget_data_representation = col2.radio(
            "Select if the data will be shown in percentage or absolute numbers:",
            ["Absolute numbers", "Relative numbers"],
            index=1,
        )
        # Selector for the year range displayed in the chart
        col2.slider(
            "Select years range:",
            min_value=st.session_state.min_max[0],
            max_value=st.session_state.min_max[1],
            key="year_range",
            on_change=gl.update_year_range(),
        )
        if widget_data_representation != st.session_state.widget_data_representation:
            st.session_state.widget_data_representation = widget_data_representation
            gl.paint_graph()

        # Show the chart
        # Because it is connected to session state, it will automatically update
        # when "graph" session state updates
        col1.plotly_chart(st.session_state.graph, use_container_width=True, theme="streamlit")

    # Display the graph history checkboxes
    gl.display_graph_checkboxes()

    # Display statistics
    gs.display_general_statistics(st.session_state.cursor)

    display_footer()

    st.markdown(
        """
        <style>
            a:link, a:visited {
                color: #b1073b; 
                text-decoration: underline;
            }
            .css-13m4bxd, .e19lei0e1 {
                visibility: hidden;
            }

            .css-nps9tx, .e1m3hlzs0, .css-1p0bytv, .e1m3hlzs1 {
                visibility: collapse;
                height: 0px;
            }
        </style>
    """,
        unsafe_allow_html=True,
    )

    # Hide the hamburger menu provided by streamlit
    hide_hamburger_menu = """
        <style>
            #MainMenu {
                content:url("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/HPI_logo.svg/1200px-HPI_logo.svg.png"); 
                width: 50px;
                height: 50px;
                visibility: visible;
                pointer-events: none; 
            }
        </style>
    """
    st.markdown(hide_hamburger_menu, unsafe_allow_html=True)

    st.markdown(
        """
  <style>
    .css-1gx893w, .egzxvld2 {
      margin-top: -60px;
    }
  </style>
""",
        unsafe_allow_html=True,
    )


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


def display_footer():
    # Show a small divider
    st.markdown(
        '<hr style="height:1px;border:none;color:#D3D3D3;background-color:#D3D3D3;"/>',
        unsafe_allow_html=True,
    )

    # Show a reference to HPI
    st.markdown(
        '<h6 style=\'text-align: center;\'>Presented by <a href="https://hpi.de/naumann/home.html" style="color: #b1073b">HPI Information Systems Group</a></h6>',
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([2, 1, 2])
    col2.image("assets/hpi_logo.png")

    # Create empty lines with the approximate size of a heading
    # Don't use a heading, because this creates the bug that
    # The site scrolls down automatically at loading
    # -> This is something Streamlit does
    for i in range(1, 3):
        st.write("&nbsp;")

    # Legal references (Imprint, Privacy policy)
    st.markdown(
        """
        <p align="center"><a href='https://hpi.de/impressum.html' style='color: #b1073b'>Imprint</a><br><a href='https://hpi.de/datenschutz.html' style='color: #b1073b'>Privacy policy</a></p>""",
        unsafe_allow_html=True,
    )

    # Hide the streamlit footer and display
    # a very small HPI footer
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


if __name__ == "__main__":
    main()
