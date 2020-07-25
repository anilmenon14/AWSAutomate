# AWSAutomate

Automate tasks to manage services in AWS

## About

 This is a project containing common commands I would use to automate tasks in AWS

## Configuration

Install the AWS CLI E.g. link available as of Jul 2020 is [here](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2-windows.html)

Install boto3 in the pipenv using:
`pipenv install boto3`

to create a profile name with name as 'awsautomate' (as used in the code in this project), run command below:
`aws configure --profile awsautomate`


## Execute program

Navigate to project root folder and run below:
`pipenv run python awsautomate`
