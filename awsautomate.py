import boto3
import botocore
import click
import mimetypes
from pathlib import Path
from functools import reduce
from hashlib import md5


#helper functions

def retrieve_instances(project):
    if project:
        filter = [{'Name':'tag:Project','Values':[project]}]
        instances = myEc2.instances.filter(Filters=filter)
    else:
        instances = myEc2.instances.all() # No filters applied
    return instances

def handle_dir_upload(bucketname,dir_name,origParentDir):
    if dir_name.is_file():
        print('ERROR: This is not a directory. Please try again with a directory')
        return
    for p in dir_name.iterdir():
        if p.is_dir():handle_dir_upload(bucketname,p,origParentDir)
        else:
            uploading_file = p.relative_to(origParentDir).as_posix()
            contenttype = mimetypes.guess_type(uploading_file)[0] or 'text/plain'
            etag = generate_etag(uploading_file)
            if manifest.get(bucketname+":"+uploading_file, '') == etag:
                print("File : {} , has not changed since last upload. Not uploading".format(uploading_file))
            else:
                print("Uploading: {}".format(uploading_file))
                try:
                    myS3.Bucket(bucketname).upload_file(uploading_file,uploading_file,ExtraArgs={'ContentType': contenttype})
                except:
                    print('An Error has occured. Check if bucket name and file name is accurate and if you have access to the bucket')
    return


def read_manifest():
    """Load contents from manifest.txt text file to a dictionary"""
    etags = {}
    with open('manifest.txt','r+') as file:
        for line in file.readlines():
            etags[line.split(",")[0].strip('"')] = line.split(",")[1].rstrip().strip('"')
    return etags

def sync_etags_manifest(bucketname):
    """Access bucket and load Etags from files in S3 and place in manifest.txt"""
    try:
        bucketIter = myS3.Bucket(bucketname).objects.all()
        eTagDict = {bucketname+":"+o.key:o.e_tag.strip('"') for o in bucketIter}
        #Update manifest variable
        for i in eTagDict:
            manifest[i] = eTagDict[i]
        #update manifest.txt
        with open('manifest.txt','r+') as file:
            file.truncate()
        with open('manifest.txt','r+') as file:
            for m in manifest:
                file.write(m+","+manifest[m])
                file.write('\n')
    except NoSuchBucket as error:
        print('No bucket of this name exists')
    return

def hash_data_gen(data):
    """Generate md5 hash for data."""
    generatedHash = md5()
    generatedHash.update(data)
    return generatedHash

def generate_etag(path):
    """Generate ETag for local files for comparison to AWS S3 retrieved ETags"""
    hashes = []
    with open(path,'rb') as file:
        while True:
            data = file.read(myS3FileChunkSize)
            if not data:
                break;
            hashes.append(hash_data_gen(data))
        if not hashes: #no files
            # Generate hash with '' since S3 seems to be doing same and need to mirror this to compare
            return hash_data_gen(''.encode('utf-8')).hexdigest()
        elif len(hashes) == 1: #only one file
            return hashes[0].hexdigest()
        else: #multiple files
            #hash all the hashes to a final hash
            concatHash = hash_data_gen(reduce(lambda x,y: x+y , (h.digest() for h in hashes)))
            return "{}-{}".format(concatHash.hexdigest(),len(hashes))



# end of helper functions

manifest = read_manifest() #load manifest file

@click.group()
@click.option('--profile',default='awsautomate',help="AWS profile name to use for the command. Default is 'awsautomate'")
def cli(profile):
    "Main CLI group calling instances, volumes and snapshot groups"
    global session, myEc2, myS3, myS3FileChunkSize, myS3transferConfig #These variables are required to be available globally
    session = boto3.Session(profile_name=profile)
    myEc2 = session.resource('ec2')
    myS3 = session.resource('s3')
    myS3FileChunkSize = 8388608
    myS3transferConfig = boto3.s3.transfer.TransferConfig(
                multipart_threshold = myS3FileChunkSize,
                multipart_chunksize = myS3FileChunkSize
            )

@cli.group('instances')
def instances_actions():
    "Actions to run on EC2 instances"
    #instances_actions has been decorated to be the parent function of all commands

@cli.group('s3buckets')
def s3_actions():
    "Actions to run on S3 buckets"

@instances_actions.command('list')
@click.option('--project',default=None,help="Lists out instances only of tag(of name'Project') specified")
def list_instances(project):
    "List all of the EC2 instances"
    instances = retrieve_instances(project)
    if not list(instances):
        print('No instances found on this search')
        return
    for i in instances:
        tags = {tag['Key']: tag['Value'] for tag in i.tags or []}
        print((' , '.join([
        tags.get('Project',"<no 'Project' tag>")
        ,i.id
        ,i.instance_type
        ,i.placement['AvailabilityZone']
        ,i.state['Name']
        ,i.private_dns_name,
        i.meta.data['LaunchTime'].strftime("%m/%d/%Y, %H:%M:%S")
        ])))

    return


