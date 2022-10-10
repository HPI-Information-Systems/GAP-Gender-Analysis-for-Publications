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
import streamlit as st
import pandas as pd
from sqlite3 import Connection
import prototype as pt
import plotly.figure_factory as ff
import plotly.express as px
from utils import log

# Display all the filters that the user can select
def display_filters(cursor):
    if "filters" not in st.session_state:
        st.session_state.filters = []
    if st.session_state.filters == [] or len(st.session_state.filters) < 4:

        # Concept for getting the filters:
        # 1. Read the csv
        # 2. Get the specific column
        # 3. Convert it to a list
        # 4. Sort the list ascending
        # 5. Convert the sorted list into a tuple for future processes
        #
        # Concwept applies to all the other filters as well

        country_continent_data = pd.read_csv("filters/Countries.csv")
        st.session_state.country_continent_dataframe = country_continent_data
        st.session_state.filters.append(
            tuple(sorted(list(set(country_continent_data["Continent"])))),
        )
        st.session_state.filters.append(
            tuple(sorted(list(country_continent_data["Country"]))),
        )

        st.session_state.filters.append(
            tuple(sorted(list(pd.read_csv("filters/Venues.csv")["Venue"]))),
        )

        st.session_state.filters.append(
            tuple(sorted(list(pd.read_csv("filters/PublicationTypes.csv")["PublicationType"]))),
        )

    placeholder = st.empty()
    col1, col2 = st.columns([1, 1])
    with col1:
        widget_cont = st.multiselect("Filter by Continent:", st.session_state.filters[0], key="cont")
        if widget_cont != st.session_state.widget_cont:
            st.session_state.widget_cont = widget_cont
            update_available_countries(cursor)
        widget_venue = st.multiselect("Filter by Conference/Journals:", st.session_state.filters[2], key="venue")
        widget_auth_pos = st.radio(
            "Filter by Woman Author Position:",
            (
                "First author woman",
                "Middle author woman",
                "Last author woman",
                "Any author woman",
            ),
            key="author_pos",
        )
    with col2:
        widget_count = st.multiselect("Filter by Country:", st.session_state.filters[1], key="country")
        widget_pub_type = st.multiselect(
            "Filter by publication type:",
            st.session_state.filters[3],
            key="publication_type",
        )
        
    # year-range selector for the drop-down lists for selection
    st.subheader("Global Options")
    year_range = st.slider(
        "Select years range:",
        min_value=st.session_state.min_max[0],
        max_value=st.session_state.min_max[1],
            key="year_range",
            on_change=update_year_range()
    )

    clear_history_button = st.button("Clear History", on_click=clear_history)
    button = st.button("Submit and Compare")
    if button:
        update_graph(
            widget_venue,
            widget_count,
            widget_cont,
            widget_pub_type,
            widget_auth_pos,
            st.session_state.widget_data_representation,
        )



def clear_history():
    st.session_state["auth_pos"] = "First author woman"
    st.session_state["cont"] = []
    st.session_state["venue"] = []
    st.session_state["country"] = []
    st.session_state["publication_type"] = []
    st.session_state["year_range"] = [2000, 2022]
    clear_graphs()    

def update_year_range():
    st.session_state.graph_years = list(
        range(
            list(st.session_state.year_range)[0],
            list(st.session_state.year_range)[1],
        )
    )
    paint_graph()

def update_available_countries(cursor):
    df = st.session_state.country_continent_dataframe

    filtered_countries = ()
    # Check if the continents to filter is not empty
    if not st.session_state.widget_cont:
        # If it is empty, display all countries
        filtered_countries = tuple(list(df["Country"]))
    else:
    # If it is not empty (the user filters by countries)
    # it will go through the whole list to filter
    # Get all the countries for each continent
    # And adds them into one result tuple
        for i in range(len(st.session_state.widget_cont)):
            filtered_countries = filtered_countries + tuple(
               list(df[df["Continent"] == st.session_state.widget_cont[i]]["Country"])
            )

    # At the end, the tuple will get sorted
    filtered_countries = sorted(filtered_countries)
    
    st.session_state.filters[1] = filtered_countries


