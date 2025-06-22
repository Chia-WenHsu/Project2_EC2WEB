## 此程式為 項目2 WEB 層程式

1. git clone 
2. pip install requirements
3. uvicorn main:app --host 0.0.0.0 --port 8000


INPUT_BUCKET = "nicoproject2input"
REQUEST_QUEUE_URL = "https://sqs.ap-northeast-2.amazonaws.com/530751794867/project2-request-q"
RESPONSE_QUEUE_URL = 'https://sqs.ap-northeast-2.amazonaws.com/530751794867/project2-response-q'
REGION = "ap-northeast-2"
AMI_ID = "ami-011dae5f0fc7d1a64"
INSTANCE_TYPE = "t2.micro"
KEY_NAME = "nico_projectKey"
SECURITY_GROUP_IDS = ["sg-06130228d6c599dd4"]