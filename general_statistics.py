import streamlit as st
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import graph_logic

# Get general statistics about the data
def display_general_statistics(cursor):

    # Load all the general statistics out of the corresponding table
    with st.spinner("Loading general statistics..."):
        for statistic_name, session_state_key in zip(statistics_to_check, session_state_keys):
            if session_state_key not in st.session_state:
                value = get_statistic_from_db(cursor, statistic_name)

                if value is not None:
                    if session_state_key != "last_time_updated":
                        value = separate_integer(value)

                    st.session_state[session_state_key] = value
                else:
                    st.session_state[session_state_key] = ""


    # Display the data in a formatted way
    st.subheader("General statistics")

    col1, col2, col3 = st.columns(3)

    col1.markdown(f"**Number of publications**:  \n{st.session_state.publication_count}")
    col2.markdown(f"**Number of distinct authors**:  \n{st.session_state.author_count}")
    col3.markdown(f"**Number of distinct affiliations**:  \n{st.session_state.affiliation_count}")

    col1.markdown(f"**Number of distinct venues**:  \n{st.session_state.venue_count}")
    col2.markdown(f"**Number of distinct authorships**:  \n{st.session_state.publication_author_count}")
    col3.markdown(
        f'**Last time updated database**:  \n{datetime.strptime(st.session_state.last_time_updated, "%Y-%m-%d %H:%M:%S").strftime("%d %b %Y")} '
    )

    col1.markdown(f"**Number of distinct woman authors**:  \n{st.session_state.female_author_count}")
    col2.markdown(f"**Number of distinct man authors**:  \n{st.session_state.male_author_count}")
    col3.markdown(f"**Number of distinct authors with unknown gender**:  \n{st.session_state.unknown_author_count}")

    col1.markdown(
        f"**Authors with affiliation that has a country assigned**:  \n{st.session_state.authors_with_country}"
    )
    col2.markdown(
        f"**Authors with affiliation that has no country assigned**:  \n{st.session_state.authors_without_country}"
    )
    col3.markdown(
        f"""
        **Created by**:  \n[HPI Information Systems](https://hpi.de/naumann/home.html)
        """,
        unsafe_allow_html=True,
    )

    col1.markdown(
        f"""**Data source for publications**:  \n[dblp](https://dblp.org/)""",
        unsafe_allow_html=True,
    )
    col2.markdown(
        f"""**Gender determination**:  \n[Gender API](https://gender-api.com/)""",
        unsafe_allow_html=True,
    )

    col3.markdown(
        f"""**Research area determination**:  \n[CSRankings](https://csrankings.org/)""",
        unsafe_allow_html=True,
    )
    col1.markdown(
        f"""**Illustrations by**:  \n[Undraw](https://undraw.co/)""",
        unsafe_allow_html=True,
    )
    continents = ("Africa","Asia","Europe","North America","Oceania","South America",)
    selectedContinent = st.selectbox(
        "Select a continent to see it's statistics",
        continents
    ),

    selectedContinentInSessionStateKey = str(
        selectedContinent[0]).lower().replace(" ", "_")

    col1, col2, col3, col4= st.columns(4)
    numOfWomenInContinent = st.session_state[f'{selectedContinentInSessionStateKey}_female_author_count']
    numOfMenInContinent = st.session_state[f'{selectedContinentInSessionStateKey}_male_author_count']
    numOfUnknownInContinent = st.session_state[f'{selectedContinentInSessionStateKey}_unknown_author_count']
    # defines the first collumn
    col1.markdown(
        f"**Number of distinct woman authors in {selectedContinent[0]}**: {numOfWomenInContinent}",
        unsafe_allow_html=True,
    )
    col1.markdown(
        f"**Number of distinct man authors in {selectedContinent[0]}**: {numOfMenInContinent}",
        unsafe_allow_html=True,
    )

    col1.markdown(
        f"**Number of distinct authors with unknown gender in {selectedContinent[0]}**: {numOfUnknownInContinent}",
        unsafe_allow_html=True,
    )

    # plots the first pie chart
    fig1 = plt.figure()
    ax1 = fig1.add_subplot()
    ax1.pie(
        [# replace is used to remove the space, for example to convert "6 760" to "6760"
        numOfWomenInContinent.replace(" ",""), 
        numOfMenInContinent.replace(" ",""), 
        numOfUnknownInContinent.replace(" ","")
        ],
        labels=["Woman", "Man", "unknown"], autopct='%.1f%%', startangle=90, textprops={"fontsize": 15}, 
        colors=plt.cm.Dark2.colors[3:], wedgeprops={"linewidth":3}
    )
    col2.pyplot(fig1)

    # defines the third collumn
    # calculates the percentage of papers that were written in the selected continent
    continent_percentage = st.session_state.grouped_absolutes[selectedContinent[0]] / sum(st.session_state.grouped_absolutes.values())
    col3.markdown(
        f"**Percentage of papers published in {selectedContinent[0]}**: {f"{continent_percentage:.2%}"}",
        unsafe_allow_html=True
    )

    # plots the second pie chart
    fig2 = plt.figure()
    ax2 = fig2.add_subplot()
    ax2.pie(
        [
        continent_percentage,
        1 - continent_percentage],
        labels = [selectedContinent[0], "Other"], autopct = "%.1f%%", startangle = 90, textprops = {"fontsize": 15}, 
        colors=plt.cm.tab20.colors[4:], explode=(0.1,0)
    )
    col4.pyplot(fig2)

    st.subheader("Instructions")
    st.markdown(
        "When clicking \"Submit and Compare\" you will see the number of publications where the first author, middle author (any but first or last), last author or any author is a woman or man author, based on their first name as automatically determined by [Gender API](https://gender-api.com/). The identified gender is considered valid if the gender accuracy is greater than 50%. You can set a year range and select whether the data is shown in absolute or relative numbers. For \"Relative numbers\", the number of publications with woman/man that match the criteria is compared with the global number (any gender).  \n The continent filter and the country filter refer to the country/continent of the affiliation the author belongs to. Here, the data under consideration is reduced to those publications for which DBLP provides affiliation information. Filtering by a specific venue (conference or journal) counts only the publications published in this journal. Filtering by research area groups the most important publications of each area into one graph. The choice of conferences to represent research areas is based on [csrankings.org](https://csrankings.org)."
    )
    st.markdown(
        """Acknowledgements: The initial ideas for these analyses are based on work together with Angela Bonifati, Michael Mior and Nele Noack: [SIGMOD Reference](https://sigmodrecord.org/publications/sigmodRecord/2112/pdfs/06_Research_Bonifati.pdf)"""
    )
    st.markdown(
        """
    Contact: For questions and comments on the tool and the underlying data, please contact <a href="mailto: Felix.Naumann@hpi.de">Felix Naumann</a>. You are also welcome to visit our <a href="https://github.com/HPI-Information-Systems/GAP-Gender-Analysis-for-Publications">GitHub Page</a>.""",
        unsafe_allow_html=True,
    )


