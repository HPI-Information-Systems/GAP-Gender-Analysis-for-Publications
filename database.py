from lxml import etree
import pandas as pd
from sqlite3 import Connection, connect
from utils import log
from datetime import datetime
import os
import ast
import re
import glob
import pathlib

if not os.path.exists("csv/db"):
    os.makedirs("csv/db")

if not os.path.exists("csv/GenderAPI/unprocessed"):
    os.makedirs("csv/GenderAPI/unprocessed")

DB = "gap.db"

# For preventing pandas from interpreting Namibia's country code 'NA' as NaN value
NA_VALUES = [
    "''",
    "#N/A",
    "#N/A N/A",
    "#NA",
    "-1.#IND",
    "-1.#QNAN",
    "-NaN",
    "-nan",
    "1.#IND",
    "1.#QNAN",
    "<NA>",
    "N/A",
    "NULL",
    "NaN",
    "n/a",
    "nan",
    "null",
]
COUNTRY_VARIATIONS = pd.read_csv(
    "country_name_variations.csv", keep_default_na=False, na_values=NA_VALUES
)
COUNTRIES = pd.read_csv(
    "countries_unique.csv", keep_default_na=False, na_values=NA_VALUES
)
CONTINENTS = pd.read_csv("continents.csv", keep_default_na=False, na_values=NA_VALUES)
# The, Zu, De, Den, Der, Del, Ul, Al, Da, El, Des, Di, Ten, Ter, Van, Von, Zur, Du, Das, Le actually are first names
NO_MIDDLE_NAMES = [
    "van",
    "von",
    "zur",
    "aus",
    "dem",
    "den",
    "der",
    "del",
    "de",
    "la",
    "La",
    "las",
    "le",
    "los",
    "ul",
    "al",
    "da",
    "el",
    "vom",
    "Vom",
    "auf",
    "Auf",
    "des",
    "di",
    "dos",
    "du",
    "ten",
    "ter",
    "van't",
    "Van't",
    "of",
    "het",
    "the",
    "af",
    "til",
    "zu",
    "do",
    "das",
    "Sri",
    "Si",
    "della",
    "Della",
    "degli",
    "Degli",
    "Mc",
    "Mac",
    "und",
    "on",
    "in't",
    "i",
    "ka",
    "t",
]


def main():
    conn = connect(DB)

    drop(conn, 'PublicationAuthor')
    drop(conn, 'Publication')
    drop(conn, 'Venue')
    drop(conn, 'AuthorName')
    drop(conn, 'Author')
    drop(conn, 'GenderAPIResults')
    drop(conn, 'Affiliation')
    drop(conn, 'Country')
    drop(conn, 'AllTogether')
    drop(conn, "GeneralStatistics")
    drop(conn, "Filters")

    drop_index(conn, 'all_together_index')

    # Do not enable the foreign key constraint checks before dropping the tables as this would make the dropping process
    # incredibly slow
    enable_foreign_key_constraints(conn)

    fill_countries(conn, to_csv=True)
    fill_affiliations(conn, to_csv=True)
    fill_gender_api_results(conn)
    fill_authors(conn, to_csv=True)  # Internally triggers fill_author_names()
    fill_venues(conn, to_csv=True)
    fill_publications(conn, to_csv=True)  # Internally triggers fill_publication_author_relationships()
    
    fill_all_together(conn)

    # # Generate a csv file of first names with unknown gender that can be passed to the GenderAPI
    get_unknown_first_names(conn)

    create_indices(conn)
    insert_research_areas(conn)

    fill_statistics(conn)
    fill_filters(conn)


def drop(conn, table):
    conn.execute(f"DROP TABLE IF EXISTS {table};")


def drop_index(conn, index):
    conn.execute(f"DROP INDEX IF EXISTS {index};")


def enable_foreign_key_constraints(conn):
    conn.execute("PRAGMA foreign_keys = ON;")


def fill_countries(conn: Connection, to_csv=False):
    """
    Get list of countries with unique names and country codes from countries_unique.csv, add continents and save
    everything to table 'Country' by using the given connection conn.
    :param conn:    sqlite3.Connection
    :param to_csv:  bool, whether to save the resulting table to csv/db/Country.csv, too.
    :return:
    """
    log("Progress of filling countries started")
    Country = COUNTRIES.merge(CONTINENTS, on="Code")
    log("Continents to country list added")

    # Save countries to database
    Country.rename(
        {"Country": "DisplayName", "Code": "CountryCode"}, axis="columns", inplace=True
    )

    if to_csv:
        Country.to_csv("csv/db/Country.csv", index=False)

    conn.execute(
        """
        CREATE TABLE Country(
            CountryCode TEXT PRIMARY KEY NOT NULL,
            DisplayName TEXT NOT NULL,
            Continent TEXT NOT NULL
        );
    """
    )

    Country.to_sql("Country", con=conn, if_exists="append", index=False)
    log("Countries written to database")


def fill_affiliations(conn: Connection, to_csv=False):
    """
    Parse unique affiliations from dblp.xml, extract their country (usually given at the end of an affiliation string),
    identify their country code and save everything to table 'Affiliation' by using the given connection conn.
    :param conn:    sqlite3.Connection
    :param to_csv:  bool, whether to save the resulting table to csv/db/Affiliation.csv, too.
    """
    log("Progress of filling affiliations started")
    context = etree.iterparse(
        source="dblp/dblp.xml", dtd_validation=True, load_dtd=True
    )

    # Extract affiliations from dblp xml
    raw_affiliations = set()
    for action, elem in context:
        if (
            elem.tag == "note"
            and elem.get("type") == "affiliation"
            and elem.text is not None
        ):
            # Remove leading and trailing spaces
            raw_affiliations.add(elem.text.strip())
        elem.clear()
    log("Affiliations from dblp extracted")

    # Extract country from affiliations and find country code
    affiliations = []
    for affiliation in raw_affiliations:
        affiliations.append(_assign_country_code(affiliation))
    log("Countries to affiliations added")

    # Save affiliations to database
    Affiliation = pd.DataFrame(affiliations, columns=["FullAffiliation", "CountryCode"])
    Affiliation.sort_values("FullAffiliation", inplace=True, ignore_index=True)

    if to_csv:
        Affiliation.to_csv("csv/db/Affiliation.csv", index=False)

    conn.execute(
        """
        CREATE TABLE Affiliation(
            AffiliationID INT NOT NULL PRIMARY KEY,
            FullAffiliation TEXT NOT NULL UNIQUE,
            Type TEXT,
            CountryCode TEXT,
            FOREIGN KEY(CountryCode) REFERENCES Country(CountryCode) ON DELETE CASCADE
        );
    """
    )
    Affiliation.to_sql(
        "Affiliation", con=conn, if_exists="append", index_label="AffiliationID"
    )
    log("Affiliations written to database")


