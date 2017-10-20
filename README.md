## CloudFormation-Cleaner

### Overview

This function was designed to solve the problem of long running tasks, in particular, the timely
teardown of resources once the task is complete.  This repo contains two components; a Lambda function,
and a script to be run on the instance upon completion of a task.

### Components

* function.py ( The Lambda Function )
* cloudformation-cleaner.py ( Script to generate CloudFormation Template )
* notify-completion.py ( Script to download and run on the instance within a stack to be removed on completion )
* templates/cloudformation-cleaner.json ( Template to deploy cloudformation-cleaner and associated resources )

### How to Use

#### Deploy Lambda Function

1. Deploy Lambda function using cloudformation-cleaner.json template and record ARN after creation. 
(Look at the CloudFormation Output Tab)

#### Set up long running task stack to notify Lambda

In order for the Lambda function to execute, you need to create your stack with the following items:
* An SNS topic *my-topic*
* Subscription for Lambda to *my-topic*
* After the stack is created, you need to manually add the Lambda trigger from your SNS topic (Still looking
at how to automate)

#### Download and run completion script

1.  Install ec2-metadata dependency using pip:
`pip install ec2-metadata`

2.  Download the notify_completion.py script:
`curl -o /tmp/notify_completion.py https://raw.githubusercontent.com/venicegeo/cloudformation-cleaner/master/notify_completion.py`

3.  Execute script by providing topic name:
`python /tmp/notify_completion.py --topic topic_name`
The script will automatically determine the stack name and other information, and send a notification
using SNS containing the stack name and uptime.  Provided that the Lambda function is subscribed to
the SNS topic, it will then delete the stack.