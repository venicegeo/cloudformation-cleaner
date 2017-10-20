#!/usr/bin/python3
import boto3
import json

def lambda_handler( event, context ):
  print(event['Records'][0]['Sns']['Message'])
  message_data = event['Records'][0]['Sns']['MessageAttributes']
  
  uptime = message_data['Uptime']['Value']
  stack_name = message_data['Stack']['Value']

  client = boto3.client('cloudformation')
  stacks = client.list_stacks()
  
  for stack in stacks['StackSummaries']:
    if stack['StackName'] == stack_name and "DELETE_COMPLETE" not in stack['StackStatus']:
      client.delete_stack(
        StackName = stack_name
      )
      return "Deleted Stack:" + stack['StackName'] + " ARN:" + stack['StackId'] + " Ran for:" + uptime + " hours"
  return "No Stack Deleted"