def fill_gender_api_results(
    conn: Connection,
    gapi_path="csv/GenderAPI/",
):
    """
    Read csv file given under gapi_path or, if it's a directory, read each csv file located there, concatenate them,
    drop duplicates and save everything to table 'GenderAPIResults' by using the given connection conn.
    This function assumes all csv files in gapi_path to have semicolons as separators as that's the way they are
    returned by the GenderAPI.
    :param conn:        sqlite3.Connection
    :param gapi_path:   relative path to csv file(s) returned by the GenderAPI
    """
    log("Progress of filling GenderAPI results started")

    if ".csv" in gapi_path:
        GenderAPIResults = pd.read_csv(gapi_path, sep=";")
    else:
        glob_path = os.path.join(gapi_path, "*.csv")
        GenderAPIResults = pd.DataFrame()
        for csv_file in glob.glob(glob_path):
            GenderAPIResults = pd.concat(
                [GenderAPIResults, pd.read_csv(csv_file, sep=";")]
            )

    # Remove duplicates
    GenderAPIResults.drop_duplicates(inplace=True)

    # Rename columns to wanted sql columns
    GenderAPIResults.rename(
        columns={
            "first_name": "FirstName",
            "ga_first_name": "GaFirstName",
            "ga_gender": "GaGender",
            "ga_accuracy": "GaAccuracy",
            "ga_samples": "GaSamples",
        },
        inplace=True,
    )

    # Some names that are now known by GenderAPI were unknown in previous requests
    # These names occur several times in GenderAPIResults.FirstName and the entries with NaN values in every column but
    # FirstName needs to be deleted
    # Thus, we sort first such that entries with the highest power (GaSamples) are listed before their unknown
    # duplicates and then drop any but the first entry for each duplicated FirstName
    if not GenderAPIResults.empty:
        GenderAPIResults.sort_values(
            by=["FirstName", "GaSamples"], ascending=[True, False], inplace=True
        )
        GenderAPIResults.drop_duplicates(
            subset=["FirstName"], keep="first", inplace=True
        )

    conn.execute(
        """
        CREATE TABLE GenderAPIResults(
            FirstName TEXT NOT NULL PRIMARY KEY,
            GaFirstName TEXT,
            GaGender TEXT,
            GaAccuracy INT,
            GaSamples INT
        );
    """
    )
    GenderAPIResults.to_sql(
        "GenderAPIResults", con=conn, if_exists="append", index=False
    )
    log("GenderAPI results written to database")


def fill_authors(conn: Connection, to_csv=False):
    """
    Extract persons from dblp's www entries with title 'Home Page' (See https://dblp.org/faq/1474690.html.)
    Expect to find 'csv/www.csv', a csv file of www entries, generated by dblp_parser.py. Use first (full) name in
    column author as DBLPName and triggers propagation of table AuthorName with the remaining full names in list. Pick
    first affiliation only for a person in case multiple ones are listed and not specified further (See
    _prepare_affiliations() for details). Extracts Orcid and GoogleScholar pages from column url and puts the remaining
    ones to a separate column named Homepages. Determine the gender of each author (see _determine_genders() for
    details) and also save the first name that lead to this decision. Save everything to table 'Author' by using the
    given connection conn.
    :param conn:                sqlite3.Connection
    :param to_csv:              bool, whether to save the resulting table to csv/db/AuthorName.csv, too.
    """
    log("Progress of filling authors started")
    www = pd.read_csv("csv/www.csv")

    # Drop modification date, entries not referring to actual authors and title (turned useless)
    www.drop(["mdate"], axis="columns", inplace=True)
    www = www[www.title.isin(["Home Page", "Home Page ", "Home Page\nHome Page"])]
    www.drop(["title"], axis="columns", inplace=True)
    www = www[www.author.notnull()]

    # Extract name dblp uses on a person's page and corresponding alternative names
    www["DBLPName"], alternative_names = _separate_names(www.author)

    # Extract a person's first affiliation that is not specified further (See _prepare_affiliations() for details)
    www["affiliation"] = _prepare_affiliations(www[["key", "note"]])
    www.drop(columns=["note"], inplace=True)

    # Get AffiliationID from table Affiliation by mapping 'affiliation' with Affiliation.FullAffiliation
    Affiliation = pd.read_sql(
        "SELECT AffiliationID, FullAffiliation FROM Affiliation", con=conn
    )
    Author = www.merge(
        Affiliation, how="left", left_on="affiliation", right_on="FullAffiliation"
    ).astype({"AffiliationID": "Int64"})
    Author.drop(columns=["FullAffiliation", "affiliation"], inplace=True)
    log("AffiliationIDs to authors added")

    # Get a person's web pages by extracting Orcid and GoogleScholar pages from the urls and fill column Homepages with
    # remaining urls separated by newlines
    Author["OrcidPage"], Author["GoogleScholarPage"], Author["Homepages"] = zip(
        *Author.url.apply(lambda x: _prepare_urls(x))
    )
    Author.drop(columns=["url"], inplace=True)
    log("Web pages of authors extracted and added")

    # Determine genders
    log("Gender determination process started")
    Author["Gender"], Author["FirstName"] = _determine_genders(
        Author.DBLPName, alternative_names, conn
    )
    # Groups should not have a gender
    Author.loc[Author.publtype == "group", ["Gender", "FirstName"]] = "unknown", None
    log("Genders of authors determined")

    # Rename columns to wanted sql columns
    Author.rename(columns={"key": "AuthorID", "publtype": "Type"}, inplace=True)
    Author.drop(columns=["author"], inplace=True)

    # Save authors to database
    if to_csv:
        Author.to_csv("csv/db/Author.csv", index=False)

    conn.execute(
        """
        CREATE TABLE Author(
            AuthorID TEXT NOT NULL PRIMARY KEY,
            DBLPName TEXT NOT NULL UNIQUE,
            Type TEXT,
            OrcidPage TEXT,
            GoogleScholarPage TEXT,
            Homepages TEXT,
            AffiliationID INT,
            Gender TEXT,
            FirstName TEXT,
            FOREIGN KEY(AffiliationID) REFERENCES Affiliation(AffiliationID) ON DELETE CASCADE
        );
    """
    )
    Author.to_sql("Author", con=conn, if_exists="append", index=False)
    log("Authors written to database")

    # Trigger filling the table AuthorName
    fill_author_names(alternative_names, conn, to_csv=to_csv)


