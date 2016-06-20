#!/usr/bin/env python3
"""
Script to build a layered VPC in AWS

Uses a three layer model for subnets with

web layer: public subnet
app layer: private subnet for app servers
app layer: private subnet

An exercise in using boto3 to interact with AWS
"""
import os.path
from itertools import product
from collections import namedtuple, OrderedDict

import botocore
import boto3
import yaml
from ipaddress import IPv4Network, AddressValueError

# define the network layers for the VPC
NETWORK_LAYERS = ('web', 'app', 'rds')

# Set the prefix length for building the subnets
SUBNET_PREFIX = 25  # 128(-5 for AWS) = 123 hosts per subnet

# location of template files
RESOURCES_DIRECTORY = '../resources'

# security group rulesets
SECURITY_RULES_FILE = 'security_group_rules.yaml'

# namedtuples used for security group firewall rules
IPRule = namedtuple('IPRule', 'proto from_port to_port source')

# initialise the connections to AWS needed by LayeredVPC
try:
    ec2c = boto3.client('ec2')
    ec2 = boto3.resource('ec2')
except botocore.exceptions.ClientError as e:
    print('Unable to get client or resource')
    print(e['Error']['Message'])
    raise e

class LayeredVPC():
    """Custom VPC for AWS that implements three newtork layers"""

    def __init__(self,
                 vpc_name=None,
                 cidr_block='10.0.0.0/16'):
        super(LayeredVPC, self).__init__()
        self._name = vpc_name
        self._cidr_block = IPv4Network(cidr_block)
        self.vpc = ec2.create_vpc(CidrBlock=str(self._cidr_block))
        self.vpc.create_tags(Tags=[{'Key': 'Name', 'Value': self._name}])

    @property
    def name(self):
        """Return name of VPC"""
        return self._name

    @property
    def cidr_block(self):
        """Return Cidr block for VPC"""
        return self._cidr_block

    @property
    def vpcid(self):
        """Return VPC id"""
        try:
            return self.vpc.id
        except AttributeError:
            return 'VPC not created yet'

    def create_subnets(self, subnet_prefix=None):
        """Create the subnets (3 per AZ as there are 3 network_layers)

        The number of subnets will be calculated automatically according
        to the number of available AZs in the current region. The size
        of the subnet is set by the module constant SUBNET_PREFIX and this value
        must be greater than the netmask value of the
        VPC cidr block"""

        if not subnet_prefix:
            subnet_prefix = SUBNET_PREFIX

        MIN_PREFIX = 17
        MAX_PREFIX = 28

        # Get generator for subnet sequence
        # (perhaps should be part of the product method?)
        try:
            if not MIN_PREFIX <= subnet_prefix <= MAX_PREFIX:
                raise ValueError
            subnet_list = self._cidr_block.subnets(new_prefix=subnet_prefix)
        except ValueError as e:
            print('Subnet prefix not valid or not in range for VPC CIDR block')
            raise e

        # define generator expression to retrieve
        # available AZs for the current region
        self._zones = (
            zone['ZoneName']
            for zone in ec2c.describe_availability_zones()['AvailabilityZones']
            if zone['State'] == 'available'
            )

        for network_layer, zone in product(NETWORK_LAYERS, self._zones):
            subnet_cidr = str(next(subnet_list))
            subnet = self.vpc.create_subnet(
                CidrBlock=subnet_cidr,
                AvailabilityZone=zone)
            subnet_name = '{0}-{1}-{2}'.format(self.name, network_layer, zone)
            subnet.create_tags(Tags=[{'Key': 'Name', 'Value': subnet_name}])

    def create_internet_gateway(self):
        """Create VPC internet gateway"""
        gateway_name = 'igw'
        route_table_name = 'public-rtb'

        self.igw = ec2.create_internet_gateway()
        self.igw.attach_to_vpc(VpcId=self.vpcid)
        self.igw.create_tags(Tags=[{
            'Key': 'Name',
            'Value': '{0}-{1}'.format(self.name, gateway_name)}])

        wrt = ec2.create_route_table(VpcId=self.vpcid)

        wrt.create_tags(Tags=[{
            'Key': 'Name',
            'Value': '{0}-{1}'.format(self.name, route_table_name)}])

        wrt.create_route(
            DestinationCidrBlock='0.0.0.0/0',
            GatewayId=self.igw.id
            )

        # Add the public subnets of the web layer to the route table
        web_subnet_filter = [{
            'Name': 'tag:Name',
            'Values' : ['{0}-web*'.format(self.name)]}]
        for each_web_net in self.vpc.subnets.filter(Filters=web_subnet_filter):
            wrt.associate_with_subnet(SubnetId=each_web_net.id)

    def create_security_groups(self, security_data=None):
        """Build security groups from yaml file"""

        if not security_data:
            security_data = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            RESOURCES_DIRECTORY,
            SECURITY_RULES_FILE)

        security_groups = OrderedDict()
        with open(security_data, 'r') as yaml_data:
            security_groups = yaml.safe_load(yaml_data)

        # First create the security groups
        self._security_group_ids = dict()
        for secgrp in security_groups.keys():
            grp_name = security_groups[secgrp]['group_name']
            description = security_groups[secgrp]['description']
            try:
                security_group = ec2.create_security_group(
                    GroupName=grp_name,
                    Description=description,
                    VpcId=self.vpcid)
                security_group.create_tags(Tags=[{
                    'Key' : 'Name',
                    'Value' : '{0}-{1}'.format(self.name, grp_name)}])
                self._security_group_ids[secgrp] = security_group
            except botocore.client.ClientError as e:
                print('Unable to create security group')
                raise e

        # Next add the ingress and egress rules
        for secgrp in security_groups.keys():
            group = self._security_group_ids[secgrp]
            ingress_rules = security_groups[secgrp]['ip_permissions']
            if ingress_rules:
                ingress_permissions = self._build_security_group_rule(ingress_rules)
                group.authorize_ingress(**ingress_permissions)
            egress_rules = security_groups[secgrp]['ip_permissions_egress']
            if egress_rules:
                egress_permissions = self._build_security_group_rule(egress_rules)
                group.authorize_egress(**egress_permissions)

    def _build_security_group_rule(self, rules):
        """Utility to build a rule definition from a list

        Returns a dict with the IpPermissions attribute
        set to the supplied rule"""
        rule_list = list()
        authorize_rules = dict()
        for rule in rules:
            ip_rule = IPRule(*rule)
            ip_permissions_base = {
                'IpProtocol': ip_rule.proto,
                'FromPort': int(ip_rule.from_port),
                'ToPort': int(ip_rule.to_port),
                }
            # check if we are dealing with a cidr IP
            # or a security group name
            try:
                my_ip = IPv4Network(ip_rule.source)
                ip_source = {'IpRanges': [{'CidrIp': str(my_ip)}]}
            except AddressValueError:
                ip_source = {'UserIdGroupPairs': [{
                    'GroupId': self._security_group_ids[ip_rule.source].id,
                    'VpcId': self.vpcid}]}
            rule_list.append({**ip_permissions_base, **ip_source})
        authorize_rules['IpPermissions'] = rule_list
        return authorize_rules

    def create_rds_subnet_group(self):
        """Create a subnet group from the 'rds' subnets"""

        rds_subnet_filter = [{
            'Name' : 'tag:Name',
            'Values' : ['{0}-rds*'.format(self.name)]}]

        rds_subnets = [
            subnet.id
            for subnet in self.vpc.subnets.filter(Filters=rds_subnet_filter)]

        dbsubnet_args = {
            'DBSubnetGroupName': '{0}-db-net'.format(self.name),
            'DBSubnetGroupDescription': 'Subnet for RDS instances',
            'SubnetIds': rds_subnets,
            'Tags' : [{'Key': 'Name', 'Value': 'rds_subnet'}]}

        rdsc = boto3.client('rds')
        rdsc.create_db_subnet_group(**dbsubnet_args)
