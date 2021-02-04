# Databricks notebook source
# MAGIC %pip install azureml-sdk

# COMMAND ----------

# MAGIC %md ### Deploy latest mlFlow registry Model to Azure ML

# COMMAND ----------

# MAGIC %md ###Get Name of Model

# COMMAND ----------

dbutils.widgets.text(name = "model_name", defaultValue = "wine-model-ok", label = "Model Name")
dbutils.widgets.text(name = "stage", defaultValue = "staging", label = "Stage")
dbutils.widgets.text(name = "phase", defaultValue = "qa", label = "Phase")

# COMMAND ----------

model_name = dbutils.widgets.get("model_name")
stage = dbutils.widgets.get("stage")
phase=dbutils.widgets.get("phase")

# COMMAND ----------

# Config for AzureML Workspace
# for secure keeping, store credentials in Azure Key Vault and link using Azure Databricks secrets with dbutils
#subscription_id = dbutils.secrets.get(scope = "common-sp", key ="az-sub-id")
subscription_id = "3f2e4d32-8e8d-46d6-82bc-5bb8d962328b"
resource_group = "ok-azureml-test"                   
workspace_name = "ok-azureml-test"                       
tenant_id = "9f37a392-f0ae-4280-9796-f1864a10effc" # Tenant ID
sp_id = dbutils.secrets.get(scope = "common-sp", key ="common-sa-sp-client-id") # Service Principal ID
sp_secret = dbutils.secrets.get(scope = "common-sp", key ="common-sa-sp-client-secret") # Service Principal Secret

# COMMAND ----------

import mlflow
import mlflow.azureml
#import azureml.mlflow
import azureml.core
from azureml.core import Workspace
#from azureml.mlflow import get_portal_url

print("AzureML SDK version:", azureml.core.VERSION)
print("MLflow version:", mlflow.version.VERSION)

# COMMAND ----------

from azureml.core.authentication import ServicePrincipalAuthentication
def service_principal_auth():
  return ServicePrincipalAuthentication(
      tenant_id=tenant_id,
      service_principal_id=sp_id,
      service_principal_password=sp_secret)

# COMMAND ----------

def azureml_workspace(auth_type='interactive'):
  if auth_type == 'interactive':
    auth = interactive_auth()
  elif auth_type == 'service_princpal':
    auth = service_principal_auth()
    
  ws = Workspace.create(name = workspace_name,
                       resource_group = resource_group,
                       subscription_id = subscription_id,
                       exist_ok=True,
                       auth=auth)
  return ws

# COMMAND ----------

# MAGIC %md ### Get the latest version of the model that was put into Staging

# COMMAND ----------

import mlflow
import mlflow.sklearn

client = mlflow.tracking.MlflowClient()
latest_model = client.get_latest_versions(name = model_name, stages=[stage])
#print(latest_model[0])

# COMMAND ----------

model_uri="runs:/{}/model".format(latest_model[0].run_id)
latest_sk_model = mlflow.sklearn.load_model(model_uri)

# COMMAND ----------

# MAGIC %md ### Create or load an Azure ML Workspace

# COMMAND ----------

# MAGIC %md Before models can be deployed to Azure ML, an Azure ML Workspace must be created or obtained. The `azureml.core.Workspace.create()` function will load a workspace of a specified name or create one if it does not already exist. For more information about creating an Azure ML Workspace, see the [Azure ML Workspace management documentation](https://docs.microsoft.com/en-us/azure/machine-learning/service/how-to-manage-workspace).

# COMMAND ----------

import azureml
from azureml.core import Workspace

workspace = azureml_workspace(auth_type = 'service_princpal') # If you don't have a service principal, use 'interactive' for interactive login

# COMMAND ----------

# MAGIC %md ## Building an Azure Container Image for model deployment

# COMMAND ----------

# MAGIC %md ### Use MLflow to build a Container Image for the trained model
# MAGIC 
# MAGIC We will use the `mlflow.azuereml.build_image` function to build an Azure Container Image for the trained MLflow model. This function also registers the MLflow model with a specified Azure ML workspace. The resulting image can be deployed to Azure Container Instances (ACI) or Azure Kubernetes Service (AKS) for real-time serving.

# COMMAND ----------

print(phase)

# COMMAND ----------

import mlflow.azureml

model_image, azure_model = mlflow.azureml.build_image(model_uri=model_uri, 
                                                      workspace=workspace, 
                                                      model_name=model_name+"-"+stage,
                                                      image_name=model_name+"-"+phase+"-image",
                                                      description=model_name, 
                                                      tags={
                                                        "alpha": str(latest_sk_model.alpha),
                                                        "l1_ratio": str(latest_sk_model.l1_ratio),
                                                      },
                                                      synchronous=True)

# COMMAND ----------

# MAGIC %md ### Deploy Web Service in Azure ML

# COMMAND ----------

import azureml
from azureml.core.webservice import AciWebservice, Webservice
dev_webservice_name = model_name+"-"+phase # make sure this name is unique and doesnt already exist, else need to replace
dev_webservice_deployment_config = AciWebservice.deploy_configuration()
dev_webservice = Webservice.deploy_from_image(name=dev_webservice_name, image=model_image, deployment_config=dev_webservice_deployment_config, workspace=workspace,overwrite=True)

# COMMAND ----------

dev_webservice.wait_for_deployment()

# COMMAND ----------

dev_scoring_uri = dev_webservice.scoring_uri

# COMMAND ----------

print(dev_scoring_uri)

# COMMAND ----------

dbutils.notebook.exit(dev_scoring_uri)