def fill_author_names(author_names, conn: Connection, to_csv=False):
    """
    Save the given author_names to table 'AuthorName' by using the given connection conn.
    :param author_names:    pd.DataFrame, being the return value 'alternative_names' of function _separate_names() with
                            columns 'DBLPName' and 'FullName'.
    :param conn:            sqlite3.Connection
    :param to_csv:          bool, whether to save the resulting table to csv/db/AuthorName.csv, too.
    """
    log("Progress of filling author names started")
    if to_csv:
        author_names.to_csv("csv/db/AuthorName.csv", index=False)

    conn.execute(
        """
        CREATE TABLE AuthorName(
            AuthorNameID INT NOT NULL PRIMARY KEY,
            DBLPName TEXT NOT NULL,
            FullName TEXT NOT NULL UNIQUE,
            FOREIGN KEY(DBLPName) REFERENCES Author(DBLPName) ON DELETE CASCADE
        );
    """
    )
    author_names.to_sql(
        "AuthorName", con=conn, if_exists="append", index_label="AuthorNameID"
    )
    log("Author names written to database")


def fill_venues(conn: Connection, to_csv=False):
    """
    Expect to find 'csv/articles.csv' and 'csv/inproceedings.csv', csv files of article entries and inproceedings
    entries from dblp.xml, generated by dblp_parser.py. Extract the venue's (short) names from inproceedings' attribute
    'booktitle' and from article's attribute 'journal'. Add the column Type either containing 'Journal' or
    'Conference | Workshop' (as dblp does not distinguish between conferences and workshops). Add the column
    ResearchArea to be filled later. Save everything to table 'Venue' by using the given connection conn.
    :param conn:    sqlite3.Connection
    :param to_csv:  bool, whether to save the resulting table to csv/db/Venue.csv, too.
    """
    log("Progress of filling venues started")
    inproceedings = pd.read_csv("csv/inproceedings.csv", usecols=["booktitle"])
    articles = pd.read_csv("csv/article.csv", usecols=["journal"])

    # Extract conference's and workshop's names
    conferences = pd.DataFrame()
    conferences["Name"] = inproceedings.booktitle.drop_duplicates().sort_values()
    conferences["Type"] = "Conference | Workshop"
    log("Conference's and workshop's names extracted")

    # Extract journal's names
    journals = pd.DataFrame()
    journals["Name"] = articles.journal.drop_duplicates().sort_values()
    journals["Type"] = "Journal"
    log("Journals's names extracted")

    Venue = pd.concat([conferences, journals])
    Venue.reset_index(drop=True, inplace=True)
    Venue = Venue[~Venue.Name.isnull()]

    if to_csv:
        Venue.to_csv("csv/db/Venue.csv", index=False)

    conn.execute(
        """
        CREATE TABLE Venue(
            VenueID INT NOT NULL PRIMARY KEY,
            Name TEXT NOT NULL,
            Type TEXT NOT NULL,
            ResearchArea TEXT
        );
    """
    )
    Venue.to_sql("Venue", con=conn, if_exists="append", index_label="VenueID")
    log("Venues written to database")


