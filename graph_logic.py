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
    if st.session_state.filters == [] or len(st.session_state.filters) < 5:

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

        st.session_state.filters.append(
            tuple(sorted(list(pd.read_csv("filters/ResearchAreas.csv")["ResearchArea"]))),
        )

    prefill_graph()

    with st.sidebar:
        st.subheader("Filters")
        widget_research_area = st.multiselect(
            "Filter by Research Areas:", st.session_state.filters[4], key="research_area"
        )
        widget_pub_type = st.multiselect(
            "Filter by publication type:",
            st.session_state.filters[3],
            key="publication_type",
        )
        widget_venue = st.multiselect("Filter by Conference/Journals:", st.session_state.filters[2], key="venue")

        widget_cont = st.multiselect("Filter by Continent:", st.session_state.filters[0], key="cont")
        if widget_cont != st.session_state.widget_cont:
            st.session_state.widget_cont = widget_cont
            update_available_countries()

        widget_count = st.multiselect("Filter by Country:", st.session_state.filters[1], key="country")

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

        clear_filters_button = st.button("Clear Filters", on_click=clear_filters)

        # Only submit the newest changes after the Button was clicked, prevents the
        # graph to update if the user hasn't done all filters yet
        button = st.button("**Submit and Compare**")
        if button:
            update_graph(
                widget_venue,
                widget_count,
                widget_cont,
                widget_pub_type,
                widget_auth_pos,
                widget_research_area,
                st.session_state.widget_data_representation,
            )


def clear_history():
    st.session_state.y_columns = []
    st.session_state.graph = None


def clear_filters():
    st.session_state["auth_pos"] = "First author woman"
    st.session_state["cont"] = []
    st.session_state["venue"] = []
    st.session_state["country"] = []
    st.session_state["publication_type"] = []
    # st.session_state["year_range"] = (2000, 2022)
    st.session_state["research_area"] = []


# Update the year range
# As soon as the year range changes, the graph
# will be rebuild
# The minimum value and maximum value
# automatically get converted into a list between
# these two values
def update_year_range():

    # When the user sets the year range to 2 exact same values, e.g. 2023 and 2023,
    # it will apply a range that is the selected year and the seelcted year - 5
    # If the user selects the minimum possible values twice, it will apply a range
    # with the selected year and the selected year + 5
    if list(st.session_state.year_range)[0] == list(st.session_state.year_range)[1]:
        if st.session_state.year_range[0] < st.session_state.min_max[0] + 5:
            st.session_state["year_range"] = (
                list(st.session_state.year_range)[0],
                list(st.session_state.year_range)[1] + 5,
            )
        else:
            st.session_state["year_range"] = (
                list(st.session_state.year_range)[0] - 5,
                list(st.session_state.year_range)[1],
            )

    st.session_state.graph_years = list(
        range(
            list(st.session_state.year_range)[0],
            # "+ 1" is to include the highest selected year. 
            # If, for example, the highest year selected is 2023, it
            # wouldn't include 2023 in the query without the + 1
            list(st.session_state.year_range)[1] + 1,
        )
    )
    paint_graph()


def update_available_countries():
    df = st.session_state.country_continent_dataframe

    filtered_countries = ()
    # Check if the continents to filter is not empty
    if not st.session_state.widget_cont:
        # If it is empty, return a selection for all countries
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

    # And gets inserted into the country filter
    st.session_state.filters[1] = filtered_countries


def prefill_graph():
    if st.session_state.is_first_run == True:

        continents = ["Europe", "Asia", "North America", "South America", "Africa", "Oceania"]
        for i in continents:
            update_graph(
                [],
                [],
                [i],
                [],
                "First author woman",
                [],
                "Relative numbers",
            )
        st.session_state["cont"] = ["Oceania"]

        st.session_state.is_first_run = False


# Insert all the data gotten by the form into the session state and populate the graph
def update_graph(
    widget_venue,
    widget_count,
    widget_cont,
    widget_pub_type,
    widget_auth_pos,
    widget_research_area,
    widget_data_representation,
):
    (
        st.session_state.widget_venue,
        st.session_state.widget_count,
        st.session_state.widget_cont,
        st.session_state.widget_pub_type,
        st.session_state.widget_auth_pos,
        st.session_state.widget_research_area,
        st.session_state.widget_data_representation,
    ) = (
        widget_venue,
        widget_count,
        widget_cont,
        widget_pub_type,
        widget_auth_pos,
        widget_research_area,
        widget_data_representation,
    )
    populate_graph(widget_venue, widget_count, widget_cont, widget_pub_type, widget_auth_pos, widget_research_area)


