# This function is designed to create a message in a previously created SNS topic
# for the purpose of triggering a lambda cleaner function

import boto3
from datetime import timedelta
from ec2_metadata import ec2_metadata
import sys
import argparse
import json
import subprocess

# Function to get the uptime of the instance as a string
# Format is Days Hours:Minutes:Seconds.Microseconds
def get_uptime():
  try:
    with open('/proc/uptime', 'r') as f:
      uptime_seconds = float(f.readline().split()[0])
      uptime = timedelta(seconds = uptime_seconds)
  except:
      uptime = "unknown"
  return str(uptime)

# Function to find the ARN of the SNS topic given the topic name
def get_topic_arn( topic_name ):
  global sns
  topics = (sns.list_topics())
  for topic in topics['Topics']:
    if topic_name in topic['TopicArn']:
      return topic['TopicArn']
      
# Function to find the region the instance is in
def get_region():
  try:
    region = ec2_metadata.region
    return region
  except Exception as e:
    print("Error determining region:  " + e)
    exit(1)

# Function to find the stack name of the current instance
def get_stack( region ):
  instance_id = ec2_metadata.instance_id
  command = "aws ec2 describe-instances \
    --region " + region + " \
    --instance-id " + instance_id + " \
    --output json"
  response = json.loads(subprocess.check_output(command.split()))
  tags = response['Reservations'][0]['Instances'][0]['Tags']
  stack = None
  for tag in tags:
    if tag['Key'] == 'aws:cloudformation:stack-name':
      stack = (tag['Value'])
  if stack is None:
    print("Unable to find stack name from metadata, exiting")
    exit(1)
  else:
    return stack

# Function to send a message to an SNS queue
def send_message( target_arn, stack ):
  global sns
  uptime = get_uptime()
  message = "Instance " + ec2_metadata.public_hostname + " ran for " + uptime
  try:
    sns.publish(
      TargetArn = target_arn,
      Subject = "Import Complete",
      Message = message,
      MessageStructure = 'string',
      MessageAttributes = {
        "Uptime" : {
          'DataType' : 'String',
          'StringValue' : uptime
        },
        "Stack" : {
          'DataType' : 'String',
          'StringValue' : stack
        }
      }
    )
    return "Sent Message to " + target_arn
  except Exception as e:
    return e

### Execution Begins Here ###
def main(argv):
  global sns
  
  # Get options, if any
  parser = argparse.ArgumentParser()
  parser.add_argument('-t','--topic', help='Topic name', required=True)
  parser.add_argument('-p','--profile', help='Profile to use, if configured', required=False)
  parser.add_argument('-r','--region', help='AWS Region', required=False)
  parser.add_argument('-s', '--stack', help='Stack name', required=False)
  args = parser.parse_args()
    
  # Set Variables
  topic = args.topic
  profile = args.profile
  
  if args.region is not None:
    region = args.region
  else:
    region = get_region()
  
  if args.stack is not None:
    stack = args.stack
  else:
    stack = get_stack( region )
  
  # Create the session
  if profile is not None:
    session = boto3.Session(region_name=region, profile_name=profile)
  else:
    session = boto3.Session(region_name=region)
  
  sns = session.client('sns')

  # Get the arn for the provided topic name
  topic_arn = get_topic_arn(topic)

  # Send Message to Queue
  print(send_message( topic_arn, stack ))
    
if __name__ == "__main__":
  main(sys.argv[1:])
  