@instances_actions.command('stop')
@click.option('--project',default=None,help="Stops instances only of tag(of name'Project') specified")
@click.option('--num',default=1,help="Number of instances to stop")
@click.option('--stopall',default=False,help="Pass --stopall=True to stop every instance in specified project (or all if no project specified)")
def stop_instances(project,num,stopall):
    """Stops number of instances specified (Default = 1)\n(1) Stops oldest instance first\n(2) If no 'project' tag specified , will stop any instance (based on oldest)
    (3) To stop all instances of project, pass 'stopall' option"""
    instances = retrieve_instances(project)
    #find running instances
    ids = {}
    for i in instances:
        if i.state['Name'] == 'running':
            ids[i.id] = i.meta.data['LaunchTime']

    #sort instance ID by oldest at start of list
    time_sort_tuples= sorted(ids.items(), key=lambda x:x[1]) #Generates list of tuples of (id,datetime) format
    time_sort_ids = list(map(lambda x: x[0],time_sort_tuples)) #pull out list of IDs only
    #if stopall is used
    if stopall=="True":
        print('Will stop all instances of specified project now')
        print('****Following Instances will be stopped****')
        print(time_sort_ids)
        myEc2.instances.filter(InstanceIds=time_sort_ids).stop()
        return
    #Below will run when stopall isn't set
    stopnum = len(time_sort_ids) if num > len(time_sort_ids) else num # Get number of inst to stop
    if stopnum == 0:
        print('0 instances to stop')
        return
    print("Existing {} running instances...".format(len(time_sort_ids)))
    print("Requesting to stop {} instances...".format(num))
    print("Stopping {} instances...".format(stopnum))
    print('****Following Instances will be stopped****')
    print(time_sort_ids[0:stopnum])
    myEc2.instances.filter(InstanceIds=time_sort_ids[0:stopnum]).stop()


    return


@instances_actions.command('start')
@click.option('--project',default=None,help="Starts instances only with tag(of name'Project') specified")
@click.option('--num',default=1,help="Number of instances to start")
def start_instances(project,num):
    """Starts number of instances specified (Default = 1)\n(1) Starts existing stopped instances first \n(2) If no 'project' tag specified , will start any stopped instance
    """
    instances = retrieve_instances(project)
    ids = []
    #find stopped instances
    for i in instances:
        if i.state['Name'] == 'stopped':
            ids.append(i.id)
    startnum = len(ids) if num > len(ids) else num
    if startnum == 0:
        print('0 instances to start')
        return
    print("Existing {} stopped instances".format(len(ids)))
    print("Requesting to start {} instances".format(num))
    print("Starting {} instances".format(startnum))
    print('****Following Instances will be started****')
    print(ids[0:startnum])
    myEc2.instances.filter(InstanceIds=ids[0:startnum]).start()
    return

@instances_actions.command('terminate')
@click.option('--project',default=None,help="List of stopped instances with tag(of name'Project') specified")
def terminate_stopped_instances(project):
    """Lists out stopped instances and allows choice of stopped instance to terminate"""
    instances = retrieve_instances(project)
    ids = {}
    #find stopped instances
    count = 0
    for i in instances:
        if i.state['Name'] == 'stopped':
            count = count + 1;
            ids[i.id] = {'slno': count, 'type': i.instance_type, 'private_dns_name': i.private_dns_name}
    if len(ids) == 0:
        print('0 instances available to terminate')
        return
    print("Existing {} stopped instances".format(len(ids)))
    print('Select serial number of options below to terminate:')
    print('Sl.no #')
    listSl = list(map(lambda i: str(ids[i]['slno']), ids))
    for id in ids:
        print("{}          {}    {}    {}".format(ids[id]['slno'],id,ids[id]['type'],ids[id]['private_dns_name']))
    print("Select serial number of options below to terminate ('Q' to quit) : ",end="")
    choice = input();
    while True:
        if choice == 'Q':
            print('Termination process cancelled')
            break
        elif choice in listSl:
            for i in ids:
                if ids[i]['slno'] == int(choice):
                    IdFromChoice = i;
            print("Your choice is '{}'----'{}':".format(choice,IdFromChoice))
            print('Please confirm (Y/N): ',end='')
            confirm = input()
            while True:
                if confirm.upper() == 'Y':
                    myEc2.instances.filter(InstanceIds=[IdFromChoice]).terminate()
                    print('Instance has been terminated')
                    break
                elif confirm.upper() == 'N':
                    print('Termination process cancelled')
                    break
                else:
                    print('Please confirm (Y/N): ',end='')
                    confirm = input()
            break
        print("Please select a valid serial number ('Q' to quit) : ",end="")
        choice = input();
    return