# Creates Dynamic queries based on selection and
# runs the query to generate the count to populate the line graphs
def populate_graph(venue, country, cont, publication_type, auth_pos, research_area):
    # Basic SQL query structure

    # The query creates a table with Year | Absolute | Relative columns
    # It first counts all the Publications that match the WHERE conditions and where at least one woman is found
    # The same is done for relative, but this also includes a calculation of the
    # percentage where the publications with woman gender are divided by all the unique publications
    sql_start = """SELECT 
  Year, 
  COUNT(DISTINCT 
    CASE 
      WHEN Gender = 'woman' THEN PublicationID 
    END
  ) AS Absolute, 
  COUNT(DISTINCT 
    CASE 
      WHEN Gender = 'woman' THEN PublicationID 
    END
  ) * 100 / COUNT(DISTINCT PublicationID) AS Relative
  FROM AllTogether
    """
    sql_filter_start = """\nWHERE """
    sql_end = """\nGROUP BY Year;"""

    # the column/fiter names for each selection
    y_name = ""

    # Creates query
    # For each available filter, check if the user has filtered something there
    # If so, go through every selection and add them as a filter group (statement OR statement OR...)
    if venue == []:
        f_1 = ""
    else:  # for the 'Venue' of Publication
        f_1 = "("
        for v in venue:
            if v != venue[0]:
                f_1 = f_1 + " or "
            f_1 = f_1 + 'Venue = "' + str(v) + '"'
            y_name = y_name + str(v) + ", "
        f_1 = f_1 + ")"
    if research_area == []:
        f_2 = ""
    else:
        f_2 = "("
        for ra in research_area:
            if ra != research_area[0]:
                f_2 = f_2 + " or "
            f_2 = f_2 + 'ResearchArea = "' + str(ra) + '"'
            y_name = y_name + str(ra) + ", "
        f_2 = f_2 + ")"
    if country == []:
        f_3 = ""
    else:  # for the 'Country' of Author
        f_3 = "("
        for c in country:
            if c != country[0]:
                f_3 = f_3 + " or "
            f_3 = f_3 + 'Country = "' + str(c) + '"'
            y_name = y_name + str(c) + ", "
        f_3 = f_3 + ")"
    if cont == []:
        f_4 = ""
    else:  # for the 'Continent' of Author
        f_4 = "("
        for C in cont:
            if C != cont[0]:
                f_4 = f_4 + " or "
            f_4 = f_4 + 'Continent = "' + str(C) + '"'
            y_name = y_name + str(C) + ", "
        f_4 = f_4 + ")"
    if publication_type == []:
        f_6 = ""
    else:
        f_6 = "("
        for p in publication_type:
            if p != publication_type[0]:
                f_6 = f_6 + " or "
            f_6 = f_6 + 'PublicationType = "' + str(p) + '"'
            y_name = y_name + str(p) + ", "
        f_6 = f_6 + ")"

    if auth_pos == "":
        f_5 = ""
    elif auth_pos == "Any author woman":
        f_5 = ""
        y_name = y_name + "Any author woman"
    else:
        f_5 = "("
        if auth_pos == "First author woman":
            f_5 = f_5 + 'Position = "1"'
            y_name = y_name + "First author woman"
            # If any author, everyone, including first author
        elif auth_pos == "Last author woman":
            f_5 = f_5 + "CAST(Position AS INT) = AuthorCount"
            y_name = y_name + "Last author woman"
        elif auth_pos == "Middle author woman":
            f_5 = f_5 + "Position > 1 AND CAST(Position AS INT) < AuthorCount"
            y_name = y_name + "Middle author woman"
        f_5 = f_5 + ")"
    sql_logic = [f_1, f_2, f_3, f_4, f_5, f_6]
    newf = ""
    f_count = 0

    # Combine each filter group with an AND operation
    if not all(not f for f in sql_logic):
        for f in sql_logic:
            if f != "":
                if f_count > 0:
                    newf = newf + " AND "
                f_count += 1
                newf = newf + f

    # Convert the data from the range selector into a list
    # that includes all the ears within this range
    year = list(
        range(
            list(st.session_state.year_range)[0],
            list(st.session_state.year_range)[1] + 1,
        ))

    # Checks if the query was already requested
    if not [item for item in st.session_state.y_columns if y_name in item]:
        with st.spinner("Creating graph..."):


            # If the query wasn't already requested, combine the different parts of it
            sql_query = sql_start + (sql_filter_start
                                         if newf else "") + newf + sql_end

            # Run the sql query and convert it to a pandas dataframe
            output = pd.read_sql(sql_query, st.session_state.connection)

            # Drop the columns that are not needed for the specific use case
            # And set the Year as the index
            grouped_absolute = output.drop('Relative', axis=1).set_index('Year')
            grouped_relative = output.drop(
                'Absolute', axis=1).set_index('Year')

            # Get all the available years that the user could have selected
            # and check if some of them are not in the output data
            #
            # It is necessary to have every year, including these with 0 values
            # inside of the list for further operation
            available_years = list(
                range(st.session_state.min_max[0],
                      st.session_state.min_max[1] + 1))


            for i in available_years:
                if i not in grouped_absolute.index:
                    grouped_absolute.loc[i] = {'Absolute': 0}
                if i not in grouped_relative.index:
                    grouped_relative.loc[i] = {'Relative': 0}

            # Set the specific graph color with colors and the modulo
            # of the length of colors. This ensures, that the graph color of
            # one specific graph does not change if another graph is added
            # The first color is the theme color, the other ones the standard
            # plotly colors
            colors = [
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
            ]
            color_index = len(st.session_state.y_columns) % len(colors)

            # Add all the gotten data into the y_columns session state,
            # That provides the data for the graph history, change between
            # Relative and Absolute numbers and some other features
            st.session_state.y_columns.append([
                y_name, True,
                grouped_absolute.sort_index().to_dict()['Absolute'],
                grouped_relative.sort_index().to_dict()['Relative'], colors[color_index]
            ])

    # The graph_years are important for displaying only the
    # Selected years on the chart
    st.session_state.graph_years = year

    # Visualize the collected data
    paint_graph()


