# GAP: Gender Analysis for Publications

### The Web App


Install python virtualenv:
```
pip3.9 install virtualenv 
```
Create a virtual environment:
```
python3.9 -m virtualenv gap_env
```
Activate the virtual environment:
```
source gap_env/bin/activate
```
Install all the relevant dependencies:

```
pip3.9 install -r requirements.txt
```
Create dummy data with `python3.9 create_data.py`
Run app with `streamlit run prototype.py`.