def update_graph(
    widget_venue,
    widget_count,
    widget_cont,
    widget_pub_type,
    widget_auth_pos,
    widget_data_representation,
):
    (
        st.session_state.widget_venue,
        st.session_state.widget_count,
        st.session_state.widget_count,
        st.session_state.widget_pub_type,
        st.session_state.widget_auth_pos,
        st.session_state.widget_data_representation,
    ) = (
        widget_venue,
        widget_count,
        widget_cont,
        widget_pub_type,
        widget_auth_pos,
        widget_data_representation,
    )
    populate_graph(widget_venue, widget_count, widget_cont, widget_pub_type, widget_auth_pos)


# Creates Dynamic queries based on selection and
# runs the query to generate the count to populate the line graphs
def populate_graph(venue, country, cont, publication_type, auth_pos):
    sql_start = """SELECT Year, count(PublicationID) as count\nFROM AllTogether """
    sql_filter = """\nWHERE """
    sql_woman_filter = """ AND (Gender = "woman")"""
    sql_end = """\nGROUP BY Year;"""
    # the column/fiter names for each selection
    y_name = ""
    # change_year_range_df()
    # RETRIEVING OPTIONS AND FILLING UP THE DROP DOWN LISTS TO POPULATE GRAPH
    # creating query
    if venue == []:
        f_1 = ""
    else:  # for the 'Venue' of Publication
        f_1 = "("
        for v in venue:
            if v != venue[0]:
                f_1 = f_1 + " or "
            f_1 = f_1 + 'Venue = "' + str(v) + '"'
            y_name = y_name + str(v) + "/"
        f_1 = f_1 + ")"
    if country == []:
        f_2 = ""
    else:  # for the 'Country' of Author
        f_2 = "("
        for c in country:
            if c != country[0]:
                f_2 = f_2 + " or "
            f_2 = f_2 + 'Country = "' + str(c) + '"'
            y_name = y_name + str(c) + "/"
        f_2 = f_2 + ")"
    if cont == []:
        f_3 = ""
    else:  # for the 'Continent' of Author
        f_3 = "("
        for C in cont:
            if C != cont[0]:
                f_3 = f_3 + " or "
            f_3 = f_3 + 'Continent = "' + str(C) + '"'
            y_name = y_name + str(C) + "/"
        f_3 = f_3 + ")"
    if auth_pos == "":
        f_4 = ""
    else:
        f_4 = "("
        if auth_pos == "First author woman":
            f_4 = f_4 + 'Position = "1"'
            y_name = y_name + "First author woman/"
            # If any author, everyone, including first author
        elif auth_pos == "Last author woman":
            f_4 = f_4 + "CAST(Position AS INT) = AuthorCount"
            y_name = y_name + "Last author woman/"
        elif auth_pos == "Middle author woman":
            f_4 = f_4 + "Position > 1 AND CAST(Position AS INT) < AuthorCount"
            y_name = y_name + "Middle author woman/"
        else:
            f_4 = f_4 + 'Position = "1" OR Position <> "1"'
            y_name = y_name + "Any author woman/"
        f_4 = f_4 + ")"
    if publication_type == []:
        f_5 = ""
    else:
        f_5 = "("
        for p in publication_type:
            if p != publication_type[0]:
                f_5 = f_5 + " or "
            f_5 = f_5 + 'PublicationType = "' + str(p) + '"'
            y_name = y_name + str(p) + "/"
        f_5 = f_5 + ")"
    sql_logic = [f_1, f_2, f_3, f_4, f_5]
    newf = ""
    f_count = 0
    for f in sql_logic:
        if f != "":
            if f_count > 0:
                newf = newf + " AND "
            f_count += 1
            newf = newf + f
    # Getting data to graph format
    year = list(
        range(
            list(st.session_state.year_range)[0],
            list(st.session_state.year_range)[1],
        )
    )
    # Checks if the query was already requested
    if not [item for item in st.session_state.y_columns if y_name in item]:
        print(y_name)
        with st.spinner("Creating graph..."):
            sql = sql_start + sql_filter + newf + sql_woman_filter + sql_end
            sql_non_woman = sql_start + sql_filter + newf + sql_end
            out = pt.query_action(sql, "store")
            sql = sql_start + sql_filter + newf + sql_end
            print(sql)
            out_all = pt.query_action(sql, "store")
            available_years = list(range(st.session_state.min_max[0], st.session_state.min_max[1] + 1))
            for i in available_years:
                # Set years where value is null to 0, for future operations
                # and calculations
                if i not in out:
                    out.update({i: 0})
                if i not in out_all:
                    out_all.update({i: 0})
                # Calculate the percentages for "Relative Numbers"
                try:
                    out_all[i] = out[i] * 100 / out_all[i]
                except:
                    out_all[i] = 0
            # Sort the dicts ascending
            out = dict(sorted(out.items(), key=lambda x: x[0]))
            out_all = dict(sorted(out_all.items(), key=lambda x: x[0]))
            st.session_state.df_compare[0][y_name] = out
            st.session_state.df_compare[1][y_name] = out_all
            # construction of line_chart's data
            st.session_state.y_columns.append([y_name, True, out, out_all])
    st.session_state.graph_years = year
    paint_graph()


