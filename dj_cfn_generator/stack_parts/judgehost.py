from troposphere import Ref, Base64, Join, GetAtt, GetAZs, If, FindInMap
from troposphere.autoscaling import Tag as asgTag
from troposphere.autoscaling import AutoScalingGroup, LaunchConfiguration, ScalingPolicy
from troposphere.cloudwatch import Alarm


def build_user_data(r):
    parts = ["""#!/bin/bash
#!/bin/bash
cat >/etc/domjudge/restapi.secret <<EOF
default http://""", GetAtt(r['webserver_elb'], 'DNSName'), """/api/  judgehost  """, Ref(r['judgehost_pass']), """
EOF
"""]

    return Base64(Join('', parts))


def init(t, r):
    stackname = Ref('AWS::StackName')
    judgehost_userdata = build_user_data(r)

    lc = LaunchConfiguration(
        "JudgehostLaunchConfiguration",
        ImageId=Ref(r['judgehost_ami']),
        InstanceType=If(
            "IsStaging",
            't2.micro',
            Ref(r['judge_instance_type'])
        ),
        SecurityGroups=[GetAtt(r['judgehost_securitygroup'], 'GroupId')],
        UserData=judgehost_userdata,
        InstanceMonitoring=If("IsStaging", "False", "True"),
        KeyName=Ref(r['aws_keypair'])
    )
    #if settings['judge_spot_price']:
    #    lc.SpotPrice = str(settings['judge_spot_price'])
    r['judgehost_lc'] = t.add_resource(lc)

    r['judgehost_asg'] = t.add_resource(AutoScalingGroup(
        "JudgehostAutoScalingGroup",
        AvailabilityZones=GetAZs(Ref("AWS::Region")),
        LaunchConfigurationName=Ref(r['judgehost_lc']),
        DependsOn=[(r['webserver_asg']).name],
        DesiredCapacity=If(
            "CreateJudgehosts",
            If(
                "IsStaging",
                '1',
                FindInMap("SizeMap", Ref(r['contestsize']), 'JudgeASGMinSize')
            ),
            '0'
        ),
        MinSize=If(
            "CreateJudgehosts",
            If(
                "IsStaging",
                '1',
                FindInMap("SizeMap", Ref(r['contestsize']), 'JudgeASGMinSize')
            ),
            '0'
        ),
        MaxSize=If(
            "CreateJudgehosts",
            If(
                "IsStaging",
                '1',
                FindInMap("SizeMap", Ref(r['contestsize']), 'JudgeASGMaxSize')
            ),
            '0'
        ),

        HealthCheckGracePeriod=300,  # 5 Minute grace period
        HealthCheckType="EC2",

        Tags=[
            asgTag("djclusterid", stackname, True),
            asgTag("Name", Join("", [stackname, "-judge"]), True)
        ]
    ))

    # Autoscale policies + cloudwatch triggers
    r['judgehost_scaleout_policy'] = t.add_resource(ScalingPolicy(
        "JudgehostScaleoutPolicy",
        AutoScalingGroupName=Ref(r['judgehost_asg']),
        Cooldown=300,    # 5 minutes
        AdjustmentType="ChangeInCapacity",
        ScalingAdjustment="1"
    ))
    r['judgehost_scalein_policy'] = t.add_resource(ScalingPolicy(
        "JudgehostScaleinPolicy",
        AutoScalingGroupName=Ref(r['judgehost_asg']),
        Cooldown=300,    # 5 minutes
        AdjustmentType="ChangeInCapacity",
        ScalingAdjustment="-1"
    ))

    r['judgehost_scaleout_alarm'] = t.add_resource(Alarm(
        "JudgehostScaleoutAlarm",
        AlarmDescription=Join("", [stackname, " Scale Out Judgehosts"]),
        Namespace="DOMjudge",
        MetricName=Join("", [stackname, "-queuesize"]),
        Statistic="Average",
        EvaluationPeriods="2",
        Period="300",
        Threshold="40",    # More than 40 items in queue for 10 minutes
        ComparisonOperator="GreaterThanThreshold",
        AlarmActions=[Ref(r['judgehost_scaleout_policy'])],
        InsufficientDataActions=[]
    ))

    r['judgehost_scalein_alarm'] = t.add_resource(Alarm(
        "JudgehostScaleinAlarm",
        AlarmDescription=Join("", [stackname, " Scale In Judgehosts"]),
        Namespace="DOMjudge",
        MetricName=Join("", [stackname, "-queuesize"]),
        Statistic="Average",
        EvaluationPeriods="4",
        Period="300",
        Threshold="20",    # Less than 20 items in the queue for 20 minutes
        ComparisonOperator="LessThanThreshold",
        AlarmActions=[Ref(r['judgehost_scaleout_policy'])],
        InsufficientDataActions=[]
    ))
