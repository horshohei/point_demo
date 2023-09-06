from fastapi import FastAPI, Body, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import json
import hashlib
import io

origins = ['*']

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def make_datalist(data_dict=None):
    if data_dict is None:
        data_dict = {}
    for filename in os.listdir('annotation_data/case'):
        if filename.endswith('.pdf'):
            caseID = filename.replace('_main.pdf', '')
            if filename not in data_dict:
                data_dict[caseID] = {}
                data_dict[caseID]['case'] = filename
                if os.path.exists('annotation_data/attachment/' + caseID + '_sub.pdf'):
                    data_dict[caseID]['sub'] = caseID + '_sub.pdf'
                else:
                    data_dict[caseID]['sub'] = ""
    return data_dict

def make_userlist(user_dict=None):
    with open('Users/users.json', 'r', encoding='utf-8') as f:
        user_dict = json.load(f)
    return user_dict

def attribute_list():
    with open('attributes.json', 'r', encoding='utf-8') as f:
        attributes = json.load(f)
    return attributes

def check_userstate(userdict, attributes, data_dict):
    userstate_dict = {}
    for user in userdict:
        if os.path.exists('Users/'+user+'/annotation_state.json'):
            with open('Users/'+user+'/annotation_state.json', 'r', encoding='utf-8') as f:
                userstate_dict[user] = json.load(f)
        else:
            os.makedirs('Users/'+user, exist_ok=True)
            userstate_dict[user] = {}
            for case in data_dict:
                userstate_dict[user][case] = {'state': False, 'data': []}
                post = {}
                for attri in attributes:
                    if attributes[attri] == '入力':
                        post[attri] = ''
                    elif type(attributes[attri]) is list:
                        post[attri] = []
                userstate_dict[user][case]['data'].append(post)
            with open('Users/'+user+'/annotation_state.json', 'w', encoding='utf-8') as f:
                json.dump(userstate_dict[user], f, ensure_ascii=False)
    return userstate_dict


data_dict = make_datalist()
user_dict = make_userlist()
attributes = attribute_list()
userstatedict = check_userstate(user_dict, attributes, data_dict)


def verify_access_token(token: str):
    if token != "YOUR_SECRET_TOKEN":
        raise HTTPException(status_code=403, detail="Unauthorized")


@app.get("/api/before")
async def root():
    return {"message": "Hello World"}


@app.get("/api/attributes")
async def say_hello():
    return attributes

@app.post("/api/annotationState")
async def annotation_state(body: dict = Body(None)):
    if 'username' in body:
        if body['username'] not in userstatedict:
            return {"message": "NG", "reason": "username"}
        else:
            if 'fetch' in body:
                data = body['fetch']
                if 'caseID' not in data:
                    return {"message": "NG", "reason": "caseID"}
                if 'index' not in data:
                    return {"message": "NG", "reason": "index"}
                if len(userstatedict[body['username']][data['caseID']]['data']) <= data['index']:
                    return {"message": "NG", "reason": "index"}
                print(userstatedict[body['username']][data['caseID']]['data'][data['index']])
                return {"message": "OK", 'annotationState': userstatedict[body['username']][data['caseID']]['data'][data['index']]}
            else:
                return {"message": "NG"}
    else:
        return {"message": "NG"}

@app.post("/api/save")
async def read_item(body: dict = Body(None)):
    print(body['texts'])
    data_dict = {"text": body['text'], "context": body['context']}
    data_dict.update(body['selections'])
    data_dict.update(body['texts'])
    with open('data.jsonl', 'a', encoding='utf8') as f:
        f.write(json.dumps(data_dict, ensure_ascii=False) + '\n', )
    return {"message": "OK"}

@app.post("/api/login")
async def read_item(body: dict = Body(None)):
    print(body['username'])
    #print(hashlib.sha256(user_dict[body['username']].encode()).hexdigest())
    if body['username'] not in user_dict:
        return {"message": "NG", "reason": "username"}
    if hashlib.sha256(user_dict[body['username']].encode()).hexdigest() == body['password']:
        #with open('user_state.json', 'r') as f:
        #    users_state = json.load(f)
        #    user_state = users_state[body['username']]
        return {"message": "OK", "username": body['username']}
    else:
        return {"message": "NG", "reason": "password"}


@app.get("/get-case/")
async def get_case(filename: str, token: str = Depends(verify_access_token)):
    file_directory = "annotation_data"  # PDFファイルが保存されているディレクトリ
    file_path = os.path.join(file_directory, f"{filename}.pdf")

    if os.path.exists(file_path):
        return FileResponse(file_path, headers={"Content-Disposition": "inline"})
    else:
        raise HTTPException(status_code=404, detail="PDF file not found")