def paint_graph():
    """All the functionality for visualizing the collected data"""

    pd.options.plotting.backend = "plotly"
    line_graph_data = get_selected_df()
    line_graph_data = line_graph_data[
        (line_graph_data["Year"] >= min(st.session_state.graph_years))
        & (line_graph_data["Year"] <= max(st.session_state.graph_years))
    ]
    line_graph_data = line_graph_data.set_index("Year")

    fig = px.line(
        line_graph_data,
        color_discrete_sequence=[
            "#b1073b",
            "#636EFA",
            "#00CC96",
            "#AB63FA",
            "#FFA15A",
            "#19D3F3",
            "#FF6692",
            "#B6E880",
            "#FF97FF",
            "#FECB52",
        ],
    )
    fig.update_layout(legend_title="Filters")
    fig.update_yaxes(rangemode="tozero")
    fig.layout.plot_bgcolor = "#f1f3f6"
    if st.session_state.widget_data_representation == "Relative numbers":
        fig.update_layout(yaxis_title="Percentage", yaxis_ticksuffix="%")
    else:
        fig.update_layout(yaxis_title="Number of Publications")
    st.session_state.graph = fig


# def change_year_range_df():
#     st.session_state.line_chart = st.empty()
def get_selected_df():
    """Get all the graphs that the user selected in "Graph History" """
    true_df = pd.DataFrame()
    for i in range(len(st.session_state.y_columns)):
        if st.session_state.y_columns[i][1] is True:
            if st.session_state.widget_data_representation == "Absolute numbers":
                true_df.insert(
                    loc=0,
                    column=st.session_state.y_columns[i][0],
                    value=list(st.session_state.y_columns[i][2].values()),
                )
            else:
                true_df.insert(
                    loc=0,
                    column=st.session_state.y_columns[i][0],
                    value=list(st.session_state.y_columns[i][3].values()),
                )
    # Insert year column
    #
    # There will be enough values for every filter for sure,
    # because missing values from the original query were filled
    # with 0 in previous steps
    true_df.insert(
        loc=0,
        column="Year",
        value=list(
            range(st.session_state.min_max[0], st.session_state.min_max[1] + 1),
        ),
    )
    return true_df


def clear_graphs():
    """Clears the whole graph history including the selected filters"""
    st.session_state.df_compare = [pd.DataFrame(), pd.DataFrame()]
    st.session_state.y_columns = []
    st.session_state.graph = None


def display_graph_checkboxes():
    """Display the checkboxes for the Graph history with the logic of selecting/unselecting the checkboxes"""
    st.subheader("Graph history")
    if len(st.session_state.y_columns) != 0:
        st.session_state.y_columns.sort(key=lambda x: x[1], reverse=True)
        for i in range(len(st.session_state.y_columns)):
            globals()["graph_checkbox_%s" % i] = st.checkbox(
                st.session_state.y_columns[i][0],
                value=st.session_state.y_columns[i][1],
                key=f"graph_checkbox_{i}",
                on_change=change_graph_checkbox,
                args=(i,),
            )
            st.session_state.y_columns[i][1] = globals()["graph_checkbox_%s" % i]
            globals()["graph_checkbox_%s" % i] = globals()["graph_checkbox_%s" % i]


def change_graph_checkbox(i):
    if st.session_state[f"graph_checkbox_{i}"]:
        st.session_state.y_columns[i][1] = True
    if not st.session_state[f"graph_checkbox_{i}"]:
        st.session_state.y_columns[i][1] = False
    paint_graph()
