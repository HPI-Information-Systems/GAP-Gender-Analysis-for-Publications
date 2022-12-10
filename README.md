# GAP: Gender Analysis for Publications

## Before Using this Project

We are very pleased that you would like to use our tool.
If you want to skip the possibly hour-long [initial setup](#setting-up-the-data-source), we recommend recommend you to visit the already set up version at **[csgender.org](https://csgender.org/)**.
You can instantly start analyzing the data and we also try our best to update the data used there every 3 months.

## Setting up the Data Source

### Prepare the Environment

1. Install python virtualenv: `pip3.9 install virtualenv`
2. Create a virtual environment: `python3.9 -m virtualenv gap_env`
3. Activate the virtual environment: `source gap_env/bin/activate`
4. Install the dependencies: `pip3.9 install -r requirements.txt`

### Parse the dblp xml

csv files of all [level-1 elements of dblp.xml](https://dblp.org/faq/16154937.html) can be parsed with this component.
To do so, perform the following steps:

0.
   1. [Prepare the Environment](#prepare-the-environment) if not already done.
   2. Activate the virtual environment: `source gap_env/bin/activate` if not already done in (i).
1. Create a directory for the dblp dump: `mkdir dblp`
2. Download the dblp.xml and the relevant dblp-20xx-xx-xx.dtd file from the [dblp xml dump](https://dblp.org/xml/).
3. Store the downloaded files in the 'dblp' directory.
4. Run the parser to generate the csv files to be stored in `csv/`: `python3.9 dblp_parser.py`

### Propagate data to the database

0.
   1. [Prepare the Environment](#prepare-the-environment) if not already done.
   2. Activate the virtual environment: `source gap_env/bin/activate` if not already done in (i).
   3. [Parse the dblp xml](#parse-the-dblp-xml) if not already done.
1. If you already have gender-annotated first names from the GenderAPI, put them under `csv/GenderAPI/`
2. Run the database script to fill the database and also save the tables as readable csv files under `csv/db/`:
`python3.9 database.py`

A csv file with all unknown first name can be found under `csv/GenderAPI/unprocessed/`. It contains first names that
where unknown to the GenderAPI in the past (this may change over time!) as well as names that we did not requested from
the GenderAPI yet. Pass it to the GenderAPI and start with the first step again to increase the gender
determination rate.

## The Web App

0.
   1. [Prepare the Environment](#prepare-the-environment) if not already done.
   2. Activate the virtual environment: `source gap_env/bin/activate` if not already done in (i).
   3. [Parse the dblp xml](#parse-the-dblp-xml) if not already done.
   4. [Propagate data to the database](#propagate-data-to-the-database) if not already done.
1. [Install Streamlit](https://docs.streamlit.io/library/get-started/installation)
2. Run the website with `streamlit run prototype.py`. A new browser tab will open with the app.
