# Databricks notebook source
# DBTITLE 1,Define Environment Variables For MLflow Registry Webhooks
import json
import os
dbutils.widgets.text(name = "model_name", defaultValue = "wine-model-ok", label = "Model Name")
dbutils.widgets.text(name = "api_endpoint", defaultValue = "https://mlflowwebhooks2.azurewebsites.net/api/httpexample", label = "API Endpoint")
dbutils.widgets.text(name = "events", defaultValue = "MODEL_VERSION_TRANSITIONED_STAGE", label = "Events")
databricks_host = json.loads(dbutils.notebook.entry_point.getDbutils().notebook().getContext().toJson())
databricks_host_url = "https://"+databricks_host["tags"]["browserHostName"]
databricks_token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()
os.environ['DATABRICKS_HOST'] = databricks_host_url
os.environ['DATABRICKS_TOKEN'] = databricks_token
os.environ['MODEL_NAME']= dbutils.widgets.get("model_name")
os.environ['API_ENDPOINT']= dbutils.widgets.get("api_endpoint")
os.environ['MLFLOW_EVENTS']= dbutils.widgets.get("events")

# COMMAND ----------

# DBTITLE 1,List Existing Webhooks (Run the next two commands). Manually Delete Existing Webhooks if necessary (see below)
# MAGIC %sh
# MAGIC curl -X GET -H "Authorization: Bearer "$DATABRICKS_TOKEN -d \
# MAGIC '{"model_name": "'$MODEL_NAME'"}' \
# MAGIC $DATABRICKS_HOST/api/2.0/mlflow/registry-webhooks/list > /dbfs/curl_resp.txt
# MAGIC export CURL=$(cat /dbfs/curl_resp.txt)

# COMMAND ----------

f = open("/dbfs/curl_resp.txt", "r")
result = json.load(f)
json_formatted_str = json.dumps(result, indent=2)
print(json_formatted_str)

# COMMAND ----------

# DBTITLE 1,Create Webhook using the API Endpoint provide above
# MAGIC %sh
# MAGIC curl -X POST -H "Authorization: Bearer $DATABRICKS_TOKEN" -d '{"model_name": "'$MODEL_NAME'","events": ["'$MLFLOW_EVENTS'"],"description": "Dev Ops","status": "ACTIVE","http_url_spec": {"url": "'$API_ENDPOINT'"}}' $DATABRICKS_HOST/api/2.0/mlflow/registry-webhooks/create

# COMMAND ----------

# DBTITLE 1,Delete Webhook
# MAGIC %sh
# MAGIC curl -X DELETE -H "Authorization: Bearer "$DATABRICKS_TOKEN -d \
# MAGIC '{"id": "4d446d23941c49b99417fcaeada0580e"}' \
# MAGIC $DATABRICKS_HOST/api/2.0/mlflow/registry-webhooks/delete