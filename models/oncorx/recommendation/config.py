# Azure settings
AZURE_SUBSCRIPTION_ID = ""
AZURE_RESOURCE_GROUP_NAME = "" # "TestGroup"

# Azure Machine Learning settings
AZURE_ML_WORKSPACE_NAME = "aml-nefire-dev" # "finetunephi-workspace"

# Azure Managed Identity settings
AZURE_MANAGED_IDENTITY_CLIENT_ID = ""
AZURE_MANAGED_IDENTITY_NAME = "" # "finetunephi-mangedidentity"
AZURE_MANAGED_IDENTITY_RESOURCE_ID = f"/subscriptions/{AZURE_SUBSCRIPTION_ID}/resourceGroups/{AZURE_RESOURCE_GROUP_NAME}/providers/Microsoft.ManagedIdentity/userAssignedIdentities/{AZURE_MANAGED_IDENTITY_NAME}"

# Dataset file paths
TRAIN_DATA_PATH = "data/train_data.jsonl"
TEST_DATA_PATH = "data/test_data.jsonl"

# Fine-tuned model settings
AZURE_MODEL_NAME = "" # "finetune-phi-model"
AZURE_ENDPOINT_NAME = "" # "finetune-phi-endpoint"
AZURE_DEPLOYMENT_NAME = "" # "finetune-phi-deployment"

AZURE_ML_API_KEY = "your_fine_tuned_model_api_key"
AZURE_ML_ENDPOINT = "" # "https://{your-endpoint-name}.{your-region}.inference.ml.azure.com/score"