def get_statistic_from_db(cursor, statistic_name):
    sql = f"""SELECT Value\nFROM GeneralStatistics WHERE Name = "{statistic_name}";"""
    cursor.execute(sql)
    result = cursor.fetchall()

    if not result:
        return None

    return result[0][0] if result else None


statistics_to_check = [
    "PublicationCount",
    "AuthorCount",
    "AffiliationCount",
    "VenueCount",
    "PublicationAuthorCount",
    "FemaleAuthorCount",
    "MaleAuthorCount",
    "UnknownAuthorCount",
    "Date",
    "AuthorCountWithCountry",
    "AuthorCountWithoutCountry",
    "EuropeFemaleAuthorCount",
    "EuropeMaleAuthorCount",
    "EuropeUnknownAuthorCount",
    "AfricaFemaleAuthorCount",
    "AfricaMaleAuthorCount",
    "AfricaUnknownAuthorCount",
    "AsiaFemaleAuthorCount",
    "AsiaMaleAuthorCount",
    "AsiaUnknownAuthorCount",
    "North AmericaFemaleAuthorCount",
    "North AmericaMaleAuthorCount",
    "North AmericaUnknownAuthorCount",
    "OceaniaFemaleAuthorCount",
    "OceaniaMaleAuthorCount",
    "OceaniaUnknownAuthorCount",
    "South AmericaFemaleAuthorCount",
    "South AmericaMaleAuthorCount",
    "South AmericaUnknownAuthorCount",
]

session_state_keys = [
    "publication_count",
    "author_count",
    "affiliation_count",
    "venue_count",
    "publication_author_count",
    "female_author_count",
    "male_author_count",
    "unknown_author_count",
    "last_time_updated",
    "authors_with_country",
    "authors_without_country",
    "europe_female_author_count",
    "europe_male_author_count",
    "europe_unknown_author_count",
    "africa_female_author_count",
    "africa_male_author_count",
    "africa_unknown_author_count",
    "asia_female_author_count",
    "asia_male_author_count",
    "asia_unknown_author_count",
    "north_america_female_author_count",
    "north_america_male_author_count",
    "north_america_unknown_author_count",
    "oceania_female_author_count",
    "oceania_male_author_count",
    "oceania_unknown_author_count",
    "south_america_female_author_count",
    "south_america_male_author_count",
    "south_america_unknown_author_count",
]


def separate_integer(string):
    number = int(string)
    return " ".join([
        str(number)[::-1][i:i + 3][::-1]
        for i in range(0, len(str(number)), 3)
    ][::-1])
