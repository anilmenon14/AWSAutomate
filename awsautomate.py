import boto3

if __name__ == "__main__":
    session = boto3.Session(profile_name="awsautomate")
    myEc2 = session.resource('ec2')

    for i in myEc2.instances.all():
        print(i)