@s3_actions.command('list-buckets')
def list_buckets():
    """Lists out all the buckets present in the account"""
    for bucket in myS3.buckets.all():
        print(bucket)
    return

@s3_actions.command('list-objects')
def list_bucket_object():
    """Interactively choose bucket to list contents of"""
    bktCnt = 0
    bktTupleList = []
    for bucket in myS3.buckets.all():
        bktCnt += 1
        bktTupleList.append((bktCnt,bucket))
    choiceList = list(map(lambda i: str(i[0]),bktTupleList))
    for i in bktTupleList:
        print("{}-------{}".format(i[0],i[1].name))
    print("Select serial number of bucket to display objects('Q' to quit) : ",end="")
    choice = input();
    while True:
        if choice == 'Q':
            print('Process cancelled')
            break
        elif choice in choiceList:
            for i in bktTupleList:
                if i[0] == int(choice):
                    IdFromChoice = i[1];
            print("Your choice is '{}'----'{}':".format(choice,IdFromChoice))
            print('Please confirm (Y/N): ',end='')
            confirm = input()
            while True:
                if confirm.upper() == 'Y':
                    bucketObjects = myS3.Bucket(IdFromChoice.name).objects.all()
                    if not list(bucketObjects):
                        print('No objects currently in the bucket {}'.format(IdFromChoice.name))
                    for object in bucketObjects:
                        print(object)
                    break
                elif confirm.upper() == 'N':
                    print('Cancelled')
                    break
                else:
                    print('Please confirm (Y/N): ',end='')
                    confirm = input()
            break
        print("Please select a valid serial number ('Q' to quit) : ",end="")
        choice = input();
    return
#    for object in myS3.Bucket(bucket).objects.all():
#        print(object)
#    return

@s3_actions.command('create-bucket')
@click.argument('newbucketname')
def create_bucket(newbucketname):
    """Create a new bucket in region of the profile associated to the script"""
    bucketregion = session.region_name #session.region_name pulls up information from the profile region
    try:
        myS3.create_bucket(Bucket=newbucketname,CreateBucketConfiguration={'LocationConstraint': bucketregion})
    except botocore.exceptions.ClientError as e:
        print('An Error has occured...')
        print(e.response)

    return

@s3_actions.command('upload-file')
@click.argument('bucketname')
@click.option('--filename',required= True,help="File to be uploaded.Provide relative path from current working directory or full path from root")
@click.option('--asfilename',help="Optional name the file has to be uploaded as (Do not specify if required to be same as 'filename')")
def upload_file(bucketname,filename,asfilename):
    """Upload file to an S3 bucket"""
    sync_etags_manifest(bucketname); #loads Etags from s3 bucket as latest source of truth into manifest.txt
    contenttype = mimetypes.guess_type(filename)[0] or 'text/plain'

    cwd = Path.cwd().resolve()
    filename = Path(filename).resolve() #converting to Path object

    try:
        relFileName = filename.relative_to(cwd).as_posix()
        etag = generate_etag(relFileName)
        if manifest.get(bucketname+":"+relFileName, '') == etag:
            print("File : {} , has not changed since last upload. Not uploading".format(filename))
            return None
        if not asfilename:
            asfilename = relFileName
        print("Uploading: {}".format(relFileName))
        myS3.Bucket(bucketname).upload_file(relFileName,asfilename,ExtraArgs={'ContentType': contenttype},Config=myS3transferConfig)
    except ValueError as error:
        print('Value Error:',end="")
        print(error)
    except FileNotFoundError as error:
        print('File name is incorrect or does not exist')
    except :
        print('An Error has occured. Check if bucket name and file name is accurate and if you have access to the bucket')

    return


@s3_actions.command('upload-dir')
@click.argument('bucketname')
@click.option('--dirname',required= True,type=click.Path(exists=True),help="Directory to be uploaded. Should be present in present working directory")
def upload_dir(bucketname,dirname):
    """Upload directory to an S3 bucket"""
    sync_etags_manifest(bucketname); #loads Etags from s3 bucket as latest source of truth into manifest.txt
    dirname = Path(dirname).resolve() # Conver path to valid directory
    parentDir = Path.cwd()
    handle_dir_upload(bucketname,dirname,parentDir)

    return



if __name__ == "__main__":
    cli();