def fill_publications(conn: Connection, to_csv=False):
    """
    Extract publications from dblp's inproceedings, article, proceedings, book, incollection, phdthesis and masterthesis
    entries. Expect to find 'csv/article.csv', 'csv/book.csv', csv/incollection.csv', 'csv/inproceedings.csv',
    'csv/mastersthesis.csv', 'csv/phdthesis.csv' and csv/proceedings.csv', csv files generated by dblp_parser.py.
    Use the entries dblp keys as 'PublicationID'. Use the title, pages and year to fill the corresponding columns. Use
    the entries' 'publtype' for column 'PublicationType' (empty for regular publications). Add a column 'Type'
    containing the entries' name (e.g. 'Article' or 'Inproceedings'). Use proceedings' and inproceedings' booktitle and
    article's journal as their venue and add a reference to the venue in column VenueID. Save everything to table
    'Publication' by using the given connection conn. Trigger propagation of table PublicationAuthor containing the
    m-to-n-relationship entries for the relationships between Publication and Author.
    :param conn:    sqlite3.Connection
    :param to_csv:  bool, whether to save the resulting table to csv/db/AuthorName.csv, too.
    """
    log("Progress of filling publications started")
    # Read all the needed csv files and prepare for publication extraction
    inproceedings = pd.read_csv(
        "csv/inproceedings.csv",
        dtype={"year": int, "publtype": str, "pages": str},
        usecols=["key", "title", "booktitle", "pages", "year", "publtype", "author"],
    )
    articles = pd.read_csv(
        "csv/article.csv",
        usecols=["key", "title", "journal", "pages", "year", "publtype", "author"],
        dtype={"year": float, "publtype": str, "pages": str},
    )
    # Read column year as float due to NaN values and then convert it to int
    articles.year = articles.year.astype(pd.Int64Dtype())
    proceedings = pd.read_csv(
        "csv/proceedings.csv",
        usecols=["key", "title", "booktitle", "year", "publtype", "editor"],
        dtype={"year": int, "publtype": str},
    )
    books = pd.read_csv(
        "csv/book.csv",
        usecols=["key", "title", "year", "publtype", "author"],
        dtype={"year": int, "publtype": str},
    )
    incollections = pd.read_csv(
        "csv/incollection.csv",
        usecols=["key", "title", "pages", "year", "publtype", "author"],
        dtype={"year": int, "publtype": str, "pages": str},
    )
    phdtheses = pd.read_csv(
        "csv/phdthesis.csv",
        usecols=["key", "title", "pages", "year", "publtype", "author"],
        dtype={"year": object, "publtype": str, "pages": str},
    )
    # Read column year as object due to multiple years separated by newlines, pick the maximum and convert to int
    phdtheses.year = phdtheses.year.apply(lambda x: max(x.split("\n"))).astype(
        pd.Int64Dtype()
    )

    mastertheses = pd.read_csv(
        "csv/mastersthesis.csv",
        usecols=["key", "title", "year", "author"],
        dtype={"year": int},
    )

    # Use different queries and request by Type as there are some journals and conferences with the same name
    Venue_conf = pd.read_sql(
        "SELECT VenueID, Name FROM Venue where Type = 'Conference | Workshop'", con=conn
    )
    Venue_journal = pd.read_sql(
        "SELECT VenueID, Name FROM Venue where Type = 'Journal'", con=conn
    )

    # Prepare inproceedings
    inproceedings.rename(
        inplace=True,
        columns={
            "key": "PublicationID",
            "title": "Title",
            "booktitle": "Venue",
            "pages": "Pages",
            "year": "Year",
            "publtype": "PublicationType",
        },
    )
    inproceedings["Type"] = "Inproceedings"
    inproceedings["VenueID"] = inproceedings.merge(
        Venue_conf, how="left", left_on="Venue", right_on="Name"
    ).astype({"VenueID": "Int64"})["VenueID"]
    inproceedings.drop(columns=["Venue"], inplace=True)

    # Prepare articles
    articles.rename(
        inplace=True,
        columns={
            "key": "PublicationID",
            "title": "Title",
            "journal": "Venue",
            "pages": "Pages",
            "year": "Year",
            "publtype": "PublicationType",
        },
    )
    articles["Type"] = "Article"
    articles["VenueID"] = articles.merge(
        Venue_journal, how="left", left_on="Venue", right_on="Name"
    ).astype({"VenueID": "Int64"})["VenueID"]
    articles.drop(columns=["Venue"], inplace=True)

    # Prepare proceedings
    proceedings.rename(
        inplace=True,
        columns={
            "key": "PublicationID",
            "title": "Title",
            "booktitle": "Venue",
            "year": "Year",
            "publtype": "PublicationType",
            "editor": "author",
        },
    )
    proceedings["Type"] = "Proceedings"
    proceedings["VenueID"] = proceedings.merge(
        Venue_conf, how="left", left_on="Venue", right_on="Name"
    ).astype({"VenueID": "Int64"})["VenueID"]
    proceedings.drop(columns=["Venue"], inplace=True)

    # Prepare books
    books.rename(
        inplace=True,
        columns={
            "key": "PublicationID",
            "title": "Title",
            "year": "Year",
            "publtype": "PublicationType",
        },
    )
    books["Type"] = "Book"

    # Prepare incollections (chapters of books)
    incollections.rename(
        inplace=True,
        columns={
            "key": "PublicationID",
            "title": "Title",
            "year": "Year",
            "pages": "Pages",
            "publtype": "PublicationType",
        },
    )
    incollections["Type"] = "Incollection"

    # Prepare phdtheses
    phdtheses.rename(
        inplace=True,
        columns={
            "key": "PublicationID",
            "title": "Title",
            "year": "Year",
            "pages": "Pages",
            "publtype": "PublicationType",
        },
    )
    phdtheses["Type"] = "PhD Thesis"

    # Prepare mastertheses
    mastertheses.rename(
        inplace=True, columns={"key": "PublicationID", "title": "Title", "year": "Year"}
    )
    mastertheses["Type"] = "Master Thesis"

    Publication = pd.concat(
        [
            inproceedings,
            articles,
            proceedings,
            books,
            incollections,
            phdtheses,
            mastertheses,
        ]
    )
    publications_with_authors = Publication[["PublicationID", "author"]]
    Publication["AuthorCount"] = Publication.author.apply(
        lambda x: len(x.split("\n")) if pd.notnull(x) else 0
    )
    Publication.drop(columns=["author"], inplace=True)

    # Extract actual title if additional title information like bibtex are given via dict
    Publication.Title = Publication.Title.apply(lambda x: _extract(x, "text"))

    if to_csv:
        Publication.to_csv("csv/db/Publication.csv", index=False)

    Publication[Publication.Type.isnull()].to_csv("noPublicationType.csv", index=False)

    conn.execute(
        """
        CREATE TABLE Publication(
            PublicationID TEXT NOT NULL PRIMARY KEY,
            Title TEXT NOT NULL,
            VenueID INT,
            Type TEXT NOT NULL,
            PublicationType TEXT,
            Year INT,
            Pages TEXT,
            AuthorCount INT
        );
    """
    )

    Publication.to_sql("Publication", con=conn, if_exists="append", index=False)
    log("Publications written to database")

    fill_publication_author_relationships(
        publications_with_authors, conn=conn, to_csv=True
    )


def fill_publication_author_relationships(
    publications: pd.DataFrame, conn: Connection, to_csv=False
):
    """
    Find for each author in the list of authors of a publication in publications.author the corresponding DBLPName. Add
    the position the author is listed in the list of authors of publication. Save everything to table
    'PublicationAuthor' by using the given connection conn.
    :param publications:    pd.DataFrame, with columns 'PublicationID' and 'author'
    :param conn:            sqlite3.Connection
    :param to_csv:          bool, whether to save the resulting table to csv/db/PublicationAuthor.csv, too.
    """
    log("Progress of filling publication author relationships started")

    # Read tables Author and AuthorName
    Author = pd.read_sql("SELECT DBLPName FROM Author", con=conn)
    AuthorName = pd.read_sql("SELECT DBLPName, FullName FROM AuthorName", con=conn)

    publications = publications.copy()
    # Create a row per author in column author and add their position in the author list
    publications.author = publications.author.apply(
        lambda x: x.split("\n") if pd.notnull(x) else []
    )
    publications["Position"] = publications.author.apply(
        lambda x: list(range(1, len(x) + 1))
    )
    publications = publications.explode(["author", "Position"])
    log("Positions in author lists added")
    publications.author = publications.author.apply(
        lambda x: _extract(x, "text") if pd.notnull(x) else None
    )

    # Find DBLPName for each author by joining with Author on DBLPName and with AuthorName on FullName
    PublicationAuthor = publications.merge(
        Author, how="left", left_on="author", right_on="DBLPName"
    )
    PublicationAuthor = PublicationAuthor.merge(
        AuthorName, how="left", left_on="author", right_on="FullName"
    )
    PublicationAuthor["DBLPName"] = PublicationAuthor.DBLPName_x.fillna(
        PublicationAuthor.DBLPName_y
    )
    log("DBLPNames for publications found")

    PublicationAuthor.drop_duplicates(inplace=True)

    # There are papers mapped to a person twice, most likely due to erroneously mapped alternative names in dblp.
    # These violate our unique constraint on (PublicationID, DBLPName).
    # As long as dblp does not fix these errors, we need to one of the publication author relationships.
    PublicationAuthor[
        PublicationAuthor.duplicated(subset=["PublicationID", "DBLPName"], keep=False)
    ].to_csv("dblp/publications_with_erroneously_duplicated_authors.csv", index=False)
    PublicationAuthor.drop_duplicates(
        subset=["PublicationID", "DBLPName"], inplace=True, keep="first"
    )
    PublicationAuthor.drop(
        columns=["DBLPName_x", "DBLPName_y", "FullName", "author"], inplace=True
    )

    if to_csv:
        PublicationAuthor.to_csv("csv/db/PublicationAuthor.csv", index=False)

    conn.execute(
        """
        CREATE TABLE PublicationAuthor(
            PublicationID TEXT NOT NULL,
            DBLPName TEXT,
            Position TEXT,
            PRIMARY KEY (PublicationID, DBLPName),
            FOREIGN KEY(DBLPName) REFERENCES Author(DBLPName),
            FOREIGN KEY(PublicationID) REFERENCES Publication(PublicationID)
        );
    """
    )

    PublicationAuthor.to_sql(
        "PublicationAuthor", con=conn, if_exists="append", index=False
    )

    log("Publication author relationships written to database")


