import itertools
import requests
import pandas as pd
import tqdm

searchperson_url = 'http://collaboration.mit.edu/Home/SearchPersons'
productivity_url = 'http://collaboration.mit.edu/Home/Productivity/'

deptid_path = 'D:\CS\cs506\project/deptId.txt'

deptid = {} # id: deptname
with open(deptid_path) as f:
    lines = f.readlines()

    for line in lines:
        line_elem = line.strip().split(':')
        deptid[int(line_elem[1])] = line_elem[0]

form = {
    'searchTerms': '',               # search field
    'searchTermTypeId': 2,           # 1: Name, 2: Topic
    'unitIdStrings': 1175,           # department/center id
    'unitTypeId': 2,              # 2: department, 21: center
    'workTypeIds': '',
    'workYearStart': 0,
    'workYearEnd': 0
}

alphabets = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

def parse_response(response, data, department):

    for i in range(len(response['searchResults'])):
        
        for header in response['searchResults'][i].keys():
            if data.get(header) == None:
                data[header] = [response['searchResults'][i][header]]
            else:
                data[header].append(response['searchResults'][i][header])

        collab_ids = []
        for j in range(len(response['Collaborations'][i]['Collaborations'])):
            author_id = response['Collaborations'][i]['Collaborations'][j]['AuthorId']
            coauthor_id = response['Collaborations'][i]['Collaborations'][j]['CoAuthorId']
            person_id = response['searchResults'][i]['Id']
            if (author_id != person_id):
                raise ValueError('AuthorId does not match person Id')
            else:
                collab_ids.append(coauthor_id)

        collab_str = ''
        for collab_id in collab_ids:
            collab_str += collab_id + '|'

        if data.get('Collaborations') == None:
            data['Collaborations'] = [collab_str]
        else:
            data['Collaborations'].append(collab_str)

        if data.get('Department_MITCollab') == None:
            data['Department_MITCollab'] = [department]
        else:
            data['Department_MITCollab'].append(department)
    
    return data

for year in range(2004, 2022):

    print(year)

    data = {}
    for unitIdStrings in deptid.keys():

        # setting parameters for posted data
        form['searchTerms'] = ''
        form['unitTypeId'] = 2
        form['searchTermTypeId'] = 2
        form['unitIdStrings'] = unitIdStrings
        form['workYearStart'] = year
        form['workYearEnd'] = year
        response = requests.post(searchperson_url, data=form).json()

        if len(response['searchResults']) == 100:
            # if results overflow, use advanced scraping
            combinations = [
                combination[0] + combination[1] for combination in itertools.product(alphabets, repeat=2)
            ]
            combinations += alphabets

            for i in tqdm.tqdm(range(len(combinations))):

                # search by name
                form['searchTermTypeId'] = 1
                form['searchTerms'] = combinations[i]

                response = requests.post(searchperson_url, data=form).json()
                data = parse_response(response, data, deptid[unitIdStrings])
        else:
            data = parse_response(response, data, deptid[unitIdStrings])

    df = pd.DataFrame(data=data)
    # dropping ALL duplicate values
    df.drop_duplicates(subset='Id', inplace = True)
    df.to_csv('D:\CS\cs506\project/year/{}.csv'.format(year), index=False)