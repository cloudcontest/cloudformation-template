from troposphere import Ref, Join
from troposphere.iam import Role, InstanceProfile

from troposphere.iam import PolicyType as IAMPolicy
from awacs.aws import Action, Allow, Statement, Principal, Policy
from awacs.sts import AssumeRole


def init(t, r):
    r['webserver_role'] = t.add_resource(Role(
        "WebServerRole",
        AssumeRolePolicyDocument=Policy(
            Statement=[
                Statement(
                    Effect=Allow,
                    Action=[AssumeRole],
                    Principal=Principal("Service", ["ec2.amazonaws.com"])
                )
            ]
        )
    ))
    r['webserver_policy'] = t.add_resource(IAMPolicy(
        "WebServerRolePolicy",
        PolicyName="WebServerRole",
        Roles=[Ref(r['webserver_role'])],
        PolicyDocument=Policy(
            Statement=[
                Statement(
                    Sid="1",
                    Effect="Allow",
                    Action=[Action("dynamodb", x) for x in ["DeleteItem", "UpdateItem", "GetItem", "PutItem"]],
                    Resource=[
                        # XXX: No ARN Attribute for a dynamodb table :/
                        Join("", ["arn:aws:dynamodb:", Ref("AWS::Region"), ":", Ref("AWS::AccountId"), ":table/", Ref(r['sessiontable'])])
                    ]
                ),
                Statement(
                    Sid="2",
                    Effect="Allow",
                    Action=[Action("cloudwatch", x) for x in ["PutMetricData", "GetMetricStatistics"]],
                    Resource=["*"]
                ),
                Statement(
                    Sid="3",
                    Effect="Allow",
                    Action=[Action("s3", x) for x in ["GetObject", "GetObjectVersion"]],
                    Resource=[
                        Join("", ["arn:aws:s3:::", Ref(r['s3_bucket'])]),
                        Join("", ["arn:aws:s3:::", Ref(r['s3_bucket']), "/*"]),
                    ]
                ),
                Statement(
                    Sid="4",
                    Effect="Allow",
                    Action=[Action("cloudformation", "SignalResource")],
                    Resource=[
                        Join("", ["arn:aws:cloudformation:", Ref("AWS::Region"), ":", Ref("AWS::AccountId"), ":stack/", Ref("AWS::StackName"), "/*"])
                    ]
                )
            ]
        )
    ))
    r['webserver_instanceprofile'] = t.add_resource(InstanceProfile(
        "WebServerInstanceProfile",
        Roles=[Ref(r['webserver_role'])],
        Path="/domjudge/"
    ))
