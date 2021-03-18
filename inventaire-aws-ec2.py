from collections import defaultdict
import boto3
 
ec2_client = boto3.client("ec2")
response = ec2_client.describe_regions()
for region in response['Regions']:
    print(region)
    work_region = region['RegionName']
    ec2 = boto3.resource('ec2',
                         region_name=work_region)
 
                         
    # Get information for all running instances
 
    running_instances = ec2.instances.filter(Filters=[{
        'Name': 'instance-state-name',
        'Values': ['running', 'stopped', 'terminated']}])
    ec2info = defaultdict()
    for instance in running_instances:
        for tag in instance.tags:
            if 'Name' in tag['Key']:
                name = tag['Value']
        
        # Add instance info to a dictionary
 
        ec2info[instance.id] = {
            'Name': name,
            'Instance ID': instance.id,
            'State': instance.state['Name']
        }
    attributes = ['Instance ID', 'Name', 'State']
    for instance_id, instance in ec2info.items():
        for key in attributes:
            print("{0}: {1}".format(key, instance[key]))
        print("------")
        volume_iterator = ec2.volumes.all()
    for instance_id, instance in ec2info.items():
        for key in attributes:
            print("{0}: {1}".format(key, instance[key]))
        print("------")
    
    #ec2 = boto3.resource('ec2')
    
    volume_iterator = ec2.volumes.all()
    for v in volume_iterator:
        for a in v.attachments:
            print("{0} {1} {2}".format(v.id, v.state, a['InstanceId']))
    print("------")
