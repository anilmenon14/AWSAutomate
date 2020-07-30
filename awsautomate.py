import boto3
import click

#helper functions

def retrieve_instances(project):
    if project:
        filter = [{'Name':'tag:Project','Values':[project]}]
        instances = myEc2.instances.filter(Filters=filter)
    else:
        instances = myEc2.instances.all() # No filters applied
    return instances


@click.group()
def instances_actions():
    "Actions to run on EC2 instances"
    #instances_actions has been decorated to be the parent function of all commands

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
def stop_instances(project,num):
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

if __name__ == "__main__":
    session = boto3.Session(profile_name="awsautomate")
    myEc2 = session.resource('ec2')
    instances_actions();
