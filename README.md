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

Navigate to project root folder to run below:  

### List instances
`pipenv run python awsautomate list`

List all of the EC2 instances

Options:
--project TEXT  Lists out instances only of tag(of name'Project') specified

### Stop instances
`pipenv run python awsautomate stop`

Stops number of instances specified (Default = 1)
(1) Stops oldest instance first
(2) If no 'project' tag specified , will stop any instance (based on oldest)     
(3) To stop all instances of project, pass 'stopall' option

Options:
--project TEXT  Stops instances only of tag(of name'Project') specified
--num INTEGER   Number of instances to stop
--stopall TEXT  Pass --stopall=True to stop every instance in specified
                project (or all if no project specified)

### Start instances
`pipenv run python awsautomate start`

Starts number of instances specified (Default = 1)
(1) Starts existing stopped instances first  
(2) If no 'project' tag specified , will start any stopped instance

Options:
--project TEXT  Starts instances only with tag(of name'Project') specified
--num INTEGER   Number of instances to start

### Terminate instances
`pipenv run python awsautomate terminate`

Lists out stopped instances and allows choice of stopped instance to terminate

Options:
--project TEXT  List of stopped instances with tag(of name'Project')specified
