#!/usr/bin/python3
from troposphere import (
  Base64, 
  Tags, 
  Join, 
  GetAtt,
  Parameter,
  Output,
  Ref,
  Template,
  Sub
  )
from troposphere.policies import (
  CreationPolicy,
  ResourceSignal,
  AutoScalingReplacingUpdate,
  AutoScalingRollingUpdate,
  UpdatePolicy
  )    
from awacs.aws import Allow, Statement, Policy, Action, Principal
from pathlib import Path
import troposphere.ec2 as ec2
import types
import sys, getopt
import os
import re
from troposphere.constants import NUMBER
from troposphere.awslambda import Function, Code, MEMORY_VALUES
from troposphere.cloudformation import CustomResource
from troposphere.iam import Role, Policy

# Naming Conventions
# My naming convention is a bit confusing, describe as follows:
# - CloudFormation resources are generated in JSON so they use CamelCase
# - Python variables and function names use lower_case_with_underscore_for_spaces
# - Strings that get displayed in the AWS console will be use dashes-for-spaces

## BEGIN Input Parameter Definition ##
## These are "global" parameters that will be assigned to all instances
parameters = {
      "LambdaMemorySize" : Parameter(
        'LambdaMemorySize',
        Type=NUMBER,
        Description='Amount of memory to allocate to the Lambda Function',
        Default='128',
        AllowedValues=MEMORY_VALUES
      ),
      "LambdaTimeout" : Parameter(
        'LambdaTimeout',
        Type=NUMBER,
        Description='Timeout in seconds for the Lambda function',
        Default='60'
      ),
    }
## BEGIN Python specific variable declaration ##

######### node_params usage ########
service_name = "CloudFormation-Cleaner"

## END  Input Parameter Definition ##

# Generates the tag parameter for everything except ASGs
def gen_tags(name):
  tags = Tags(
      Name = name,
      POC = "Grant Soyka",
      Project = "overhead",
      )
  return tags
  
def get_code():
  with open('function.py') as f:
    lines = f.read().splitlines()
  lines = [line+'\n' for line in lines]  
  return lines
    
def gen_lambda_function():
  function = Function(
      "CloudformationCleanupFunction",
      Code=Code(
          ZipFile=Join("", get_code())
      ),
      Handler="index.lambda_handler",
      Role=GetAtt("LambdaExecutionRole", "Arn"),
      Runtime="python3.6",
      MemorySize=Ref(parameters['LambdaMemorySize']),
      Timeout=Ref(parameters['LambdaTimeout']),
      Tags = gen_tags("CloudFormation-Cleaner")
  )
  return function
  
def gen_iam_role():
  LambdaExecutionRole = Role(
      "LambdaExecutionRole",
      Path="/",
      Policies=[Policy(
          PolicyName="CloudformationCleanerLambdaPolicy",
          PolicyDocument={
              "Version": "2012-10-17",
              "Statement": [{
                  "Action": [
                    "cloudformation:DeleteStack", 
                    "cloudformation:ListStacks", 
                    "cloudformation:DescribeStacks",
                    "iam:DeleteRolePolicy",
                    "iam:DeleteRole",
                    "iam:DeleteInstanceProfile",
                    "iam:RemoveRoleFromInstanceProfile",
                    "ec2:DescribeInstances",
                    "ec2:DeleteSecurityGroup",
                    "ec2:TerminateInstances",
                    "sns:DeleteTopic",
                    "sns:GetTopicAttributes",
                    "sns:ListSubscriptionsByTopic",
                    "sns:Unsubscribe",
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                  ],
                  "Resource": "*",
                  "Effect": "Allow"
              }
              ]
          })],
      AssumeRolePolicyDocument={
          "Version": "2012-10-17",
          "Statement": [{
              "Action": ["sts:AssumeRole"],
              "Effect": "Allow",
              "Principal": {
                  "Service": ["lambda.amazonaws.com"]
              }
          }]
      },
  )
  return LambdaExecutionRole
    
# Function to write template to specified file
def write_to_file( template ):
  
  # Define the directory to write to as a folder named templates in the current directory
  dir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), 'templates'))
  
  # Create the directory if it does not exist
  if not os.path.exists(dir):
    os.makedirs(dir)
  
  # Define filename for template equal to name of current script    
  filename = re.sub('\.py$','', sys.argv[0])
  file = os.path.join(dir,filename)
  
  # Write the template to file
  target = open(file + '.json', 'w')
  target.truncate()
  target.write(template)
  target.close()

######################## MAIN BEGINS HERE ###############################
def main(argv):
  # Set up a blank template
  t = Template()
  
  # Add description
  t.add_description("CloudFormation Cleaner Lambda Function")

  # Add all defined input parameters to template
  for p in parameters.values():
    t.add_parameter(p)
  
  # Create iam role and lambda function and add to template
  t.add_resource(gen_iam_role())
  t.add_resource(gen_lambda_function())
  
  t.add_output(Output(
    "LambdaFunctionArn",
    Description = "Arn for the Lambda Function",
    Value = GetAtt("CloudformationCleanupFunction", "Arn"),
  ))
  
  # Convert template to json
  template=(t.to_json())
  
  # Print template to console (for debugging) and write to file
  print(template)
  write_to_file(template)

if __name__ == "__main__":
  main(sys.argv[0:])