# Functionality for visualizing the collected data
def paint_graph():

    # Set pandas graph processing to plotly library
    pd.options.plotting.backend = "plotly"

    # Get only the dataframes that were
    # selected in graph history
    line_graph_data = get_selected_df()

    # Filter the data by the year range, that the user wants
    # to be displayed
    line_graph_data = line_graph_data[
        (line_graph_data["Year"] >= min(st.session_state.graph_years))
        & (line_graph_data["Year"] <= max(st.session_state.graph_years))
    ]

    line_graph_data = line_graph_data.set_index("Year")

    # --- Customizing the chart---
    colors = []

    # Select the y_columns that are also in the dataframe
    # And get the specific colors of them
    data_column_names = list(line_graph_data.columns)
    y_column_names = [i[0] for i in st.session_state.y_columns]
    for i in range(len(st.session_state.y_columns)):
        if st.session_state.y_columns[i][0] in data_column_names:
            colors.append(st.session_state.y_columns[i][4])

    fig = px.line(
        line_graph_data,
        color_discrete_sequence=colors,
        # markers=True,
    )

    # Set legend title, y-axis to start with 0 etc.
    fig.update_layout(
        font_size=13,
        legend_title="Filters (click to toggle on/off)",
        autosize=True,
        height=500,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=-0.1,
            xanchor="left",
            x=0,
        ),
    )

    fig.update_yaxes(automargin=True)

    fig.update_yaxes(rangemode="tozero"),
    fig.layout.plot_bgcolor = "#f1f3f6"

    # If Relative numbers is selected, set the y-Axis title to "Percentage"
    # And add to each displayed number a % symbol
    # If Absolute numbers is selected, set the y-axis title to "Number of Publications"
    if st.session_state.widget_data_representation == "Relative numbers":
        fig.update_layout(yaxis_title="Percentage", yaxis_ticksuffix="%")
    else:
        fig.update_layout(yaxis_title="Number of Publications")

    # Update the session state graph
    # -> Because of this update, it will
    # automatically rebuild the chart
    st.session_state.graph = fig


# Get all the graphs that the user selected in "Graph History"
def get_selected_df():
    true_df = pd.DataFrame()

    # Go through every possible dataframe
    for i in range(len(st.session_state.y_columns)):

        # If the user has selected the graph in Graph history,
        # Do further operations for displaying it
        if st.session_state.y_columns[i][1] is True:

            # Access the different stored values.
            # If Absolute numbers is selected, get the data for absolute numbers
            # and the same for relative numbers
            if st.session_state.widget_data_representation == "Absolute numbers":
                true_df.insert(
                    loc=len(true_df.columns),
                    column=st.session_state.y_columns[i][0],
                    value=list(st.session_state.y_columns[i][2].values()),
                )
            else:
                true_df.insert(
                    loc=len(true_df.columns),
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


# Display the checkboxes for the Graph history with the logic of selecting/unselecting the checkboxes
def display_graph_checkboxes():
    if len(st.session_state.y_columns) != 0:
        st.subheader("Graph history")

        # Sort the graph names ascending
        st.session_state.y_columns.sort(key=lambda x: x[1], reverse=True)

        # Create dynamic variables for each graph checkbox,
        # So every checkbox can be handled individually
        for i in range(len(st.session_state.y_columns)):
            globals()["graph_checkbox_%s" % i] = st.checkbox(
                st.session_state.y_columns[i][0],
                value=st.session_state.y_columns[i][1],
                # Setting the key makes this specific value
                # Accessible via the session state
                key=f"graph_checkbox_{i}",
                on_change=change_graph_checkbox,
                args=(i,),
            )
            st.session_state.y_columns[i][1] = globals()["graph_checkbox_%s" % i]

            # Set the variable to it's own value due to a bug by streamlit
            # Over which we have no influence on
            globals()["graph_checkbox_%s" % i] = globals()["graph_checkbox_%s" % i]

        clear_history_button = st.button("Clear History", on_click=clear_history)


def change_graph_checkbox(i):
    if st.session_state[f"graph_checkbox_{i}"]:
        st.session_state.y_columns[i][1] = True
    if not st.session_state[f"graph_checkbox_{i}"]:
        st.session_state.y_columns[i][1] = False

    # After a checkbox has been changed,
    # Automatically repaint the graph
    paint_graph()