def get_unknown_first_names(conn: Connection):
    unknown = pd.read_sql(
        """
        SELECT DISTINCT FirstName AS first_name FROM Author 
        WHERE Gender = 'unknown' AND FirstName NOT NULL ORDER BY FirstName;
        """,
        con=conn,
    )

    # Discard 'nobiliary' particles in first names
    unknown = unknown[~unknown.first_name.isin(NO_MIDDLE_NAMES)]

    unknown.to_csv("csv/GenderAPI/unprocessed/first_names.csv", index=False)


def fill_all_together(conn: Connection):
    """
    Prepare the table 'AllTogether' by using the given connection conn.
    :param conn:    sqlite3.Connection
    :param to_csv:  bool, whether to save the resulting table to csv/db/AllTogether.csv, too.
    """
    log("Progress of filling all together started")
    conn.execute(
        """
        CREATE TABLE AllTogether(
            PublicationID TEXT, 
            PublicationType TEXT, 
            AuthorID TEXT, 
            Venue TEXT, 
            AffiliationID INT, 
            Position TEXT, 
            Gender TEXT, 
            Year INT, 
            AuthorCount INT, 
            Country TEXT, 
            Continent TEXT);
    """
    )

    conn.execute(
        """
        INSERT INTO AllTogether
        SELECT Publication.PublicationID, Publication.Type, Author.AuthorID, Venue.Name, Author.AffiliationID, PublicationAuthor.Position, Author.Gender, Publication.Year, Publication.AuthorCount, Country.DisplayName, Country.Continent
        FROM Publication

        INNER JOIN PublicationAuthor ON PublicationAuthor.PublicationID = Publication.PublicationID
        INNER JOIN Author ON PublicationAuthor.DBLPName = Author.DBLPName
        INNER JOIN Venue ON Publication.VenueID = Venue.VenueID
        INNER JOIN Affiliation ON Author.AffiliationID = Affiliation.AffiliationID
        INNER JOIN Country ON Affiliation.CountryCode = Country.CountryCode;
    """
    )
    log("All together written to database")


def create_indices(conn: Connection):
    log("Process of creating AllTogether index started")

    conn.execute(
        """CREATE INDEX all_together_index ON AllTogether(PublicationID, PublicationType, AuthorID, Venue, AffiliationID, Position, Gender, Year, AuthorCount, Country, Continent);"""
    )

    log("Index created")


def insert_research_areas(conn: Connection):
    research_areas = pd.read_csv("Research_area.csv")
    conn.execute(
        """
        ALTER TABLE AllTogether
            ADD ResearchArea VARCHAR;"""
    )

    for i in range(len(research_areas)):
        conference_name = (
            research_areas["Research Area"][i],
            research_areas["Venue"][i],
        )
        conference_aliases = [
            (
                research_areas["Research Area"][i],
                research_areas["Alias(es)(; separated)"][i].split(";")[x],
            )
            for x in range(len(research_areas["Alias(es)(; separated)"][i].split(";")))
        ]
        conference_aliases.insert(0, conference_name)

        for y in range(len(conference_aliases)):
            sql = f"""
            SELECT
                CASE WHEN EXISTS(
                    SELECT Venue
                    FROM AllTogether
                    WHERE Venue = ?
                )
                THEN 'True'
                ELSE 'False'
            END
            """

            result = conn.execute(sql, (conference_aliases[y][1].lstrip(),))
            if result.fetchall()[0][0] == "True":
                sql = f"""
                    UPDATE AllTogether
                    SET ResearchArea = ?
                    WHERE Venue = ?
                """
                conn.execute(
                    sql,
                    (
                        conference_aliases[y][0].lstrip(),
                        conference_aliases[y][1].lstrip(),
                    ),
                )
    conn.commit()


