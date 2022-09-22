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
    params = ''
    job_id = ''

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hs:t:c:lwo',
                                   ['shard=', 'token=','params=','job_id='])
    except getopt.GetoptError:
        print(
            'Wrong Paraemeters: executejob.py --shard <shard> --token <token> --params <params> --job_id <job_id>')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print(
                'executejob.py --shard <shard> --token <token> --params <params> --job_id <job_id>')
            sys.exit()
        elif opt in ('-s', '--shard'):
            shard = arg
        elif opt in ('-t', '--token'):
            token = arg
        elif opt in ('-p', '--params'):
            params = arg
        elif opt in ('-j', '--job_id'):
            job_id = arg
    print('--shard is ' + shard)
    #print('-t is ' + token)
    print('--params are ' + params)
    print('--job_id is ' + job_id)
    # Generate array from walking local path
        
    #Create json from inout parameter list
    if params == '':
        paramList = list()
    else:
        paramList = params.split(',')
    print("paramlist is "+str(paramList))
    jsonString = '{'
    for param in paramList:
        print("Param is "+param)
        if jsonString != '{':
            jsonString=jsonString+','
        paramElement = param.split('=')
        jsonString = jsonString +'"' + paramElement[0]+'":"'+paramElement[1]+'"'
    jsonString = jsonString + '}'
    pyJsonString = json.loads(jsonString)
    jobid = job_id
    #Run Job
    print('Run Request URL: '+ shard + '/api/2.1/jobs/run-now')
    values={'job_id': jobid,'notebook_params':pyJsonString}
    print('Run Request Data:' + json.dumps(values))
    resp = requests.post(shard + '/api/2.1/jobs/run-now',
                         data=json.dumps(values), auth=("token", token))
    runjson = resp.text
    print("runjson response:" + runjson)
    d = json.loads(runjson)
    runid = d['run_id']
    i=0
    waiting = True
    while waiting:
        time.sleep(10)
        jobresp = requests.get(shard + '/api/2.1/jobs/runs/get?run_id='+str(runid), auth=("token", token))
        jobjson = jobresp.text
        print("jobjson:" + jobjson)
        j = json.loads(jobjson)
        current_state = j['state']['life_cycle_state']
        runid = j['run_id']
        if current_state in ['INTERNAL_ERROR', 'SKIPPED']:
            sys.exit("Notebook run did not complete. Status is "+current_state)
            break
        else:
            if current_state in ['TERMINATED']:
                result_state = j['state']['result_state']
                if result_state in ['FAILED']:
                    sys.exit("Notebook run did not complete. Status is "+result_state)
                else:
                    break
        i=i+1
        print('Waiting for job to finish. Current state is: '+current_state)
    print('Job finished successfully. Result state is: ' + result_state)


if __name__ == '__main__':
    main()