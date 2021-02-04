#This script promotes the latest model with the given name out of staging into production
import importlib,pprint,json,os
from  mlflow_http_client import MlflowHttpClient, get_host,get_token

client = MlflowHttpClient(host=get_host(),token=get_token())
pp = pprint.PrettyPrinter(indent=4)
model_name=os.environ.get('MODEL_NAME')
print("Mode Name is: "+model_name)
rsp = client.get("registered-models/get-latest-versions?name="+model_name+"&stages=staging")
if len(rsp) >= 1:
    version = rsp['model_versions'][0]['version']
else:
    raise BaseException('There is no staging model for the model named: '+model_name)
result=rsp['model_versions'][0]['version']

data = {"name": model_name,"version":version,"stage":"production","archive_existing_versions":True}
rsp = client.post("model-versions/transition-stage", data)
pp.pprint(rsp)
response=rsp['model_version']['version']
print ("Return value is:"+response)
print('##vso[task.setvariable variable=response;]%s' % (response))