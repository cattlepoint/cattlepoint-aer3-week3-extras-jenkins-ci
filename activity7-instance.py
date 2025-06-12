#!/usr/bin/env python3
"""
activity7-instance.py – Start or stop the Jenkins EC2 instance created by the
"jenkins-ci" CloudFormation stack.

Usage:
  python activity7-instance.py --start
  python activity7-instance.py --stop

The AWS region is taken from the AWS_DEFAULT_REGION environment variable.
"""
from __future__ import annotations

import argparse
import os
import sys

import boto3
from botocore.exceptions import BotoCoreError, ClientError

STACK_NAME = "jenkins-ci"
LOGICAL_ID = "JenkinsInstance"

def get_region() -> str:
    region = os.environ.get("AWS_DEFAULT_REGION")
    if not region:
        sys.exit("AWS_DEFAULT_REGION is not set")
    return region

def get_instance_id(cf, stack_name: str, logical_id: str) -> str:
    """Return the physical instance ID for *logical_id* in *stack_name*."""
    try:
        resp = cf.describe_stack_resource(StackName=stack_name,
                                          LogicalResourceId=logical_id)
        return resp["StackResourceDetail"]["PhysicalResourceId"]
    except (BotoCoreError, ClientError) as exc:
        sys.exit(f"Unable to retrieve instance ID: {exc}")

def change_state(ec2, instance_id: str, action: str) -> None:
    """Start or stop *instance_id* and wait until it reaches the goal state."""
    if action == "start":
        ec2.start_instances(InstanceIds=[instance_id])
        waiter = ec2.get_waiter("instance_running")
    else:
        ec2.stop_instances(InstanceIds=[instance_id])
        waiter = ec2.get_waiter("instance_stopped")
    waiter.wait(InstanceIds=[instance_id])
    print(f"{action.title()}ed instance {instance_id}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Start or stop the Jenkins EC2 instance.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--start", action="store_true", help="Start the instance")
    group.add_argument("--stop", action="store_true", help="Stop the instance")
    args = parser.parse_args()

    region = get_region()
    cf_client = boto3.client("cloudformation", region_name=region)
    ec2_client = boto3.client("ec2", region_name=region)

    instance_id = get_instance_id(cf_client, STACK_NAME, LOGICAL_ID)

    if args.start:
        change_state(ec2_client, instance_id, "start")
    else:
        change_state(ec2_client, instance_id, "stop")

if __name__ == "__main__":
    main()
