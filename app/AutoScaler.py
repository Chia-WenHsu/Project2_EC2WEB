import boto3

REGION = "ap-northeast-2"
MAX_INSTANCE =  11 
AMI_ID = "ami-011dae5f0fc7d1a64"
INSTANCE_TYPE = "t2.micro"
KEY_NAME = "nico_projectKey"
SECURITY_GROUP_IDS = ["sg-06130228d6c599dd4"]
REQUEST_QUEUE_URL = "https://sqs.ap-northeast-2.amazonaws.com/530751794867/project2-request-q"


ec2 = boto3.client('ec2', region_name=REGION)
sqs = boto3.client('sqs', region_name=REGION)

low_queue_counter = 0
COOLDOWN_CYCLE = 3

def get_sqs_q_depth():
    response = sqs.get_queue_attributes(
        QueueUrl=REQUEST_QUEUE_URL,
        AttributeNames=['ApproximateNumberOfMessages']

    )
    return int(response['Attributes']['ApproximateNumberOfMessages'])


## 取的現在多少instance
def get_current_app_instance():
    response = ec2.describe_instances(
        Filters=[
            {'Name': 'tag:Name', 'Values': ['app-instance*']},
            {'Name': 'instance-state-name', 'Values': ['pending', 'running']}
        ]
    )
    instances = [i['InstanceId'] for r in response['Reservations'] for i in r['Instances']]
    return instances


## 創立instance
def launch_app_instances(count):
    for i in range(count):
        ec2.run_instances(
            ImageId=AMI_ID,
            InstanceType=INSTANCE_TYPE,
            KeyName=KEY_NAME,
            MaxCount=1,
            MinCount=1,
            SecurityGroupIds=SECURITY_GROUP_IDS,
            TagSpecifications=[{
                'ResourceType': 'instance',
                'Tags': [{'Key': 'Name', 'Value': f'app-instance{i+1}'}]
            }],
            IamInstanceProfile={  
                'Name': 'CSE546WebRole'  
            }
        )


## 關掉instanse
def terminate_app_instances(count_to_terminate):
    response = ec2.describe_instances(
        Filters=[
            {'Name': 'tag:Name', 'Values': ['app-instance*']},
            {'Name': 'instance-state-name', 'Values': ['running']}
        ]
    )
    instance_infos = []
    for r in response['Reservations']:
        for i in r['Instances']:
            instance_infos.append({
                'InstanceId': i['InstanceId'],
                'LaunchTime': i['LaunchTime']
            })

    to_terminate = sorted(instance_infos, key=lambda x: x['LaunchTime'], reverse=True)[:count_to_terminate]
    instance_ids = [i['InstanceId'] for i in to_terminate]

    if instance_ids:
        ec2.terminate_instances(InstanceIds=instance_ids)
        print(f"關掉裝置中: {instance_ids}")
    else:
        print("沒有裝置")

def scale_app_instances():
    global low_queue_counter

    queue_depth = get_sqs_q_depth()
    current_instances = get_current_app_instance()
    current_count = len(current_instances)
    desired_count = min(max(queue_depth, 1), MAX_INSTANCE)

    print(f"Queue: {queue_depth},  Running: {current_count},  Target: {desired_count}")

    if queue_depth > 1:
        desired_count = min(10, MAX_INSTANCE)
    else:
        desired_count = 1


    if current_count < desired_count:
        to_add = desired_count - current_count
        print(f" 建立 {to_add} instances")
        launch_app_instances(to_add)
        low_queue_counter = 0  # 有擴張就重設

    elif current_count > desired_count:
        low_queue_counter += 1  # ✅ 關鍵：累加降載次數
        print(f" 累積低佇列次數: {low_queue_counter}/{COOLDOWN_CYCLE}")
        if low_queue_counter >= COOLDOWN_CYCLE:
            to_remove = current_count - desired_count
            print(f"🔥 Terminating {to_remove} excess instances")
            terminate_app_instances(to_remove)
            low_queue_counter = 0  # 關完再重設

    else:
        print(" 無須擴展")
        low_queue_counter = 0
