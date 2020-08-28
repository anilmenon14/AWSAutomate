# AWSAutomate

Automate tasks to manage services in AWS  

## About

 This is a project containing common commands that can be used to run view/ execute commands from command line

## Configuration

Install the AWS CLI E.g. link available as of Jul 2020 is [here](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2-windows.html)  

Install boto3 in the pipenv using:  
`pipenv install boto3`

To create a profile name with name as 'awsautomate', run command below:   
`aws configure --profile awsautomate`

**Pre-requisite**: The above command will require you to pass Key ID and private key to set up. To get this , you will need to create a user in AWS IAM console and set it up for programmatic access. Download the csv of private key credentials from the console (IMPORTANT: It is only provided at time of creation. If you accidentally missed it, delete the user and create a new one and keep the csv).    
Use the contents of the csv to pass to command above.  


## Execute program

Navigate to project root folder to run below     

### EC2 commands

#### List instances
`pipenv run python awsautomate.py instances list`

**Note**: 'awsautomate' is the default name of profile used in the awsautomate script used for this project. If you would like to use a different name or have multiple profiles, each command needs to have a --profile flag.

E.g. `pipenv run python awsautomate.py --profile "otherusername" instances list`

List all of the EC2 instances  

Options:  
*project* TEXT  Lists out instances only of tag(of name'Project') specified  

#### Stop instances
`pipenv run python awsautomate.py instances stop`

Stops number of instances specified (Default = 1)  
(1) Stops oldest instance first  
(2) If no 'project' tag specified , will stop any instance (based on oldest)       
(3) To stop all instances of proect, pass 'stopall' option  

Options:  
*project* TEXT  Stops instances only of tag(of name'Project') specified  
*num* INTEGER   Number of instances to stop  
*stopall* TEXT  Pass --stopall=True to stop every instance in specified project (or all if no project specified)  

#### Start instances
`pipenv run python awsautomate.py instances start`

Starts number of instances specified (Default = 1)  
(1) Starts existing stopped instances first  
(2) If no 'project' tag specified , will start any stopped instance    

Options:  
*project* TEXT  Starts instances only with tag(of name'Project') specified  
*num* INTEGER   Number of instances to start  

#### Terminate instances
`pipenv run python awsautomate.py instances terminate`

Lists out stopped instances and allows choice of stopped instance to terminate  

Options:  
*project* TEXT  List of stopped instances with tag(of name'Project') specified

### S3 commands

#### List buckets
`pipenv run python awsautomate.py s3buckets list-buckets`

Lists out all the buckets present in the account

#### List objects
`pipenv run python awsautomate.py s3buckets list-objects`

Interactively choose bucket to list contents of

#### Create bucket
`pipenv run python awsautomate.py s3buckets create-bucket <newbucketname>`

Create a new bucket (replace <newbucketname> with desired name) in region of the profile associated to the script

#### Upload file
`pipenv run python awsautomate.py s3buckets upload-file <bucketname>`

Upload file to an S3 bucket (replace <bucketname> with existing bucket name)

Options:
*filename* TEXT    File to be uploaded.Provide relative path from current
                     working directory or full path from root  [required]

*asfilename* TEXT  Optional name the file has to be uploaded as (Do not
                     specify if required to be same as 'filename')

#### Upload dir
`pipenv run python awsautomate.py s3buckets upload-dir <bucketname>`

Upload directory to an S3 bucket (replace <bucketname> with existing bucket name)

Options:
*dirname* PATH  Directory to be uploaded. Should be present in present
                working directory  [required]

### Auto Scaling group commands
