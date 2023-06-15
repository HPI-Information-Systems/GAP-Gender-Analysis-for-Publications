import streamlit as st
import pandas as pd
import prototype as pt
import plotly.graph_objects as go
import re


class FilterData:
    def __init__(self, continents=[], countries=[], venues=[], publication_types=[], research_areas=[]):
        self.continents = continents
        self.countries = countries
        self.venues = venues
        self.publication_types = publication_types
        self.research_areas = research_areas

    def is_any_list_empty(self):
        if (
            not self.continents
            or not self.countries
            or not self.venues
            or not self.publication_types
            or not self.research_areas
        ):
            return True
        return False


# Display all the filters that the user can select
def display_filters():
    if "filters" not in st.session_state:
        st.session_state.filters = FilterData()
    if st.session_state.filters.is_any_list_empty():
        # Concept for getting the filters:
        # 1. Read the csv
        # 2. Get the specific column
        # 3. Convert it to a list
        # 4. Sort the list ascending
        # 5. Convert the sorted list into a tuple for future processes
        #
        # Concwept applies to all the other filters as well

        country_continent_data = pd.read_csv("filters/Countries.csv")
        country_continent_data = pd.concat(
            [
                country_continent_data,
                pd.DataFrame(
                    {
                        "Country": ["Unknown"],
                        "Continent": ["Unknown"],
                    },
                ),
            ],
        )
        st.session_state.country_continent_dataframe = country_continent_data

        venue_data = pd.read_csv("filters/Venues.csv")
        publication_types_data = pd.read_csv("filters/PublicationTypes.csv")
        research_areas_data = pd.read_csv("filters/ResearchAreas.csv")

        continents = sorted(list(set(country_continent_data["Continent"])))

        countries = sorted(list(country_continent_data["Country"]))

        venues = sorted(list(venue_data["Venue"]))

        publication_types = sorted(list(publication_types_data["PublicationType"]))

        research_areas = sorted(list(research_areas_data["ResearchArea"]))

        st.session_state.filters = FilterData(
            continents,
            countries,
            venues,
            publication_types,
            research_areas,
        )

    prefill_graph()

    with st.sidebar:
        st.subheader("Filters")
        widget_research_areas = st.multiselect(
            "Filter by Research Area$\\newline$(selected conferences):",
            st.session_state.filters.research_areas,
            key="research_area",
        )
        widget_publication_types = st.multiselect(
            "Filter by publication type:",
            st.session_state.filters.publication_types,
            key="publication_type",
        )
        widget_venues = st.multiselect("Filter by Conference/Journals:", st.session_state.filters.venues, key="venue")

        widget_continents = st.multiselect(
            "Filter by Continent$\\newline$(only authors with known affiliation):",
            st.session_state.filters.continents,
            key="cont",
        )
        if widget_continents != st.session_state.widget_continents:
            st.session_state.widget_continents = widget_continents
            update_available_countries()

        widget_countries = st.multiselect(
            "Filter by Country$\\newline$(only authors with known affiliation):",
            st.session_state.filters.countries,
            key="country",
        )

        widget_author_position = st.radio(
            "Filter by Gender Author Position:",
            (
                "First author woman",
                "Middle author woman",
                "Last author woman",
                "Any author woman",
                "First author man",
                "Middle author man",
                "Last author man",
                "Any author man",
            ),
            key="author_position",
        )

        st.button("Clear Filters", on_click=clear_filters)

        # Only submit the newest changes after the Button was clicked, prevents the
        # graph to update if the user hasn't done all filters yet
        button = st.button("**Submit and Compare**")
        if button:
            if st.session_state.is_first_submit:
                st.session_state.is_first_submit = False
            update_graph(
                widget_venues,
                widget_countries,
                widget_continents,
                widget_publication_types,
                widget_author_position,
                widget_research_areas,
                st.session_state.widget_data_representation,
            )


def clear_history():
    st.session_state.y_columns = []
    st.session_state.graph = None


