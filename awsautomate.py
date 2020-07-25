import boto3
import click

@click.command()
def list_instances():
    "List all of the EC2 instances"
    for i in myEc2.instances.all():
        print((' , '.join([i.id,i.instance_type,i.placement['AvailabilityZone'],i.state['Name'],i.private_dns_name])))

if __name__ == "__main__":
    session = boto3.Session(profile_name="awsautomate")
    myEc2 = session.resource('ec2')
    list_instances();
