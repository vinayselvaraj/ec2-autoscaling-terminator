#!/usr/bin/env python2.7

import boto3
import collections
import math
from datetime import datetime

# Minimum instances to maintain in an AutoScaling Group
ASG_MIN_INSTANCES = 1

# Maxmimum percentage of instances in an autoscaling group to terminate
MAX_TERMINATE_PERCENTAGE = 50

# Minimum minutes to next billing hour
ASG_INST_MIN_MINS_TO_NEXT_BILLING_HOUR = 5

def lambda_handler(event, context):
  run()

def run():
  
  # Get low-level clients
  autoscale = boto3.client('autoscaling')
  ec2       = boto3.client('ec2')
  
  # Describe ASGs
  desc_asg_resp = autoscale.describe_auto_scaling_groups()
  as_groups = desc_asg_resp['AutoScalingGroups']
  
  # Iterate through each ASG
  for group in as_groups:
    
    # Get instances from group
    asg_instances = group['Instances']
    
    # Break out if ASG is at minimum instance count
    if len(asg_instances) <= ASG_MIN_INSTANCES:
      break
    
    # Get EC2 instance IDs
    instance_ids = list()
    for i in asg_instances:
      instance_ids.append(i['InstanceId'])
    
    # Get EC2 instance reservations
    ec2_desc_inst_resp = ec2.describe_instances(InstanceIds = instance_ids)
    reservations = ec2_desc_inst_resp['Reservations']
    
    # Add entries to dictionary contain minutes till next hourly bill and instance
    mins_instance = dict()
    for reservation in reservations:
      for instance in reservation['Instances']:
        minutes_to_next_bill = minutes_to_next_billing_hour(instance)
        if(minutes_to_next_bill < ASG_INST_MIN_MINS_TO_NEXT_BILLING_HOUR):
          mins_instance[minutes_to_next_bill] = instance
    
    # Calculate the # of instances to terminate
    group_instance_count = len(group['Instances'])
    terminate_count = int(math.ceil( group_instance_count * (MAX_TERMINATE_PERCENTAGE/100.0) ))
    if(group_instance_count - terminate_count < ASG_MIN_INSTANCES):
      terminate_count = group_instance_count - ASG_MIN_INSTANCES
    
    # Sort by time to next billing hour
    sorted_mins_instance = collections.OrderedDict( sorted(mins_instance.items()) )
    
    # Create a list of instances to terminate
    instances_to_terminate = list()
    for x in range(0, terminate_count):
      if(sorted_mins_instance):
        mins, instance = sorted_mins_instance.items()[0]
        sorted_mins_instance.pop(mins)
        instances_to_terminate.append( instance['InstanceId'] )
      else:
        break
    
    # Terminate the instances if there are any to terminate
    if(instances_to_terminate):
      print "Terminating instances: %s" % instances_to_terminate
      ec2.terminate_instances(InstanceIds = instances_to_terminate)


def minutes_to_next_billing_hour(instance):
  launch_time = instance['LaunchTime']
  launch_minute = launch_time.minute + (launch_time.second / 60.0)
  now_minute = datetime.now().minute + (datetime.now().second / 60.0)
  
  minutes = 0
  
  if(launch_minute > now_minute):
    minutes = launch_minute - now_minute
  else:
    minutes = (60.0 - now_minute) + launch_minute
  
  return minutes

if __name__ == "__main__":
  run()
