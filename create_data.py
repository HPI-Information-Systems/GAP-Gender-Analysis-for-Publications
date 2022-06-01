import pandas as pd
import random

file = open('conferences.txt', mode = 'r')
lines = file.readlines()
file.close()


# read, parse and sort the conferences into topics and abbreviations
def parse_this(lines):
    conflist = []
    Field = ''
    subField = ''
    for line in lines:
            if(len(line)<2):
                    print('bla')
            elif(line[1]=='.'):
                    try:
                            int(line[0])== True
                            Field = (line.split(line[0:3])[1]).split('\n')[0]
                            subField = ''
                    except:
                            subField = (line.split(line[0:3])[1]).split('\n')[0]
            elif(line[2]=='.'):
                    try:
                            int(line[0])== True
                            Field = (line.split(line[0:4])[1]).split('\n')[0]
                            subField = ''
                    except:
                            print('xoxoxox')
            elif(line.find('-')!=-1):
                    Conference = line.split(' - ')[1].strip('\n')
                    Abbreviation = line.split(' - ')[0].strip()
                    conflist.append((Field, Conference, Abbreviation, subField))
    return(conflist)

clist = parse_this(lines)
df = pd.DataFrame(clist, columns =["Field", "Conference", "Abbreviation","Subfield"])
file_name = 'sorted_conferences.csv'
df.to_csv(file_name)


# read and combine from countries and continents
df2 = pd.read_csv('countries_continents.csv')


# create dummy data per Conference, per country, per year from 2000 to 2022 
nlist = []
count_Field = -1 
for i in df['Conference']:
    count_Field = count_Field + 1
    k = df['Field'][count_Field]
    for j in df2['Country']:
            for year in range(2000,2022):
                    nlist.append((year,i,k,j,random.randint(0,85)))

df3 = pd.DataFrame(nlist,columns =["Year","Conference","Field","Country","No of Publications"])
file_name = "new_data_2.csv"
df3.to_csv(file_name)


