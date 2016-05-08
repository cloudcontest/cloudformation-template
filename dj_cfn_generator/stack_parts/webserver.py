from troposphere import Ref, Base64, Join, GetAtt, GetAZs, If, FindInMap, Output
from troposphere.ec2 import Tag as ec2Tag
from troposphere.autoscaling import Tag as asgTag
from troposphere.autoscaling import AutoScalingGroup, LaunchConfiguration, ScalingPolicy
from troposphere.elasticloadbalancing import HealthCheck, Listener, LoadBalancer, ConnectionDrainingPolicy
from troposphere.cloudwatch import Alarm, MetricDimension
from troposphere.policies import UpdatePolicy, AutoScalingRollingUpdate, CreationPolicy, ResourceSignal


def build_user_data(r):

    parts = ["""#!/bin/bash
# The archive that contains the version of domserver to install
cat >/root/env_vars <<EVARS
export DOMSERVER_S3_BUCKET=\"""", Ref(r['s3_bucket']), """\"
export DOMSERVER_S3_FILE=\"""", Ref(r['s3_archive']), """\"
export DOMSERVER_S3_REGION=\"""", Ref(r['s3_region']), """\"


# Set variables that the install script might need
export DJCLUSTERID=\"""", Ref('AWS::StackName'), """\"
export DYNAMODB_REGION=\"""", Ref("AWS::Region"), """\"
export DYNAMODB_TABLE=\"""", Ref(r['sessiontable']), """\"
export DBHOST=\"""", GetAtt(r['rds_database'], "Endpoint.Address"), """\"
export DBNAME=\"""", Ref(r['db_name']), """\"
export DBUSER=\"""", Ref(r['db_user']), """\"
export DBPASS=\"""", Ref(r['db_pass']), """\"
export JUDGEHOSTPASS=\"""", Ref(r['judgehost_pass']), """\"
export ADMINPASS=\"""", Ref(r['admin_pass']), """\"
EVARS
source /root/env_vars
/root/deploy_domserver.sh

# notify cloudformation we're ready/done now
aws cloudformation signal-resource --stack-name """, Ref('AWS::StackName'), " --region ", {"Ref": "AWS::Region"},
             " --logical-resource-id WebserverAutoScalingGroup",
             " --unique-id $(curl -s http://169.254.169.254/latest/meta-data/instance-id)",
             " --status SUCCESS", """
"""]

    return Base64(Join('', parts))