def fill_statistics(conn: Connection):
    log("Process of filling statistics started")
    conn.execute("""CREATE TABLE GeneralStatistics(Name TEXT, Value TEXT);""")
    returnVal = conn.execute(
        """SELECT count(distinct PublicationID) as count\nFROM Publication;"""
    )
    result = returnVal.fetchall()[0][0]
    conn.execute(
        f"""INSERT INTO GeneralStatistics(Name, Value) VALUES('PublicationCount', ?);""",
        (result,),
    )

    returnVal = conn.execute(
        """SELECT count(distinct AuthorID) as count\nFROM Author;"""
    )
    result = returnVal.fetchall()[0][0]
    conn.execute(
        """INSERT INTO GeneralStatistics VALUES('AuthorCount', ?);""", (result,)
    )

    returnVal = conn.execute(
        """SELECT count(distinct AffiliationID) as count\nFROM Affiliation;"""
    )
    result = returnVal.fetchall()[0][0]
    conn.execute(
        """INSERT INTO GeneralStatistics VALUES('AffiliationCount', ?);""", (result,)
    )

    returnVal = conn.execute("""SELECT count(distinct VenueID) as count\nFROM Venue;""")
    result = returnVal.fetchall()[0][0]
    conn.execute(
        """INSERT INTO GeneralStatistics VALUES('VenueCount', ?);""", (result,)
    )

    returnVal = conn.execute(
        """SELECT count(DBLPName) as count\nFROM PublicationAuthor;"""
    )
    result = returnVal.fetchall()[0][0]
    conn.execute(
        """INSERT INTO GeneralStatistics VALUES('PublicationAuthorCount', ?);""",
        (result,),
    )

    returnVal = conn.execute(
        """SELECT count(distinct AuthorID) as count\n FROM Author where Gender = \"woman\""""
    )
    result = returnVal.fetchall()[0][0]
    conn.execute(
        """INSERT INTO GeneralStatistics VALUES('FemaleAuthorCount', ?)""", (result,)
    )

    returnVal = conn.execute(
        """SELECT count(distinct AuthorID) as count\n FROM Author where Gender = \"man\""""
    )
    result = returnVal.fetchall()[0][0]
    conn.execute(
        """INSERT INTO GeneralStatistics VALUES('MaleAuthorCount', ?)""", (result,)
    )

    returnVal = conn.execute(
        """SELECT count(distinct AuthorID) as count\n FROM Author where Gender = \"unknown\""""
    )
    result = returnVal.fetchall()[0][0]
    conn.execute(
        """INSERT INTO GeneralStatistics VALUES('UnkownAuthorCount', ?)""", (result,)
    )

    returnVal = conn.execute(
        """SELECT count(distinct AuthorID) FROM Author INNER JOIN Affiliation ON Author.AffiliationID = Affiliation.AffiliationID WHERE Affiliation.CountryCode is not null;"""
    )
    result = returnVal.fetchall()[0][0]
    conn.execute(
        """INSERT INTO GeneralStatistics VALUES('AuthorCountWithCountry', ?)""",
        (result,),
    )

    returnVal = conn.execute(
        """SELECT count(distinct AuthorID) FROM Author INNER JOIN Affiliation ON Author.AffiliationID = Affiliation.AffiliationID WHERE Affiliation.CountryCode is null;"""
    )
    result = returnVal.fetchall()[0][0]
    conn.execute(
        """INSERT INTO GeneralStatistics VALUES('AuthorCountWithoutCountry', ?)""",
        (result,),
    )

    conn.execute(
        f"""INSERT INTO GeneralStatistics(Name, Value) VALUES('Date', ?)""",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),),
    )
    conn.commit()

    log("Process of filling statistics finished")


def fill_filters(conn: Connection):
    log("Process of filling filters started")
    if not os.path.exists('filters'):
        pathlib.Path("filters").mkdir(parents=True)

    returnPubType = pd.read_sql_query(
        """SELECT distinct PublicationType\nFROM AllTogether;""",
        conn,
    )

    returnPubType.to_csv("filters/PublicationTypes.csv", index=False)

    returnVenue = pd.read_sql_query(
        """SELECT distinct Venue\nFROM AllTogether;""",
        conn,
    )

    returnVenue.to_csv("filters/Venues.csv", index=False)

    returnContCount = pd.read_sql_query(
        """SELECT distinct Country, Continent\nFROM AllTogether""",
        conn,
    )

    returnContCount.to_csv("filters/Countries.csv", index=False)

    returnResAreas = pd.read_sql_query(
        """SELECT distinct ResearchArea\nFROM AllTogether""",
        conn,
    )

    returnResAreas.to_csv("filters/ResearchAreas.csv", index=False)


def _assign_country_code(affiliation):
    """
    Extract the country from the given affiliation by using the following rules of thumb:
    1. Most affiliations separate information by comma with the country at the last position
    2. Some affiliations do not separate information by comma but still contain the country as the last word (in case it
    is a single word country). Every other way of containing the country in the affiliation is not supported.
    The country code is then identified by _read_country_code(). If more than one country code is found, no country code
    is assigned to the affiliation and _read_country_code() writes a warning to STDOUT.
    :param affiliation: String, containing the full affiliation listed in dblp
    :return: list of given affiliation and country code, if found. Otherwise, country code is an empty string.
    """
    country_code = None

    codes_found = []

    # Most affiliations list the country after last comma
    splitted_affilation = affiliation.split(",")

    if len(splitted_affilation) > 1:
        potential_country = splitted_affilation[-1].strip()
        codes_found = _read_country_code(potential_country)
        if len(codes_found) == 1:
            country_code = codes_found[0]

    # Some affiliations do not separate the information by comma but still contain the country as the last word
    splitted_affilation = affiliation.split(" ")
    if len(codes_found) == 0:
        potential_country = splitted_affilation[-1].strip()
        codes_found = _read_country_code(potential_country)
        if len(codes_found) == 1:
            country_code = codes_found[0]
    return [affiliation, country_code]


def _read_country_code(country):
    """
    Search for the given country in country_name_variations.csv and return the result(s).
    :param country:     string
    :return:    string, one of ISO 3166-1 alpha-2 country codes or empty string if no match was found in
                country_name_variations.csv
    """
    codes = COUNTRY_VARIATIONS.loc[COUNTRY_VARIATIONS.Country == country, "Code"].values
    if len(codes) > 1:
        log(
            f"WARNING: more than one country code is found for extracted country {country}: {codes}"
        )
    return codes


def _separate_names(authors):
    """
    Split an author's names into their DBLPName (first (full) name in a row of given series authors) and corresponding
    alternative names.
    :param authors:     pd.Series, containing all names of one person per row separated by newlines.
    :return:            tuple of    1. pd.Series, containing the DBLPNames with the same indices as given in authors and
                                    2. pd.DataFrame, with columns 'DBLPName' and 'FullName', each FullName is an
                                    alternative name of an author identifiable via their DBLPName.
    """
    author_names = pd.DataFrame(columns=["DBLPName", "FullName"])
    author_names["DBLPName"], author_names["FullName"] = (
        authors.str.split("\n").str[0],
        authors.str.split("\n").str[1:],
    )

    # Extract actual name if additional author information are given via dict
    author_names.DBLPName = author_names.DBLPName.apply(lambda x: _extract(x, "text"))

    # Drop authors with one name only from alternative_names
    dblp_names = author_names.DBLPName.drop_duplicates()
    alternative_names = author_names[author_names.FullName.str.len() > 0]

    # Create a row per alternative FullName of a person
    alternative_names = alternative_names.explode("FullName")

    # Extract actual name if additional author information are given via dict
    alternative_names.FullName = alternative_names.FullName.apply(
        lambda x: _extract(x, "text")
    )
    alternative_names.reset_index(drop=True, inplace=True)

    return dblp_names, alternative_names


