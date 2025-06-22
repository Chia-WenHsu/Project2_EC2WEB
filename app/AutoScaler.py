from aiobotocore.session import get_session
import asyncio

REGION = "ap-northeast-2"
MAX_INSTANCE = 11
AMI_ID = "ami-011dae5f0fc7d1a64"
INSTANCE_TYPE = "t2.micro"
KEY_NAME = "nico_projectKey"
SECURITY_GROUP_IDS = ["sg-06130228d6c599dd4"]
REQUEST_QUEUE_URL = "https://sqs.ap-northeast-2.amazonaws.com/530751794867/project2-request-q"
COOLDOWN_CYCLE = 20

low_queue_counter = 0

async def get_sqs_q_depth():
    session = get_session()
    async with session.create_client("sqs", region_name=REGION) as sqs:
        response = await sqs.get_queue_attributes(
            QueueUrl=REQUEST_QUEUE_URL,
            AttributeNames=["ApproximateNumberOfMessages"]
        )
        return int(response["Attributes"]["ApproximateNumberOfMessages"])


async def get_current_app_instance():
    session = get_session()
    async with session.create_client("ec2", region_name=REGION) as ec2:
        response = await ec2.describe_instances(
            Filters=[
                {"Name": "tag:Name", "Values": ["app-instance*"]},
                {"Name": "instance-state-name", "Values": ["pending", "running"]}
            ]
        )
        instances = [i['InstanceId'] for r in response['Reservations'] for i in r['Instances']]
        return instances


async def launch_app_instances(count):
    session = get_session()
    async with session.create_client("ec2", region_name=REGION) as ec2:
        tasks = []
        for i in range(count):
            tasks.append(ec2.run_instances(
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
                IamInstanceProfile={'Name': 'CSE546WebRole'}
            ))
        await asyncio.gather(*tasks)


async def terminate_app_instances(count_to_terminate):
    session = get_session()
    async with session.create_client("ec2", region_name=REGION) as ec2:
        response = await ec2.describe_instances(
            Filters=[
                {"Name": "tag:Name", "Values": ["app-instance*"]},
                {"Name": "instance-state-name", "Values": ["running"]}
            ]
        )
        instance_infos = []
        for r in response['Reservations']:
            for i in r['Instances']:
                instance_infos.append({
                    "InstanceId": i["InstanceId"],
                    "LaunchTime": i["LaunchTime"]
                })

        to_terminate = sorted(instance_infos, key=lambda x: x["LaunchTime"], reverse=True)[:count_to_terminate]
        instance_ids = [i["InstanceId"] for i in to_terminate]

        if instance_ids:
            await ec2.terminate_instances(InstanceIds=instance_ids)
            print(f" Terminating instances: {instance_ids}")
        else:
            print("沒有可關閉的裝置")


async def scale_app_instances():
    global low_queue_counter

    queue_depth = await get_sqs_q_depth()
    current_instances = await get_current_app_instance()
    current_count = len(current_instances)

    if queue_depth > 1:
        desired_count = min(10, MAX_INSTANCE)
    else:
        desired_count = 1

    print(f"Queue: {queue_depth},  Running: {current_count},  Target: {desired_count}")

    if current_count < desired_count:
        to_add = desired_count - current_count
        print(f" 建立 {to_add} instances")
        await launch_app_instances(to_add)
        low_queue_counter = 0  # 有擴展就重設
    elif current_count > desired_count:
        low_queue_counter += 1
        print(f" 累積低佇列次數: {low_queue_counter}/{COOLDOWN_CYCLE}")
        if low_queue_counter >= COOLDOWN_CYCLE:
            to_remove = current_count - desired_count
            print(f" 執行縮容：準備關閉 {to_remove} instances")
            await terminate_app_instances(to_remove)
            low_queue_counter = 0
    else:
        print(" 無須擴展/縮容")
        low_queue_counter = 0