def clear_filters():
    st.session_state["author_position"] = "First author woman"
    st.session_state["cont"] = []
    st.session_state["venue"] = []
    st.session_state["country"] = []
    st.session_state["publication_type"] = []
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
    if st.session_state.year_range[0] == st.session_state.year_range[1]:
        if st.session_state.year_range[0] < st.session_state.min_max[0] + 5:
            st.session_state["year_range"] = (
                st.session_state.year_range[0],
                st.session_state.year_range[1] + 5,
            )
        else:
            st.session_state["year_range"] = (
                st.session_state.year_range[0] - 5,
                st.session_state.year_range[1],
            )

    st.session_state.graph_years = list(
        range(
            st.session_state.year_range[0],
            # "+ 1" is to include the highest selected year.
            # If, for example, the highest year selected is 2023, it
            # wouldn't include 2023 in the query without the + 1
            st.session_state.year_range[1] + 1,
        )
    )
    paint_graph()


def update_available_countries():
    df = st.session_state.country_continent_dataframe

    filtered_countries = ()
    # Check if the continents to filter is not empty
    if not st.session_state.widget_continents:
        # If it is empty, return a selection for all countries
        filtered_countries = tuple(list(df["Country"]))
    else:
        # If it is not empty (the user filters by countries)
        # it will go through the whole list to filter
        # Get all the countries for each continent
        # And adds them into one result tuple
        for i in range(len(st.session_state.widget_continents)):
            filtered_countries = filtered_countries + tuple(
                list(df[df["Continent"] == st.session_state.widget_continents[i]]["Country"])
            )

    # At the end, the tuple will get sorted
    filtered_countries = sorted(filtered_countries)

    # And gets inserted into the country filter
    st.session_state.filters.countries = filtered_countries


def prefill_graph():
    if st.session_state.is_first_run == True:

        continents = ["Europe", "Asia", "North America", "South America", "Africa", "Oceania"]
        st.session_state.is_first_submit = False
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
        # st.session_state["cont"] = [continents[-1]]

        st.session_state.is_first_run = False
        st.session_state.is_first_submit = True


# Insert all the data gotten by the form into the session state and populate the graph
def update_graph(
    widget_venues,
    widget_countries,
    widget_continents,
    widget_publication_types,
    widget_author_position,
    widget_research_areas,
    widget_data_representation,
):
    (
        st.session_state.widget_venues,
        st.session_state.widget_countries,
        st.session_state.widget_continents,
        st.session_state.widget_publication_types,
        st.session_state.widget_author_position,
        st.session_state.widget_research_areas,
        st.session_state.widget_data_representation,
    ) = (
        widget_venues,
        widget_countries,
        widget_continents,
        widget_publication_types,
        widget_author_position,
        widget_research_areas,
        widget_data_representation,
    )
    populate_graph(
        widget_venues,
        widget_countries,
        widget_continents,
        widget_publication_types,
        widget_author_position,
        widget_research_areas,
    )


