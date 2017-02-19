#!/usr/bin/env python3
"""
Generate AWS cloudformation using the python
Troposphere library
"""

from troposphere import (
    Base64, Join, FindInMap, GetAtt, Parameter,
    Output, Ref, Template, Tags)
import troposphere.ec2 as ec2

template = Template()

template.add_description("Configures an EC2 instance")

keyname_param = template.add_parameter(Parameter(
    "KeyName",
    Description="Name of an existing ec2 keypair "
                "to enable SSH access to instance",
    Type="String",))

template.add_mapping('RegionMap', {
    "ap-southeast-2": {"AMI": "ami-dc361ebf"}, })

for number in range(1, 3):
    ec2_instance = template.add_resource(ec2.Instance(
        "Ec2Instance{0:02d}".format(number),
        ImageId=FindInMap("RegionMap", Ref("AWS::Region"), "AMI"),
        InstanceType="t2.micro",
        KeyName=Ref(keyname_param),
        SecurityGroups=["Web-DMZ"],
        UserData=Base64(Join('', [
            '#!/bin/bash\n',
            'yum update -y'])),
        Tags=Tags(
            Name='my-cf-ec2-instance-{0:02d}'.format(number),
            Owner='Peter Brown',
            Env='dev'
            )
        ))

template.add_output([
    Output(
        "InstanceId",
        Description="InstanceId of the newly created EC2 instance",
        Value=Ref(ec2_instance),
    ),
    Output(
        "AZ",
        Description="Availability Zone of the newly created EC2 instance",
        Value=GetAtt(ec2_instance, "AvailabilityZone"),
    ),
    Output(
        "PublicIP",
        Description="Public IP address of the newly created EC2 instance",
        Value=GetAtt(ec2_instance, "PublicIp"),
    ),
    Output(
        "PrivateIP",
        Description="Private IP address of the newly created EC2 instance",
        Value=GetAtt(ec2_instance, "PrivateIp"),
    ),
    Output(
        "PublicDNS",
        Description="Public DNSName of the newly created EC2 instance",
        Value=GetAtt(ec2_instance, "PublicDnsName"),
    ),
    Output(
        "PrivateDNS",
        Description="Private DNSName of the newly created EC2 instance",
        Value=GetAtt(ec2_instance, "PrivateDnsName"),
    ),
])

print(template.to_json())
