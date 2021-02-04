# Databricks notebook source
# MAGIC %md In order to use a Webhook you need an API endpoint that triggers the Azure Devops pipeline. This is a simple example

# COMMAND ----------

import json
import os
dbutils.widgets.text(name = "region", defaultValue = "eastus2", label = "Region")
dbutils.widgets.text(name = "app_name", defaultValue = "mlflowwebook", label = "App Name")
dbutils.widgets.text(name = "storage_name", defaultValue = "mlflowwebhook", label = "Storage Account Name")
databricks_host = json.loads(dbutils.notebook.entry_point.getDbutils().notebook().getContext().toJson())
databricks_host_url = "https://"+databricks_host["tags"]["browserHostName"]
databricks_token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()
os.environ['FUNC_REGION'] = dbutils.widgets.get("region")
os.environ['FUNC_APP_NAME'] = dbutils.widgets.get("app_name")
os.environ['FUNC_STORAGE_NAME']= dbutils.widgets.get("storage_name")
os.environ["AZURE_TOKEN_BASE64"]=dbutils.secrets.get(scope = "demo", key = 'azt')

# COMMAND ----------

# DBTITLE 1,Installing the Azure CLI on the Driver
# MAGIC %sh
# MAGIC curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# COMMAND ----------

# DBTITLE 1,Azure Login (This will output a browser link and code to login. Once logged in, the Notebook will continue)
# MAGIC %sh
# MAGIC az login

# COMMAND ----------

# DBTITLE 1,Create Resource Group for Function App
# MAGIC %sh
# MAGIC az group create --name $FUNC_APP_NAME-rg --location $FUNC_REGION

# COMMAND ----------

# DBTITLE 1,Create Storage for Function App
# MAGIC %sh
# MAGIC az storage account create --name $FUNC_STORAGE_NAME --location $FUNC_REGION --resource-group $FUNC_APP_NAME-rg --sku Standard_LRS

# COMMAND ----------

# DBTITLE 1,Create Function App using Storage and Resource Group
# MAGIC %sh
# MAGIC az functionapp create --resource-group $FUNC_APP_NAME-rg --consumption-plan-location $FUNC_REGION --runtime python --runtime-version 3.8 --functions-version 3 --name $FUNC_APP_NAME --storage-account $FUNC_STORAGE_NAME --os-type linux

# COMMAND ----------

# DBTITLE 1,Install Function App CLI
# MAGIC %sh
# MAGIC curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
# MAGIC sudo mv microsoft.gpg /etc/apt/trusted.gpg.d/microsoft.gpg
# MAGIC sudo sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/repos/microsoft-ubuntu-$(lsb_release -cs)-prod $(lsb_release -cs) main" > /etc/apt/sources.list.d/dotnetdev.list'
# MAGIC sudo apt-get update
# MAGIC sudo apt-get install azure-functions-core-tools-3

# COMMAND ----------

# DBTITLE 1,Init Function App
# MAGIC %sh
# MAGIC func init $FUNC_APP_NAME --python

# COMMAND ----------

# DBTITLE 1,Create Function (using same name as app)
# MAGIC %sh
# MAGIC cd $FUNC_APP_NAME
# MAGIC func new --name $FUNC_APP_NAME --template "HTTP trigger" --authlevel "anonymous"
# MAGIC ls

# COMMAND ----------

# DBTITLE 1,Store Azure Dev Ops Token in file from secret
# MAGIC %sh
# MAGIC echo 'token = "'$AZURE_TOKEN_BASE64'"' > $FUNC_APP_NAME/azt.txt
# MAGIC cat $FUNC_APP_NAME/azt.txt

# COMMAND ----------

# DBTITLE 1,Create Python Code for Function (merging token info with code)
# MAGIC %sh
# MAGIC cd $FUNC_APP_NAME
# MAGIC cat > $FUNC_APP_NAME/part1.txt <<EOF
# MAGIC import logging
# MAGIC import http.client
# MAGIC import azure.functions as func
# MAGIC import json
# MAGIC 
# MAGIC def main(req: func.HttpRequest) -> func.HttpResponse:
# MAGIC     test=False #Set to True if testing the function w/o submitting an Http Request
# MAGIC     logging.info("Request Body:"+req.get_body().decode("utf-8"))
# MAGIC     event_json=json.loads(req.get_body().decode("utf-8"))
# MAGIC     logging.info("Request Headers:"+str(event_json))
# MAGIC     logging.info("To Stage "+event_json['to_stage'])
# MAGIC     logging.info('Python HTTP trigger function processed a request.')
# MAGIC     conn = http.client.HTTPSConnection("dev.azure.com")
# MAGIC     payload = "{\n    \"resources\": {\n        \"repositories\": {\n            \"self\": {\n                \"refName\": \"refs/heads/master\"\n            }\n        }\n    },\n    \"variables\":{\n        \"model_name\":{\n            \"value\": \""+event_json['model_name']+"\"\n        }\n    }\n}"
# MAGIC     headers = {
# MAGIC       'Authorization': 'Basic '" + token + "',
# MAGIC       'Content-Type': 'application/json',
# MAGIC       'Cookie': 'VstsSession=%7B%22PersistentSessionId%22%3A%2237e6fc58-1829-4596-85fd-b490f5c70dc5%22%2C%22PendingAuthenticationSessionId%22%3A%2200000000-0000-0000-0000-000000000000%22%2C%22CurrentAuthenticationSessionId%22%3A%2200000000-0000-0000-0000-000000000000%22%2C%22SignInState%22%3A%7B%7D%7D'
# MAGIC }
# MAGIC     if not test and event_json['to_stage'] == 'Staging':
# MAGIC        conn.request("POST", "/ML-Governance/ML%20Governance%20V2/_apis/pipelines/6/runs?api-version=6.0-preview", payload, headers)
# MAGIC        res = conn.getresponse()
# MAGIC        data = res.read()
# MAGIC        print(data.decode("utf-8"))
# MAGIC        return func.HttpResponse(data.decode("utf-8"))
# MAGIC     else:
# MAGIC        return "No HTTP call submitted"
# MAGIC EOF

# COMMAND ----------

# DBTITLE 1,Copy Pythin code to __init__.py file
# MAGIC %sh
# MAGIC cd $FUNC_APP_NAME
# MAGIC cat azt.txt $FUNC_APP_NAME/part1.txt > $FUNC_APP_NAME/__init__.py
# MAGIC cat $FUNC_APP_NAME/__init__.py

# COMMAND ----------

# DBTITLE 1,Uncomment this cell to test the API locally (comment cell 16)
'''%sh
cd $FUNC_APP_NAME
func start  --port 7072'''

# COMMAND ----------

# DBTITLE 1,Deploy Webhook Function to Azure
# MAGIC %sh
# MAGIC cd $FUNC_APP_NAME
# MAGIC func azure functionapp publish $FUNC_APP_NAME

# COMMAND ----------

# MAGIC %md Please look at the bottom of output of the last cell. It will provide the URL to be used in the Webhook create API

# COMMAND ----------

# DBTITLE 1,Uncomment to perform Cleanup of the Azure Function resources
'''%sh
az group delete --yes --name $FUNC_APP_NAME-rg'''