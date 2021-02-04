#!/usr/bin/python3
import json
import requests
import os
import sys
import getopt
import time

def main():
    shard = ''
    token = ''
    cluster = ''
    localpath = ''
    workspacepath = ''
    outfilepath = ''
    params=''
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hs:t:c:lwo',
                                   ['shard=', 'token=', 'cluster=', 'localpath=', 'workspacepath=', 'outfilepath=','params='])
    except getopt.GetoptError:
        print(
            'executenotebook.py -s <shard> -t <token>  -c <cluster> -l <localpath> -w <workspacepath> -o <outfilepath>) -p <params>')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print(
                'executenotebook.py -s <shard> -t <token> -c <cluster> -l <localpath> -w <workspacepath> -o <outfilepath> -p <params>')
            sys.exit()
        elif opt in ('-s', '--shard'):
            shard = arg
        elif opt in ('-t', '--token'):
            token = arg
        elif opt in ('-c', '--cluster'):
            cluster = arg
        elif opt in ('-l', '--localpath'):
            localpath = arg
        elif opt in ('-w', '--workspacepath'):
            workspacepath = arg
        elif opt in ('-o', '--outfilepath'):
            outfilepath = arg
        elif opt in ('-p', '--params'):
            params = arg
    print('-s is ' + shard)
    #print('-t is ' + token)
    print('-c is ' + cluster)
    print('-l is ' + localpath)
    print('-w is ' + workspacepath)
    print('-o is ' + outfilepath)
    print('-p is ' + params)
    # Generate array from walking local path

    notebooks = []
    for path, subdirs, files in os.walk(localpath):
        for name in files:
            fullpath = path + '/' + name
            # removes localpath to repo but keeps workspace path
            fullworkspacepath = workspacepath + path.replace(localpath, '')

            name, file_extension = os.path.splitext(fullpath)
            if file_extension.lower() in ['.scala', '.sql', '.r', '.py']:
                row = [fullpath, fullworkspacepath, 1]
                notebooks.append(row)
    print('Number of Notebooks to process: '+str(len(notebooks)))
    # run each element in array
    for notebook in notebooks:
        nameonly = os.path.basename(notebook[0])
        workspacepath = notebook[1]

        name, file_extension = os.path.splitext(nameonly)

        # workpath removes extension
        fullworkspacepath = workspacepath + '/' + name

        print('Running job for:' + fullworkspacepath)
        
        #Create json from inout parameter list
        paramList = params.split(',')
        jsonString = '{'
        for param in paramList:
            if jsonString != '{':
                jsonString=jsonString+','
            paramElement = param.split('=')
            jsonString = jsonString +'"' + paramElement[0]+'":"'+paramElement[1]+'"'
        jsonString = jsonString + '}'
        pyJsonString = json.loads(jsonString)

        values = {'name': name, 'existing_cluster_id': cluster, 'timeout_seconds': 3600, 'notebook_task': {'notebook_path': fullworkspacepath}}
        #values = {'run_name': name, 'existing_cluster_id': cluster, 'timeout_seconds': 3600, 'notebook_task': {'notebook_path': fullworkspacepath}}
        #Create DB Job
        print('Job Create Request URL: '+ shard + '/api/2.0/jobs/create')
        print('Job Create Request Data:' + json.dumps(values))
        resp = requests.post(shard + '/api/2.0/jobs/create',
                             data=json.dumps(values), auth=("token", token))
        createjson = resp.text
        print("createson response:" + createjson)
        d = json.loads(createjson)
        jobid = d['job_id']
        #Run Job
        print('Run Request URL: '+ shard + '/api/2.0/jobs/run-now')
        values={'job_id': jobid,'notebook_params':pyJsonString}
        print('Run Request Data:' + json.dumps(values))
        resp = requests.post(shard + '/api/2.0/jobs/run-now',
                             data=json.dumps(values), auth=("token", token))
        runjson = resp.text
        print("runjson response:" + runjson)
        d = json.loads(runjson)
        runid = d['run_id']
        i=0
        waiting = True
        while waiting:
            time.sleep(10)
            jobresp = requests.get(shard + '/api/2.0/jobs/runs/get?run_id='+str(runid), auth=("token", token))
            jobjson = jobresp.text
            print("jobjson:" + jobjson)
            j = json.loads(jobjson)            
            current_state = j['state']['life_cycle_state']
            runid = j['run_id']
            if current_state in ['INTERNAL_ERROR', 'SKIPPED']:
                sys.exit("Notebook run did not compleye. Status is "+current_state)
                break
            else: 
                if current_state in ['TERMINATED']:
                    result_state = j['state']['result_state']
                    if result_state in ['FAILED']:
                        sys.exit("Notebook run did not compleye. Status is "+result_state)
                    else:
                        break
            i=i+1

        jobresp = requests.get(shard + '/api/2.0/jobs/runs/get-output?run_id='+str(runid),auth=("token", token))
        jobjson = jobresp.text
        print("Final response:" + jobjson)
        j = json.loads(jobjson)  
        notebook_output= j["notebook_output"]
        response=notebook_output["result"]
        print ("Return value is:"+response)
        print('##vso[task.setvariable variable=response;]%s' % (response))
        if outfilepath != '':
            file = open(outfilepath + '/' +  str(runid) + '.json', 'w')
            file.write(json.dumps(j))
            file.close()

if __name__ == '__main__':
    main()