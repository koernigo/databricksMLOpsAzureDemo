# Databricks notebook source
# MAGIC %md ###Test the Model

# COMMAND ----------

dbutils.widgets.text(name = "model_name", defaultValue = "wine-model-ok", label = "Model Name")
dbutils.widgets.text(name = "scoring_uri", defaultValue="",label = "Scoring URI")

# COMMAND ----------

# MAGIC %md ####Download the data

# COMMAND ----------

#%sh wget https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-red.csv

# COMMAND ----------

#wine_data_path = "/databricks/driver/winequality-red.csv"
wine_data_path = "/dbfs/FileStore/tables/winequality_red-42ff5.csv"

# COMMAND ----------

import numpy as np
import pandas as pd
from sklearn import datasets
from sklearn.model_selection import train_test_split

data = pd.read_csv(wine_data_path, sep=None)
train, _ = train_test_split(data)
train_x = train.drop(["quality"], axis=1)
sample = train_x.iloc[[0]]
query_input = list(sample.values.flatten())
sample_json = sample.to_json(orient="split")

# COMMAND ----------

import requests
import json

def query_endpoint_example(scoring_uri, inputs, service_key=None):
  headers = {
    "Content-Type": "application/json",
  }
  if service_key is not None:
    headers["Authorization"] = "Bearer {service_key}".format(service_key=service_key)
    
  print("Sending batch prediction request with inputs: {}".format(inputs))
  response = requests.post(scoring_uri, data=inputs, headers=headers)
  print("Response: {}".format(response.text))
  preds = json.loads(response.text)
  print("Received response: {}".format(preds))
  return preds

# COMMAND ----------

scoring_uri = dbutils.widgets.get("scoring_uri")

# COMMAND ----------

prediction = query_endpoint_example(scoring_uri=scoring_uri, inputs=sample_json)

# COMMAND ----------

dbutils.notebook.exit(prediction)