def _prepare_affiliations(www):
    """
    Expect column note of df www to contain dblp.xml's notes of www entries separated by newline in case of multiple
    notes per person. Pick the first affiliation only in case multiple ones are listed in and not specified further by
    a type like 'award', 'uname', 'isnot' or 'former' or by a label like 'former' or specific period of time
    :param www: pd.Dataframe
    :return: pd.Series, containing one affiliation (or none) for each person that was given in df www.
    """
    www = www.copy()
    www.note = www.note.apply(lambda x: x.split("\n") if pd.notnull(x) else "")
    www = www.explode("note")

    # Split notes into type, label and text for easier handling
    www["label"] = www.note.apply(lambda x: _extract(x, "label"))
    www["type"] = www.note.apply(lambda x: _extract(x, "type"))
    www["text"] = www.note.apply(lambda x: _extract(x, "text"))
    www.drop(columns=["note"], inplace=True)

    # Drop unnecessary note types like 'award', 'uname', 'isnot' and 'former'
    www = www[www.type.isin(["affiliation", None])]

    # Drop affiliations with labels (usually 'former' or a specific period of time)
    www = www[
        ((www.type == "affiliation") & (www.label.isnull())) | (www.type.isnull())
    ]

    # Pick first affiliation only in case multiple ones are listed and not specified further
    persons_with_multiple_affiliations = www[
        www.duplicated(subset=["key"], keep="first")
    ].shape[0]
    log(
        f"Number of persons with multiple affiliations not specified further: {persons_with_multiple_affiliations}"
    )
    # www[www.duplicated(subset=['key'], keep=False)].to_csv('csv/persons_with_multiple_affiliations.csv', index=False)
    www.drop_duplicates(subset=["key"], keep="first", inplace=True)
    return www["text"]


def _extract(element, attribute):
    """
    Get the value of attribute from element if it's a dict. If the attribute is not present, return None.
    If element is not a dict, it contains the text itself.
    :param element:     string or None, derives from a column value of a csv file produced by dplp_parser.py
    :param attribute:   string, the to be extracted dict value if element contains a dict
    :return:            string or None
    """
    if (
        element
        and element[0] == "{"
        and element[-1] == "}"
        and attribute in ast.literal_eval(element)
    ):
        return ast.literal_eval(element)[attribute]
    elif attribute == "text":
        return element
    else:
        return None


def _prepare_urls(urls):
    """
    Separates web pages of a person into ORCID pages, Google Scholar pages and remaining ones. If there are multiple
    pages of one kind, they are separated by a \n . Some urls from dblp come with a type like 'archive' which get
    appended to the respective url in brackets (See _append_type() for details).
    :param urls:    String, containing urls separated by \n (or dictionaries containing additional information about one
                    url) from dblp.
    :return:        triple of strings, first one contains all orcid pages, second one all google scholar pages and last
                    one all remaining web pages of a person.
    """
    orcid_page = []
    google_scholar_page = []
    homepages = []

    urls = urls.split("\n") if pd.notnull(urls) else None

    if urls:
        for url in urls:
            url = _append_type(url)
            if "orcid.org" in url:
                orcid_page.append(url)
            elif "scholar.google.com" in url:
                google_scholar_page.append(url)
            else:
                homepages.append(url)

    orcid_page = "\n".join(orcid_page) if len(orcid_page) > 0 else None
    google_scholar_page = (
        "\n".join(google_scholar_page) if len(google_scholar_page) > 0 else None
    )
    homepages = "\n".join(homepages) if len(homepages) > 0 else None

    return orcid_page, google_scholar_page, homepages


def _append_type(url):
    """
    Check if the given url is a dictionary containing additional information from dblp and extracts the url and the type
    (like 'deprecated' or 'archive').
    :param url: string, containing a dictionary with the url given in 'text'
    :return: string, the url given in url['text'] followed by url['type'] in brackets if given
    """
    if url and url[0] == "{" and url[-1] == "}":
        url = ast.literal_eval(url)
        return url["text"] + " (" + url["type"] + ")" if "type" in url else url["text"]
    else:
        return url


def _determine_genders(
    dblp_names: pd.Series, alternative_names: pd.DataFrame, conn: Connection
):
    """
    Assign a gender to all authors by first checking the first name in a DBLPName (middle name(s) of the DBLPName are
    only used if the first name is abbreviated, see _get_checkable_first_name()).
    Todo: Actually check middle name(s)' gender if first name is unknown or neutral.
    Todo: If no gender could be found for the DBLPName (or it was determined as 'unknown' by the GenderAPI meaning it is
    a neutral name), search for alternative names in table 'AuthorName' and checks the gender for them.
    :param dblp_names:          pd.Series,
    :param alternative_names:   pd.DataFrame, being the return value 'alternative_names' of function _separate_names()
                                with columns 'DBLPName' and 'FullName'.
    :param conn:                sqlite3.Connection
    :return:                    tuple of pd.Series', first one contains the gender for each given DBLPName and second
                                one the first name that was used to determine the gender. Both have the same indices as
                                given dblp_names. If there is no first name for a given DBLPName in the second series,
                                the name was not found in the table 'GenderAPIResults'.
    """
    authors = pd.DataFrame()
    authors["DBLPName"] = dblp_names

    # Read mappings from first names to genders by GenderAPI from database
    log("read_sql GenderAPIResults started")
    GenderAPIResults = pd.read_sql(
        "SELECT FirstName, GaGender FROM GenderAPIResults", con=conn
    )
    log("read_sql GenderAPIResults ended")

    log("get_checkable_first_names started")
    authors["FirstName"] = authors.DBLPName.apply(
        lambda x: _get_checkable_first_name(x)
    )
    log("get_checkable_first_names ended")

    # Give DBLPNames a gender based on column FirstName
    log("merge Author and GenderAPIResults started")
    authors = authors.merge(
        GenderAPIResults[["FirstName", "GaGender"]], how="left", on="FirstName"
    )
    log("merge Author and GenderAPIResults ended")

    # WIP:
    # Check the gender of alternative names if necessary
    # log('check for alternative names started')
    # authors.FirstName, authors.GaGender = _check_alternative_names(authors, alternative_names, conn, GenderAPIResults)
    # a = pd.DataFrame()
    # a['FirstName'], a['GaGender'] = _check_alternative_names(authors, alternative_names, conn, GenderAPIResults)
    # log('check for alternative names ended')
    # log(f"Shape of authors: {authors.shape}")
    # log(f"Shape of authors with alternative names: {a.shape}")

    authors.rename(columns={"GaGender": "Gender"}, inplace=True)
    authors.Gender = authors.Gender.apply(lambda x: _map_gender_terms(x))
    log("merge alternative names and GenderAPIResults ended")

    return authors.Gender, authors.FirstName


