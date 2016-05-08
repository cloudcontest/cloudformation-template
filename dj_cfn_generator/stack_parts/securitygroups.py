from troposphere import Ref, GetAtt, Join, Output
from troposphere.ec2 import SecurityGroup, SecurityGroupIngress, SecurityGroupEgress
from troposphere.ec2 import Tag


def init(t, r):
    stackname = Ref('AWS::StackName')
    # ELB Security Group + Rules
    r['elb_securitygroup'] = t.add_resource(SecurityGroup(
        "ELBSecurityGroup",
        GroupDescription=Join("", ["DOMserver ELB Security Group - ", stackname]),
        Tags=[
            Tag("Name", Join("", [stackname, "-elb"])),
            Tag("djclusterid", stackname)
        ]
    ))
    t.add_resource(SecurityGroupIngress(
        "InternetToELBPort80",
        IpProtocol="tcp", FromPort="80", ToPort="80",
        CidrIp="0.0.0.0/0",
        GroupId=GetAtt(r['elb_securitygroup'], 'GroupId')
    ))
    t.add_resource(SecurityGroupEgress(
        "ELBToAny",
        IpProtocol="-1", FromPort="0", ToPort="0",
        CidrIp="0.0.0.0/0",
        GroupId=GetAtt(r['elb_securitygroup'], 'GroupId')
    ))

    # Webserver Security Group + Rules
    r['webserver_securitygroup'] = t.add_resource(SecurityGroup(
        "WebserverSecurityGroup",
        GroupDescription=Join("", ["DOMserver Webserver Security Group - ", stackname]),
        Tags=[
            Tag("Name", Join("", [stackname, "-web"])),
            Tag("djclusterid", stackname)
        ]
    ))
    t.add_resource(SecurityGroupIngress(
        "ELBToWebserverHTTP",
        IpProtocol="tcp", FromPort="80", ToPort="80",
        SourceSecurityGroupId=GetAtt(r['elb_securitygroup'], 'GroupId'),
        GroupId=GetAtt(r['webserver_securitygroup'], 'GroupId')
    ))
    t.add_resource(SecurityGroupEgress(
        "WebserverAllowAllOutbound",
        IpProtocol="-1", FromPort="0", ToPort="0",
        CidrIp="0.0.0.0/0",
        GroupId=GetAtt(r['webserver_securitygroup'], 'GroupId')
    ))
    t.add_output(Output(
        'WebserverSecurityGroupId',
        Description="Webserver SecurityGroup ID",
        Value=GetAtt(r['webserver_securitygroup'], 'GroupId')
    ))

    # RDS Security Group + Rules
    r['rds_securitygroup'] = t.add_resource(SecurityGroup(
        "RDSSecurityGroup",
        GroupDescription=Join("", ["RDS Security Group - ", stackname]),
        Tags=[
            Tag("Name", Join("", [stackname, "-rds"])),
            Tag("djclusterid", stackname)
        ]
    ))
    t.add_resource(SecurityGroupIngress(
        "WebserverToRDS",
        IpProtocol="tcp", FromPort="3306", ToPort="3306",
        SourceSecurityGroupId=GetAtt(r['webserver_securitygroup'], 'GroupId'),
        GroupId=GetAtt(r['rds_securitygroup'], 'GroupId')
    ))

    # Judgehost security group
    r['judgehost_securitygroup'] = t.add_resource(SecurityGroup(
        "JudgehostSecurityGroup",
        GroupDescription=Join("", ["DOMserver Judgehost Security Group - ", stackname]),
        Tags=[
            Tag("Name", Join("", [stackname, "-judgehost"])),
            Tag("djclusterid", stackname)
        ]
    ))
    t.add_resource(SecurityGroupEgress(
        "JudgehostToAnywhere",
        IpProtocol="-1", FromPort="0", ToPort="0",
        CidrIp="0.0.0.0/0",
        GroupId=GetAtt(r['judgehost_securitygroup'], 'GroupId')
    ))
