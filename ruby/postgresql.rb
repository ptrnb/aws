#!/usr/bin/env ruby

require 'bundler/setup'
require 'cloudformation-ruby-dsl/cfntemplate'
require 'cloudformation-ruby-dsl/spotprice'
require 'cloudformation-ruby-dsl/table'

template do

  value :AWSTemplateFormatVersion => '2010-09-09'

  value :Description => 'PostgreSQL'

  parameter 'DevOpsVPC',
            :Type => 'String',
            :Description => 'ID of the VPC to use'

  parameter 'DevOpsSubnetA',
            :Type => 'String',
            :Description => 'ID of a subnet to use'

  parameter 'DevOpsSubnetB',
            :Type => 'String',
            :Description => 'ID of a subnet to use'

  parameter 'DevOpsSubnetC',
            :Type => 'String',
            :Description => 'ID of a subnet to use'

  parameter 'DBName',
            :Type => 'String'

  parameter 'MasterUsername',
            :Type => 'String'

  parameter 'MasterUserPassword',
            :Type => 'String',
            :NoEcho => 'true'

  parameter 'EngineVersion',
            :Type => 'String'

  parameter 'MultiAZ',
            :Type => 'String',
            :Default => 'false'

  parameter 'DBInstanceClass',
            :Type => 'String',
            :Default => 'db.t2.medium'

  resource 'sb-pgsql-sg', :Type => 'AWS::EC2::SecurityGroup', :Properties => {
      :GroupDescription => 'Allow everything',
      :VpcId => ref('DevOpsVPC'),
      :SecurityGroupIngress => [
          { :CidrIp => '0.0.0.0/0', :IpProtocol => '-1', :FromPort => '5432', :ToPort => '5432' },
      ],
      :SecurityGroupEgress => [
          { :CidrIp => '0.0.0.0/0', :IpProtocol => '-1', :FromPort => '0', :ToPort => '65535' },
      ],
      :Tags => [
          {
              :Key => 'Name',
              :Value => join('', aws_stack_name, ' resource'),
          },
      ],
  }

  resource 'DBSNGroup', :Type => 'AWS::RDS::DBSubnetGroup', :Properties => {
      :DBSubnetGroupDescription => 'Database Subnet Group',
      :SubnetIds => [
          ref('DevOpsSubnetA'),
          ref('DevOpsSubnetB'),
          ref('DevOpsSubnetC'),
      ],
      :Tags => [
          {
              :Key => 'Name',
              :Value => join('', aws_stack_name, ' resource'),
          },
      ],
  }

  resource 'sb-pgsql-db', :Type => 'AWS::RDS::DBInstance', :Properties => {
      :AllocatedStorage => '30',
      :AllowMajorVersionUpgrade => 'false',
      :AutoMinorVersionUpgrade => 'false',
      :BackupRetentionPeriod => '7',
      :PreferredBackupWindow => '11:15-12:15',
      :CopyTagsToSnapshot => 'true',
      :DBInstanceClass => ref('DBInstanceClass'),
      :DBSubnetGroupName => ref('DBSNGroup'),
      :DBName => ref('DBName'),
      :Engine => 'postgres',
      :EngineVersion => ref('EngineVersion'),
      :MasterUsername => ref('MasterUsername'),
      :MasterUserPassword => ref('MasterUserPassword'),
      :MultiAZ => ref('MultiAZ'),
      :PubliclyAccessible => 'false',
      :VPCSecurityGroups => [ ref('sb-pgsql-sg') ],
      :Tags => [
          {
              :Key => 'Name',
              :Value => join('', aws_stack_name, ' resource'),
          },
          {
              :Key => 'Project',
              :Value => 'Solar',
          },
          {
              :Key => 'CostCentre',
              :Value => 'Solar',
          },
      ],
  }

  output 'DBEndpoint',
         :Value => get_att('sb-pgsql-db', 'Endpoint.Address')

  output 'DBName',
         :Value => ref('DBName')

  output 'MasterUsername',
         :Value => ref('MasterUsername')

  output 'MasterUserPassword',
         :Value => ref('MasterUserPassword')

end.exec!