def _get_checkable_first_name(DBLPName):
    """
    Return the first name out of the first and middle names that is not abbreviated (or a nobiliary particle) and clean
    the names from quotes, brackets and trailing numbers being common in dblp's author names. If only one word is given
    in DBLPName the first name cannot be determined.
    :param DBLPName:    String, following the pattern 'first_name middle_name(s) last_name', middle name(s) are optional
    :return:            String, first usable first name out of first_name and middle_name(s)
    """
    # Remove trailing numbers that may appear in DBLPName and split it into list
    fullname = DBLPName.rstrip(" 0123456789").split(" ")
    # Can't determine if this is just the first or just the last name
    if len(fullname) == 1:
        return None

    # Split into first name, middle name(s) and last name
    first_name, middle_names, last_name = fullname[0], fullname[1:-1], fullname[-1]

    # Discard quotes and brackets
    first_name = first_name.strip('()"')
    middle_names = [middle_name.strip("()'\"") for middle_name in middle_names]
    last_name = last_name.strip("()'\"")

    # Discard 'nobiliary' particles in middle_names
    middle_names = [
        middle_name
        for middle_name in middle_names
        if middle_name not in NO_MIDDLE_NAMES
    ]

    # Discard abbreviations and check for middle names if necessary
    if re.match(r"\w+[.]", first_name):
        result = _get_checkable_first_name(" ".join(middle_names + [last_name]))
        return result

    return first_name


def _check_alternative_names(authors, alternative_names, GenderAPIResults):
    """
    WIP, see Todos.
    Check the gender for alternative names of an author if their DBLPName has the gender 'unknown' or 'neutral'.
    :param authors:             pd.DataFrame, being a join result of DBLPNames and GenderAPIResults with columns
                                'DBLPName', 'FirstName', 'GaGender'
    :param alternative_names:   pd.DataFrame, being the return value 'alternative_names' of function
                                _separate_names() with columns 'DBLPName' and 'FullName'.
    :param GenderAPIResults:    pd.DataFrame, with columns 'FirstName' and 'GaGender' from table 'GenderAPIResults'
    :return:                    tuple of pd.Series, 'FirstName' and 'GaGender'
    """
    print(authors.shape)
    print(alternative_names.shape)
    alternative_names = authors[["DBLPName", "FirstName", "GaGender"]].merge(
        alternative_names[["DBLPName", "FullName"]], how="left", on="DBLPName"
    )
    print(alternative_names.shape)
    print(alternative_names.columns)

    alternative_names.rename(columns={"FirstName": "FirstName_DBLPName"}, inplace=True)
    alternative_names["FirstName_AlternativeName"] = alternative_names.apply(
        lambda x: _get_checkable_first_name(x.FullName)
        if pd.notnull(x.FullName) and (x.GaGender == "unknown" or pd.isnull(x.GaGender))
        else None,
        axis=1,
    )

    alternative_names = alternative_names.merge(
        GenderAPIResults[["FirstName", "GaGender"]],
        how="left",
        left_on="FirstName_AlternativeName",
        right_on="FirstName",
    )

    def reduce_gender(row):
        # WIP: It only picks the more meaningful gender and first name per pair of DBLPName and alternative name
        # In case of multiple alternative names per DBLPName there is still the need for more reduction
        if row.GaGender_x != "unknown" and pd.notnull(row.GaGender_x):
            return [row.FirstName_DBLPName, row.GaGender_x]
        else:
            return [row.FirstName_AlternativeName, row.GaGender_y]

    alternative_names.drop(columns=["FirstName"], inplace=True)

    log("Reduce the gender started")
    alternative_names[["FirstName", "GaGender"]] = alternative_names.apply(
        reduce_gender, axis=1, result_type="expand"
    )
    log("Reduce the gender ended")
    alternative_names.to_csv("csv/alternative_names_with_gender.csv", index=False)
    # Todo: _get_gender() could be used as well to determine the gender for the names one by one (less efficient!)
    # _get_gender() needs 11 minutes for all dblp_names
    # authors['GaGender'] = authors.FirstName_y.apply(lambda x: get_gender(x, conn))
    # Todo: shrink return series (pick one of the alternative first names, e.g. first one, and pick its gender'

    return alternative_names.FirstName, alternative_names.GaGender


def _get_gender(firstname, conn):
    """
    Map the gender from table 'GenderAPIResults' to the given firstname.
    A gender determined by the GenderAPI is one out of 'female', 'male', 'unknown' (in case of a unisex name) or none.
    :param firstname:   String
    :param conn:        sqlite3.Connection
    :return:            String or None, one of ['female', 'male', 'unknown', None]
    """
    if firstname is None:
        return None

    # Change single apostrophe to SQL's style of apostrophes
    firstname = firstname.replace("'", "''")
    result = pd.read_sql(
        f"SELECT GaGender FROM GenderAPIResults where FirstName = '{firstname}'",
        con=conn,
    )

    return result["GaGender"].iloc[0] if not result.empty else None


def _map_gender_terms(gender):
    """
    Return the final wording for the given gender. 'female' and 'male' are mapped to 'woman' and 'man'. 'unknown' as
    given by the GenderAPI means the corresponding name is actually used by man and woman equally and therefore being
    'neutral'. If no gender was determined by the GenderAPI, it is labeled as 'unknown'.
    :param gender:  String
    :return:        String
    """
    mapping = {"female": "woman", "male": "man", "unknown": "neutral"}
    if gender in mapping:
        return mapping[gender]
    else:
        return "unknown"


if __name__ == "__main__":
    main()
