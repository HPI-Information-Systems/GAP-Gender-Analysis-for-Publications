import streamlit as st
import pandas as pd
from sqlite3 import Connection, connect
from datetime import datetime

# Get general statistics about the data
def display_general_statistics(cursor):

    # Load all the general statistics out of the corresponding table
    with st.spinner("Loading general statistics..."):
        if "publication_count" not in st.session_state:
            sql = """SELECT Value\nFROM GeneralStatistics WHERE Name = "PublicationCount";"""
            cursor.execute(sql)
            st.session_state.publication_count = seperate_integer(
                cursor.fetchall()[0][0]
            )

        if "author_count" not in st.session_state:
            sql = """SELECT Value\nFROM GeneralStatistics WHERE Name = "AuthorCount";"""
            cursor.execute(sql)
            st.session_state.author_count = seperate_integer(cursor.fetchall()[0][0])
        if "affiliation_count" not in st.session_state:
            sql = """SELECT Value\nFROM GeneralStatistics WHERE Name = "AffiliationCount";"""
            cursor.execute(sql)
            st.session_state.affiliation_count = seperate_integer(
                cursor.fetchall()[0][0]
            )

        if "venue_count" not in st.session_state:
            sql = """SELECT Value\nFROM GeneralStatistics WHERE Name = "VenueCount";"""
            cursor.execute(sql)
            st.session_state.venue_count = seperate_integer(cursor.fetchall()[0][0])

        if "publication_author_count" not in st.session_state:
            sql = """SELECT Value\nFROM GeneralStatistics WHERE Name = "PublicationAuthorCount";"""
            cursor.execute(sql)
            st.session_state.publication_author_count = seperate_integer(
                cursor.fetchall()[0][0]
            )

        if "female_author_count" not in st.session_state:
            sql = """SELECT Value\nFROM GeneralStatistics WHERE Name = "FemaleAuthorCount";"""
            cursor.execute(sql)
            st.session_state.female_author_count = seperate_integer(
                cursor.fetchall()[0][0]
            )
        if "male_author_count" not in st.session_state:
            sql = """SELECT Value\nFROM GeneralStatistics WHERE Name = "MaleAuthorCount";"""
            cursor.execute(sql)
            st.session_state.male_author_count = seperate_integer(
                cursor.fetchall()[0][0]
            )

        if "unkown_author_count" not in st.session_state:
            sql = """SELECT Value\nFROM GeneralStatistics WHERE Name = "UnkownAuthorCount";"""
            cursor.execute(sql)
            st.session_state.unkown_author_count = seperate_integer(
                cursor.fetchall()[0][0]
            )

        if "last_time_updated" not in st.session_state:
            sql = """SELECT Value\nFROM GeneralStatistics WHERE Name = "Date";"""
            cursor.execute(sql)
            st.session_state.last_time_updated = cursor.fetchall()[0][0]

        if "authors_with_country" not in st.session_state:
            sql = """SELECT Value \nFROM GeneralStatistics WHERE Name = "AuthorCountWithCountry";"""
            cursor.execute(sql)
            st.session_state.authors_with_country = seperate_integer(
                cursor.fetchall()[0][0]
            )

        if "authors_without_country" not in st.session_state:
            sql = """SELECT Value \nFROM GeneralStatistics WHERE Name = "AuthorCountWithoutCountry";"""
            cursor.execute(sql)
            st.session_state.authors_without_country = seperate_integer(
                cursor.fetchall()[0][0]
            )

    # Display the data in a formatted way
    st.subheader("General statistics")

    col1, col2, col3 = st.columns(3)

    col1.markdown(
        f"**Number of publications**:  \n{st.session_state.publication_count}"
    )
    col2.markdown(f"**Number of distinct authors**:  \n{st.session_state.author_count}")
    col3.markdown(
        f"**Number of distinct affiliations**:  \n{st.session_state.affiliation_count}"
    )

    col1.markdown(f"**Number of distinct venues**:  \n{st.session_state.venue_count}")
    col2.markdown(
        f"**Number of distinct authorships**:  \n{st.session_state.publication_author_count}"
    )
    col3.markdown(
        f'**Last time updated database**:  \n{datetime.strptime(st.session_state.last_time_updated, "%Y-%m-%d %H:%M:%S").strftime("%d %b %Y")} '
    )

    col1.markdown(
        f"**Number of distinct woman authors**:  \n{st.session_state.female_author_count}"
    )
    col2.markdown(
        f"**Number of distinct man authors**:  \n{st.session_state.male_author_count}"
    )
    col3.markdown(
        f"**Number of distinct authors with unkown gender**:  \n{st.session_state.unkown_author_count}"
    )

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
        f"""**Gender determination**:  \n[GenderAPI](https://gender-api.com/)""",
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

    st.subheader("Instructions")
    st.markdown(
        """When clicking “Submit and Compare” you will see the number of publications where the first author, middle author (any but first or last), last author or any author is a woman author, based on their first name. In “Global Options” you can set a year range and select whether the data is shown in absolute or relative numbers. For "Relative numbers", the number of publications with women that match the criteria is compared with the global number (any gender).  \nThe continent filter and the country filter refer to the Country/Continent of the affiliation the author belongs to. Here, the data under consideration is reduced to those publications for which DBLP has affiliation information. \nFiltering by a specific venue (conference or journal) counts only the publications published in this journal. \nFiltering by Research Area groups the most important publications of each area into one graph. The data for the most important publications were taken from csrankings.org."""
    )
    st.markdown("""Acknowledgements: The initial ideas for these analyses are based on work together with Angela Bonifati, Michael Mior and Nele Noack: [VLDB Paper](http://www.vldb.org/pvldb/vol2/vldb09-98.pdf)""")
    st.markdown("""
    Contact: For questions and comments on the tool and the underlying data, please contact <a href="mailto: Felix.Naumann@hpi.de">Felix Naumann</a>. You are also welcome to visit our <a href="https://github.com/HPI-Information-Systems/GenderAnalysis">GitHub Page</a>.""", unsafe_allow_html=True)

def seperate_integer(string):
    return " ".join(
        [str(string[::-1][i : i + 3][::-1]) for i in range(0, len(string), 3)][::-1]
    )