# Databricks notebook source
# MAGIC %sh
# MAGIC curl -X POST -d \
# MAGIC '{
# MAGIC   "event": "MODEL_VERSION_TRANSITIONED_STAGE",
# MAGIC   "webhook_id": "c5596721253c4b429368cf6f4341b88a",
# MAGIC   "event_timestamp": 1589859029343,
# MAGIC   "model_name": "wine-model-ok",
# MAGIC   "version": "8",
# MAGIC   "to_stage": "Staging",
# MAGIC   "from_stage": "None",
# MAGIC   "text": "Registered model 'someModel' version 8 transitioned from None to Production."
# MAGIC }' \
# MAGIC https://mlflowwebook.azurewebsites.net/api/mlflowwebook