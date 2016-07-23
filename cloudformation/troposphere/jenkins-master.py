#!/usr/bin/env python3
"""
Generate AWS cloudformation using the python
Troposphere library
"""

from troposphere import (
    Base64, Join, FindInMap, GetAtt, Parameter,
    Output, Ref, Template, Tags)
from troposphere.policies import (
    CreationPolicy, ResourceSignal)
import troposphere.ec2 as ec2

user_data_jenkins_master = """
#!/bin/bash -xe
wget -O /etc/yum.repos.d/jenkins.repo http://pkg.jenkins.io/redhat-stable/jenkins.repo
rpm --import http://pkg.jenkins.io/redhat-stable/jenkins.io.key
yum install jenkins -y
yum upgrade -y
"""

template = Template()

template.add_description("Configures an EC2 jenkins master")

keyname_param = template.add_parameter(Parameter(
    "KeyName",
    Description="Name of an existing ec2 keypair "
                "to enable SSH access to instance",
    Type="String",))

sshlocation_param = template.add_parameter(Parameter(
        "SSHLocation",
        Description='The IP address range that '
                    'can be used to SSH to the EC2 instances',
        Type='String',
        MinLength='9',
        MaxLength='18',
        Default='0.0.0.0/0',
        AllowedPattern="(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})/(\d{1,2})",
        ConstraintDescription=(
            "must be a valid IP CIDR range of the form x.x.x.x/x."),
    ))

vpcid_param = template.add_parameter(Parameter(
    "VpcId",
    Description="VpcId of your existing Virtual Private Cloud (VPC)",
    Type="String",
))

"""Use my pre-built Jenkins AMI to keep things simple for now"""
template.add_mapping('RegionMap', {
    "ap-southeast-2": {"AMI": "ami-559bb136"}, })

jenkins_sg = template.add_resource(
    ec2.SecurityGroup(
        'JenkinsSecurityGroup',
        GroupDescription='Enable SSH access via port 22',
        SecurityGroupIngress=[
            ec2.SecurityGroupRule(
                IpProtocol='tcp',
                FromPort='22',
                ToPort='22',
                CidrIp=Ref(sshlocation_param)),
            ec2.SecurityGroupRule(
                IpProtocol='tcp',
                FromPort='8080',
                ToPort='8080',
                CidrIp=Ref(sshlocation_param))],
        VpcId=Ref(vpcid_param),
        Tags=Tags(
            Name='jenkins-master',
            Role='jenkins',
            Owner='Peter Brown',
            Env='dev'
            )
    ))

ec2_instance = template.add_resource(ec2.Instance(
    "JenkinsInstance",
    ImageId=FindInMap("RegionMap", Ref("AWS::Region"), "AMI"),
    InstanceType="t2.micro",
    KeyName=Ref(keyname_param),
    SecurityGroupIds=[Ref(jenkins_sg)],
    #  UserData=Base64(user_data_jenkins_master),
    UserData=Base64(Join('', [
        '#!/bin/bash -xe\n',
        '/opt/aws/bin/cfn-signal -e $? ',
        '         --stack ',
        Ref("AWS::StackName"),
        '         --resource JenkinsInstance',
        '         --region ',
        Ref("AWS::Region"),
        '\n',])),
    CreationPolicy=CreationPolicy(
        ResourceSignal=ResourceSignal(
            Timeout='PT5M')),
    Tags=Tags(
        Name='jenkins-master',
        Role='jenkins',
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