def init(t, r):
    stackname = Ref('AWS::StackName')

    webserver_userdata = build_user_data(r)

    r['webserver_elb'] = t.add_resource(LoadBalancer(
        "WebserverELB",
        AvailabilityZones=GetAZs(Ref("AWS::Region")),
        Listeners=[
            Listener(
                "HTTPListener",
                LoadBalancerPort="80", Protocol="http",
                InstancePort="80", InstanceProtocol="http",
            )
        ],
        ConnectionDrainingPolicy=ConnectionDrainingPolicy(
            Enabled=True,
            Timeout=30
        ),
        CrossZone=True,
        SecurityGroups=[GetAtt(r['elb_securitygroup'], 'GroupId')],
        HealthCheck=HealthCheck(
            Target="HTTP:80/public/index.php",
            Timeout=10,
            Interval=15,
            HealthyThreshold=2,
            UnhealthyThreshold=10,
        ),
        Tags=[
            ec2Tag("Name", Join("", [stackname, "-elb"])),
            ec2Tag("djclusterid", stackname)
        ]
    ))
    t.add_output(Output(
        'ELBEndpointAddress',
        Description="ELB endpoint address",
        Value=GetAtt('WebserverELB', 'DNSName')
    ))
    lc = LaunchConfiguration(
        "WebserverLaunchConfiguration",
        ImageId=Ref(r['web_ami']),
        InstanceType=If(
            "IsStaging",
            't2.micro',
            FindInMap("SizeMap", Ref(r['contestsize']), 'WebInstanceType')
        ),
        SecurityGroups=[GetAtt(r['webserver_securitygroup'], 'GroupId')],
        UserData=webserver_userdata,
        InstanceMonitoring=If("IsStaging", "False", "True"),
        IamInstanceProfile=Ref(r['webserver_instanceprofile']),
        KeyName=Ref(r['aws_keypair'])
    )
    #if settings['web_spot_price']:
    #    lc.SpotPrice = str(settings['web_spot_price'])
    r['webserver_lc'] = t.add_resource(lc)

    # TODO: would be neat to use scheduled actions to automatically scale up for the real contest
    # TODO: however there seems to be a bug with that and updatepolicy: https://forums.aws.amazon.com/thread.jspa?threadID=170910
    r['webserver_asg'] = t.add_resource(AutoScalingGroup(
        "WebserverAutoScalingGroup",
        AvailabilityZones=GetAZs(Ref("AWS::Region")),
        LaunchConfigurationName=Ref(r['webserver_lc']),
        LoadBalancerNames=[Ref(r['webserver_elb'])],

        UpdatePolicy=UpdatePolicy(
            AutoScalingRollingUpdate=AutoScalingRollingUpdate(
                PauseTime='PT5M',
                MinInstancesInService="0",
                MaxBatchSize='1',
                WaitOnResourceSignals=True
            )
        ),
        CreationPolicy=CreationPolicy(
            ResourceSignal=ResourceSignal(
                Timeout='PT15M'
            )
        ),
        HealthCheckGracePeriod=300,  # 5 Minute grace period(this should match the PauseTime in UpdatePolicy above)
        HealthCheckType="EC2",  # FIXME: should be ELB

        DesiredCapacity=If(
            "IsStaging",
            '1',
            FindInMap("SizeMap", Ref(r['contestsize']), 'WebASGMinSize')
        ),
        MinSize=If(
            "IsStaging",
            '1',
            FindInMap("SizeMap", Ref(r['contestsize']), 'WebASGMinSize')
        ),
        MaxSize=If(
            "IsStaging",
            '1',
            FindInMap("SizeMap", Ref(r['contestsize']), 'WebASGMaxSize')
        ),

        Tags=[
            asgTag("djclusterid", stackname, True),
            asgTag("Name", Join("", [stackname, "-web"]), True)
        ]
    ))

    # Autoscale policies + cloudwatch triggers
    r['webserver_scaleout_policy'] = t.add_resource(ScalingPolicy(
        "WebserverScaleoutPolicy",
        AutoScalingGroupName=Ref(r['webserver_asg']),
        Cooldown=300,    # 5 minutes
        AdjustmentType="ChangeInCapacity",
        ScalingAdjustment="1"
    ))
    r['webserver_scalein_policy'] = t.add_resource(ScalingPolicy(
        "WebserverScaleinPolicy",
        AutoScalingGroupName=Ref(r['webserver_asg']),
        Cooldown=300,    # 5 minutes
        AdjustmentType="ChangeInCapacity",
        ScalingAdjustment="-1"
    ))

    r['webserver_scaleout_alarm'] = t.add_resource(Alarm(
        "WebserverScaleoutAlarm",
        AlarmDescription=Join("", [stackname, " Scale Out Web Tier"]),
        Namespace="AWS/EC2",
        MetricName="CPUUtilization",
        Dimensions=[
            MetricDimension(
                Name="AutoScalingGroupName",
                Value=Ref(r['webserver_asg'])
            )
        ],
        Statistic="Average",
        EvaluationPeriods="1",
        Period="300",
        Threshold="80",    # Greater than 80% cpu for 5 minutes
        ComparisonOperator="GreaterThanThreshold",
        AlarmActions=[Ref(r['webserver_scaleout_policy'])],
        InsufficientDataActions=[]
    ))

    r['webserver_scalein_alarm'] = t.add_resource(Alarm(
        "WebserverScaleinAlarm",
        AlarmDescription=Join("", [stackname, " Scale In Web Tier"]),
        Namespace="AWS/EC2",
        MetricName="CPUUtilization",
        Dimensions=[
            MetricDimension(
                Name="AutoScalingGroupName",
                Value=Ref(r['webserver_asg'])
            )
        ],
        Statistic="Average",
        EvaluationPeriods="4",
        Period="300",
        Threshold="30",    # Les than 30% for 20 minutes
        ComparisonOperator="LessThanThreshold",
        AlarmActions=[Ref(r['webserver_scaleout_policy'])],
        InsufficientDataActions=[]
    ))

    # Load Balancer Alarms
    r['elb_healthy_hosts_alarm'] = t.add_resource(Alarm(
        "ELBHealthyHostCountAlarm",
        AlarmDescription=Join("", [stackname, " ELB no healthy backend hosts"]),
        Namespace="AWS/ELB",
        MetricName="HealthyHostCount",
        Dimensions=[
            MetricDimension(
                Name="LoadBalancerName",
                Value=Ref(r['webserver_elb'])
            )
        ],
        Statistic="Average",
        EvaluationPeriods="1",
        Period="300",
        Threshold="1",    # minimum 1 health host
        ComparisonOperator="LessThanThreshold",
        AlarmActions=[r['notify_topic']],
        InsufficientDataActions=[r['notify_topic']]
    ))

    r['elb_latency_alarm'] = t.add_resource(Alarm(
        "ELBLatencyAlarm",
        AlarmDescription=Join("", [stackname, " HIGH ELB Latency"]),
        Namespace="AWS/ELB",
        MetricName="Latency",
        Dimensions=[
            MetricDimension(
                Name="LoadBalancerName",
                Value=Ref(r['webserver_elb'])
            )
        ],
        Statistic="Average",
        EvaluationPeriods="1",
        Period="300",
        Threshold="0.5",    # 0.5s latency
        ComparisonOperator="GreaterThanThreshold",
        AlarmActions=[r['notify_topic']],
        InsufficientDataActions=[r['notify_topic']]
    ))

    r['elb_5xx_error_alarm'] = t.add_resource(Alarm(
        "ELB5XXErrorAlarm",
        AlarmDescription=Join("", [stackname, " HIGH ELB backend 5xx error rate"]),
        Namespace="AWS/ELB",
        MetricName="HTTPCode_Backend_5XX",
        Dimensions=[
            MetricDimension(
                Name="LoadBalancerName",
                Value=Ref(r['webserver_elb'])
            )
        ],
        Statistic="Sum",
        EvaluationPeriods="1",
        Period="300",
        Threshold="0",    # Any 5xx errors are bad
        ComparisonOperator="GreaterThanThreshold",
        AlarmActions=[r['notify_topic']],
        InsufficientDataActions=[r['notify_topic']]
    ))
