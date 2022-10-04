import streamlit as st
import pandas as pd
from sqlite3 import Connection, connect
from datetime import datetime

# Get general statistics about the data


def display_general_statistics(cursor):
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

    st.subheader("General statistics & Important information")

    col1, col2, col3 = st.columns(3)

    col1.markdown(f"**Publications count:**  \n{st.session_state.publication_count}")
    col2.markdown(f"**Author count:**  \n{st.session_state.author_count}")
    col3.markdown(f"**Affiliation count:**  \n{st.session_state.affiliation_count}")

    col1.markdown(f"**Venue count:**  \n{st.session_state.venue_count}")
    col2.markdown(
        f"**Publication Author count**:  \n{st.session_state.publication_author_count}"
    )
    col3.markdown(
        f'**Last time updated database:**  \n{datetime.strptime(st.session_state.last_time_updated, "%Y-%m-%d %H:%M:%S").strftime("%d %b %Y")}'
    )

    col1.markdown(f"**Woman author count**:  \n{st.session_state.female_author_count}")
    col2.markdown(f"**Man author count**:  \n{st.session_state.male_author_count}")
    col3.markdown(
        f"**Authors with unkown gender**:  \n{st.session_state.unkown_author_count}"
    )

    col1.markdown(
        f"**Authors with Affiliation that has a Country assigned:**  \n{st.session_state.authors_with_country}"
    )
    col2.markdown(
        f"**Authors with Affiliation that has not a Country assigned:**  \n{st.session_state.authors_without_country}"
    )
    col3.markdown(
        f"**Created by:**  \n[HPI Information Systems](https://hpi.de/naumann/home.html)"
    )

    col1.markdown(f"**Data source:**  \n[dblp](https://dblp.org/)")
    col2.markdown(f"**Gender determination:**  \n[GenderAPI](https://gender-api.com/)")
    col3.markdown(f"**Illustrations by:**  \n[Undraw](https://undraw.co/)")

    st.markdown("<h5>Important information</h5>", unsafe_allow_html=True)
    st.markdown(
        """Dear User,  \nwe hope you like our gender analysis tool. Our goal is to provide you the best insights about the data that we show. When clicking “Submit and Compare” you will see the number of publications where the First author, Middle author, Last author or any author (depends on your selection) is a woman. In “Global Options” you can set a year range and select whether the data is shown in absolute numbers or in per cent. If you select "Relative numbers", the number of publications with women that match the criteria will be compared with the global number (any gender).  \nThe continent filter and the country filter refer to the Country/Continent of the affiliation the author belongs to.  \nFiltering by Conference/Journal means, that you only count the publications published in this journal."""
    )


def seperate_integer(string):
    return " ".join(
        [str(string[::-1][i : i + 3][::-1]) for i in range(0, len(string), 3)][::-1]
    )
