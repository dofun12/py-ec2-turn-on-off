# This is a sample Python script.

import datetime as dt
import logging
import os
import boto3
from apscheduler.schedulers.background import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

log = logging.getLogger(__name__)

INSTANCE_ID = os.getenv("INSTANCE_ID", None)
ACCESS_KEY_ID = os.getenv("ACCESS_KEY_ID", None)
SECRET_ACCESS_KEY = os.getenv("SECRET_ACCESS_KEY", None)
CF_ID = os.getenv("CF_ID", None)
REGION_NAME = os.getenv("REGION_NAME", "us-east-1")

if INSTANCE_ID is None or ACCESS_KEY_ID is None or SECRET_ACCESS_KEY is None or CF_ID is None:
    import sys

    log.error(
        f"The env is not setted INSTANCE_ID:{INSTANCE_ID} ACCESS_KEY_ID:{ACCESS_KEY_ID} SECRET_ACCESS_KEY:{SECRET_ACCESS_KEY} CF_ID:{CF_ID}")
    sys.exit(1)


def start_client(client):
    return boto3.client(
        client,
        aws_access_key_id=ACCESS_KEY_ID,
        aws_secret_access_key=SECRET_ACCESS_KEY,
        region_name=REGION_NAME
    )


ec2 = start_client('ec2')
cf = start_client('cloudfront')


def enable_disable_distribution(distribution_id, enabled=False):
    distribution = cf.get_distribution(Id=distribution_id)
    ETag = distribution['ETag']
    distribution_config = distribution['Distribution']['DistributionConfig']
    distribution_config['Enabled'] = enabled
    cf.update_distribution(DistributionConfig=distribution_config, Id=distribution_id, IfMatch=ETag)


def list_instances():
    print(ec2.describe_instances())


def get_instance_ids(instance_names):
    all_instances = ec2.describe_instances()

    instance_ids = []

    # find instance-id based on instance name
    # many for loops but should work
    for instance_name in instance_names:
        for reservation in all_instances['Reservations']:
            for instance in reservation['Instances']:
                if 'Tags' in instance:
                    for tag in instance['Tags']:
                        if tag['Key'] == 'Name' \
                                and tag['Value'] == instance_name:
                            instance_ids.append(instance['InstanceId'])

    return instance_ids


def lambda_handler(instance_ids, action):
    if action == 'Start':
        print("STARTing your instances: " + str(instance_ids))
        ec2.start_instances(InstanceIds=instance_ids)
        response = "Successfully started instances: " + str(instance_ids)
    elif action == 'Stop':
        print("STOPping your instances: " + str(instance_ids))
        ec2.stop_instances(InstanceIds=instance_ids)
        response = "Successfully stopped instances: " + str(instance_ids)


def enable_all():
    lambda_handler([INSTANCE_ID], "Start")
    enable_disable_distribution(CF_ID, True)


def disable_all():
    lambda_handler([INSTANCE_ID], "Stop")
    enable_disable_distribution(CF_ID, False)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    scheduler = BlockingScheduler()
    cron_start = "0 9 * * *"
    cron_end = "0 2 * * *"

    triggerStart = CronTrigger.from_crontab(cron_start)
    triggerEnd = CronTrigger.from_crontab(cron_end)

    log.info(f"Next execution of start ({cron_start}) is {triggerStart.get_next_fire_time(None, dt.datetime.now())}")
    log.info(f"Next execution of stop ({cron_end}) is {triggerStart.get_next_fire_time(None, dt.datetime.now())}")

    scheduler.add_job(enable_all, trigger=triggerStart, name='start')
    scheduler.add_job(disable_all, trigger=triggerStart, name='stop')

    scheduler.start()

