## 部屬至EC2
1. cd /home/ubuntu/Project2_EC2App
2. source venv/bin/activate


## 此程式為 項目2 WEB 層程式

1. git clone 
2. pip install requirements
3. uvicorn main:app --host 0.0.0.0 --port 8000 可單獨打開程式


S3_BUCKET_NAME_input = 'nicoproject2input'
S3_BUCKET_NAME_output = 'nicoproject2output'
REQUEST_QUEUE_URL = "https://sqs.ap-northeast-2.amazonaws.com/530751794867/project2-request-q"
RESPONSE_QUEUE_URL = 'https://sqs.ap-northeast-2.amazonaws.com/530751794867/project2-response-q'
REGION = "ap-northeast-2"
AMI_ID = "ami-0ec61cd37ec14eb06"
INSTANCE_TYPE = "t2.micro"
KEY_NAME = "nico_projectKey"
SECURITY_GROUP_IDS = ["sg-06130228d6c599dd4"]