# Creates Dynamic queries based on selection and
# runs the query to generate the count to populate the line graphs
def populate_graph(venue, country, cont, publication_type, author_position, research_area):
    if st.session_state.is_first_submit:
        return

    # the column/fiter names for each selection
    y_name = ""

    # Creates query
    # For each available filter, check if the user has filtered something there
    # If so, go through every selection and add them as a filter group (statement OR statement OR...)
    def build_filter(filter_list, field_name, y_name):
        if not filter_list:
            return "", y_name

        filter_str = "({})".format(
            " or ".join(
                f'{field_name} = "{item}"' if item != "Unknown" else f"{field_name} IS NULL" for item in filter_list
            )
        )
        y_name += ", ".join(filter_list) + ", "
        return filter_str, y_name

    f_1, y_name = build_filter(venue, "Venue", y_name)
    f_2, y_name = build_filter(research_area, "ResearchArea", y_name)
    f_3, y_name = build_filter(country, "Country", y_name)
    f_4, y_name = build_filter(cont, "Continent", y_name)
    f_6, y_name = build_filter(publication_type, "PublicationType", y_name)

    author_position_filters = {
        "First author woman": ('Position = "1"', "woman"),
        "Last author woman": ("CAST(Position AS INT) = AuthorCount", "woman"),
        "Middle author woman": ("Position > 1 AND CAST(Position AS INT) < AuthorCount", "woman"),
        "First author man": ('Position = "1"', "man"),
        "Last author man": ("CAST(Position AS INT) = AuthorCount", "man"),
        "Middle author man": ("Position > 1 AND CAST(Position AS INT) < AuthorCount", "man"),
    }

    sql_gender = ""
    if author_position in {"Any author woman", "Any author man"}:
        f_5 = ""
        y_name += author_position
        sql_gender = "woman" if author_position == "Any author woman" else "man"
    elif author_position in author_position_filters:
        filter_str, sql_gender = author_position_filters[author_position]
        f_5 = f"({filter_str})"
        y_name += author_position
    else:
        f_5 = ""

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
    # that includes all the years within this range
    year = list(
        range(
            list(st.session_state.year_range)[0],
            list(st.session_state.year_range)[1] + 1,
        )
    )

    # Basic SQL query structure

    # The query creates a table with Year | Absolute | Relative columns
    # It first counts all the Publications that match the WHERE conditions and where at least one woman is found
    # The same is done for relative, but this also includes a calculation of the
    # percentage where the publications with woman gender are divided by all the unique publications
    sql_start = f"""SELECT 
    Year, 
    COUNT(DISTINCT 
        CASE 
        WHEN Gender = '{sql_gender}' THEN PublicationID 
        END
    ) AS Absolute, 
    COUNT(DISTINCT 
        CASE 
        WHEN Gender = '{sql_gender}' THEN PublicationID 
        END
    ) * 100 / COUNT(DISTINCT PublicationID) AS Relative
    FROM AllTogether
        """

    sql_filter_start = """\nWHERE """
    sql_end = """\nGROUP BY Year;"""

    # Checks if the query was already requested
    if not [item for item in st.session_state.y_columns if y_name == item.name]:
        with st.spinner("Creating graph..."):

            # If the query wasn't already requested, combine the different parts of it
            sql_query = sql_start + (sql_filter_start if newf else "") + newf + sql_end

            # Run the sql query and process it, so that it's ready for the graph
            grouped_absolutes, grouped_relatives = query_and_process(sql_query)

            # Set the specific graph color with colors and the modulo
            # of the length of colors. This ensures, that the graph color of
            # one specific graph does not change if another graph is added
            # The first color is the theme color, the other ones the standard
            # plotly colors
            COLORS = [
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
            color_index = len(st.session_state.y_columns) % len(COLORS)

            # Add all the gotten data into the y_columns session state,
            # That provides the data for the graph history, change between
            # Relative and Absolute numbers and some other features
            st.session_state.y_columns.append(
                pt.GraphData(
                    y_name,
                    True,
                    grouped_absolutes.sort_index().to_dict()["Absolute"],
                    grouped_relatives.sort_index().to_dict()["Relative"],
                    COLORS[color_index],
                ),
            )

    # The graph_years are important for displaying only the
    # Selected years on the chart
    st.session_state.graph_years = year

    # Visualize the collected data
    paint_graph()


@st.cache_data(max_entries=1000, show_spinner=False)
def query_and_process(sql_query):
    # Run the sql query and convert it to a pandas dataframe
    output = pd.read_sql(sql_query, st.session_state.connection)

    # Drop the columns that are not needed for the specific use case
    # And set the Year as the index
    # Remove 2023 from response as well, because the data is not relevant
    grouped_absolutes = output.drop("Relative", axis=1).set_index("Year").drop(2023, axis=0, errors="ignore")
    grouped_relatives = output.drop("Absolute", axis=1).set_index("Year").drop(2023, axis=0, errors="ignore")

    # Get all the available years that the user could have selected
    # and check if some of them are not in the output data
    #
    # It is necessary to have every year, including these with 0 values
    # inside of the list for further operation
    available_years = list(range(st.session_state.min_max[0], st.session_state.min_max[1] + 1))

    for i in available_years:
        if i not in grouped_absolutes.index:
            grouped_absolutes.loc[i] = {"Absolute": 0} # type: ignore
        if i not in grouped_relatives.index:
            grouped_relatives.loc[i] = {"Relative": 0} #type: ignore

    return grouped_absolutes, grouped_relatives


# Determines the font color of the hover
# Based on the luminance of the background color (trace color)
def get_hover_font_color(bg_color):
    # Convert hex color to RGB
    hex_color = re.search(r"^#?([A-Fa-f0-9]{6})$", bg_color)
    if hex_color:
        rgb_color = tuple(int(hex_color.group(1)[i : i + 2], 16) for i in (0, 2, 4))
    else:
        raise ValueError(f"Invalid hex color: {bg_color}")

    # Calculate the luminance
    r, g, b = [x / 255.0 for x in rgb_color]
    rgb_color = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in (r, g, b)]

    luminance = 0.2126 * rgb_color[0] + 0.7152 * rgb_color[1] + 0.0722 * rgb_color[2]

    # Choose font color based on luminance
    if luminance > 0.3:
        return "black"
    else:
        return "white"


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

    fig = go.Figure()

    data_column_names = list(line_graph_data.columns)

    # Create the figure
    fig = go.Figure()

    for idx, column in enumerate(data_column_names):
        if column in [y_column.name for y_column in st.session_state.y_columns]:
            index = st.session_state.y_columns[idx]
            value_title = (
                "Count"
                if st.session_state.widget_data_representation == "Absolute numbers"
                else "Share of Publications"
            )

                filtered_data = [(x, y) for x, y in zip(line_graph_data.index, line_graph_data[column]) if y != 0]
                filtered_x = [x for x, y in filtered_data]
                filtered_y = [y for x, y in filtered_data]
                customdata = [
                    f"{v}%" if (v == 0 or index.absoluteData[k] == 0) else
                    f"{v}% ({index.absoluteData[k]}/{int(index.absoluteData[k] / (v / 100))})"
                    for k, v in index.relativeData.items()
                    if st.session_state.graph_years[0] <= k <=
                    st.session_state.graph_years[-1] and line_graph_data[column][k] != 0
                ]

            else:
                filtered_data = line_graph_data
                filtered_x = line_graph_data.index
                filtered_y = line_graph_data[column]
                customdata = [
                    index.absoluteData[k]
                    for k, v in index.relativeData.items()
                    if st.session_state.graph_years[0] <= k <=
                    st.session_state.graph_years[-1]
                ]

            

            fig.add_trace(
                go.Scatter(
                    x=filtered_x,
                    y=filtered_y,
                    mode="lines",
                    name=column,
                    line_shape="spline",
                    line_smoothing=0.7,
                    meta=[column, value_title],
                    # The list to display the value alongside with the absolute numbers
                    # if the selected data representation is "Relative numbers"
                    customdata=customdata,
                    hovertemplate=
                    # Plotly's hovertemplate uses %{...} syntax to access data from the plot's data
                    # and customdata attributes. To access the name of the index, we use %{meta[0]}.
                    # To access the x-axis value, we use %{x}, and to access the y-axis value, we use
                    # %{customdata}.
                    "<b>%{meta[0]}</b><br>Year: %{x}<br>%{meta[1]}: %{customdata}<extra></extra>",
                    # We can customize the appearance of the hover label using the hoverlabel attribute.
                    # The bgcolor attribute sets the background color, and the font attribute sets
                    # the font properties.
                    hoverlabel=dict(
                        bgcolor=index.color,
                        font=dict(
                            color=get_hover_font_color(index.color),
                        ),
                    ),
                    # We can customize the appearance of the marker using the marker attribute.
                    # The color attribute sets the color of the marker.
                    marker=dict(color=st.session_state.y_columns[idx].color),
                ),
            )

    # # Add the traces
    # for idx, column in enumerate(data_column_names):
    #     if column in [
    #             y_column.name for y_column in st.session_state.y_columns
    #     ]:
    #         index = st.session_state.y_columns[idx]
    #         value_title = "Count" if st.session_state.widget_data_representation == "Absolute numbers" else "Share of Publications"
    #         fig.add_trace(
    #             go.Scatter(
    #                 x=line_graph_data.index,
    #                 y=line_graph_data[column],
    #                 mode='lines',
    #                 name=column,
    #                 line_shape='spline',
    #                 line_smoothing=0.7,
    #                 meta=[column, value_title],
    #                 # The list to display the value alongside with the absolute numbers
    #                 # if the selected data representation is "Relative numbers"
    #                 customdata=[f"{v}%" if st.session_state.widget_data_representation
    #                     == "Relative numbers" and
    #                     (v == 0 or index.absoluteData[k] == 0) else
    #                     f"{v}% ({index.absoluteData[k]}/{int(index.absoluteData[k] / (v / 100))})" if st.session_state.widget_data_representation
    #                     == "Relative numbers" else index.absoluteData[k]
    #                     for k, v in index.relativeData.items()
    #                     if st.session_state.graph_years[0] <= k <=
    #                     st.session_state.graph_years[-1]
    #                 ],
    #                 hovertemplate=

    #                 # Plotly's hovertemplate uses %{...} syntax to access data from the plot's data
    #                 # and customdata attributes. To access the name of the index, we use %{meta[0]}.
    #                 # To access the x-axis value, we use %{x}, and to access the y-axis value, we use
    #                 # %{customdata}.

    #                 '<b>%{meta[0]}</b><br>Year: %{x}<br>%{meta[1]}: %{customdata}<extra></extra>',

    #                 # We can customize the appearance of the hover label using the hoverlabel attribute.
    #                 # The bgcolor attribute sets the background color, and the font attribute sets
    #                 # the font properties.
    #                 hoverlabel=dict(
    #                     bgcolor=index.color,
    #                     font=dict(color=get_hover_font_color(index.color),),
    #                 ),

    #                 # We can customize the appearance of the marker using the marker attribute.
    #                 # The color attribute sets the color of the marker.
    #                 marker=dict(color=st.session_state.y_columns[idx].color),
    #             ), )

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
    fig.update_xaxes(tickformat="d")
    fig.update_yaxes(automargin=True, rangemode="tozero")

    if st.session_state.widget_data_representation == "Relative numbers":
        fig.update_layout(yaxis_title="Share of Publications", yaxis_ticksuffix="%")
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
        if st.session_state.y_columns[i].isVisible is True:

            # Access the different stored values.
            # If Absolute numbers is selected, get the data for absolute numbers
            # and the same for relative numbers
            if st.session_state.widget_data_representation == "Absolute numbers":
                true_df.insert(
                    loc=len(true_df.columns),
                    column=st.session_state.y_columns[i].name,
                    value=list(st.session_state.y_columns[i].absoluteData.values()),
                )
            else:
                true_df.insert(
                    loc=len(true_df.columns),
                    column=st.session_state.y_columns[i].name,
                    value=list(st.session_state.y_columns[i].relativeData.values()),
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
        st.session_state.y_columns.sort(key=lambda x: x.name, reverse=True)

        # Create dynamic variables for each graph checkbox,
        # So every checkbox can be handled individually
        for i in range(len(st.session_state.y_columns)):
            globals()["graph_checkbox_%s" % i] = st.checkbox(
                st.session_state.y_columns[i].name,
                value=st.session_state.y_columns[i].isVisible,
                # Setting the key makes this specific value
                # Accessible via the session state
                key=f"graph_checkbox_{i}",
                on_change=change_graph_checkbox,
                args=(i,),
            )
            st.session_state.y_columns[i].isVisible = globals()["graph_checkbox_%s" % i]

            # Set the variable to it's own value due to a bug by streamlit
            # Over which we have no influence on
            globals()["graph_checkbox_%s" % i] = globals()["graph_checkbox_%s" % i]

        st.button("Clear History", on_click=clear_history)


def change_graph_checkbox(i):
    if st.session_state[f"graph_checkbox_{i}"]:
        st.session_state.y_columns[i].isVisible = True
    if not st.session_state[f"graph_checkbox_{i}"]:
        st.session_state.y_columns[i].isVisible = False

    # After a checkbox has been changed,
    # Automatically repaint the graph
    paint_graph()
