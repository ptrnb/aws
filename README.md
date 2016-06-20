## Boto3 scripts for interacting with AWS ##

A minimum viable product for creating a custom three layer VPC in AWS. The layeredvpc module will build a custom vpc and uses python3's ipaddress module to automatically define the CIDR blocks for the subnets. Three subnets are created in each AZ - the web subnet (public) and the app and rds subnets (private). The web subnets are associated with the internet gateway when you create this component. You can also create an RDS subnet group from the rds subnets. At this time the module makes no attempt to provision any instances into the VPC. The default security group template is a yaml file that you will ideally override and you must update the IP inbound rule for port 22 to remove the default 'any' address (0.0.0.0/0) and replace this with the IP host or network from which you will be connecting by SSH to your custom VPC.

Created as an exercise in getting familiar with boto3.

Usage:

```python
    >>> from aws.tools.layeredvpc import LayeredVPC
    >>> my_vpc = LayeredVPC(vpc_name='abc', cidr_block='10.0.0.0/16')
    >>> my_vpc.create_subnets(subnet_prefix=24) # will build subnets with mask 255.255.255.0
    >>> my_vpc.create_internet_gateway()
    >>> my_vpc.create_security_groups(security_data='my_security_groups.yaml')
```

