from troposphere import Ref, GetAtt, Join, FindInMap, If, Output
from troposphere.rds import DBInstance, DBParameterGroup
from troposphere.ec2 import Tag
from troposphere.cloudwatch import Alarm, MetricDimension


def init(t, r):
    stackname = Ref('AWS::StackName')

    r['rds_parametergroup'] = t.add_resource(DBParameterGroup(
        "DOMjudgeParameterGroup",
        Family="mysql5.6",
        Description=Join("", [stackname, " database configuration"]),
        Parameters={
            "max_allowed_packet": "{}".format(256 * 1024 * 2014),  # 256MB

            "character_set_client": "utf8mb4",
            "character_set_database": "utf8mb4",
            "character_set_results": "utf8mb4",
            "character_set_connection": "utf8mb4",
            "character_set_server": "utf8mb4",

            "collation_connection": "utf8mb4_unicode_ci",
            "collation_server": "utf8mb4_unicode_ci",
        }
    ))

    r['rds_database'] = t.add_resource(DBInstance(
        "RDSDatabase",
        AllocatedStorage=10,
        StorageType="gp2",
        DBInstanceClass=If(
            "IsStaging",
            'db.t2.micro',
            FindInMap("SizeMap", Ref(r['contestsize']), 'RDSInstanceType')
        ),
        Engine="MySQL",
        MultiAZ=If("IsStaging", "False", "True"),

        DBName=Ref(r['db_name']),
        MasterUsername=Ref(r['db_user']),
        MasterUserPassword=Ref(r['db_pass']),

        VPCSecurityGroups=[GetAtt(r['rds_securitygroup'], 'GroupId')],

        PreferredBackupWindow="02:00-03:00",
        PreferredMaintenanceWindow=Ref(r['rds_maintenancewindow']),
        #PreferredMaintenanceWindow="tue:00:00-tue:01:00",

        DBParameterGroupName=Ref(r['rds_parametergroup']),
        Tags=[Tag('djclusterid', stackname)]
    ))

    t.add_output(Output(
        'RDSEndpointAddress',
        Description="RDS endpoint address",
        Value=GetAtt('RDSDatabase', 'Endpoint.Address')
    ))
    t.add_output(Output(
        'RDSEndpointPort',
        Description="RDS port number",
        Value=GetAtt('RDSDatabase', 'Endpoint.Port')
    ))

    # Cloudwatch alarms
    r['rds_cpu_alarm'] = t.add_resource(Alarm(
        "RDSCpuAlarm",
        AlarmDescription=Join("", [stackname, " HIGH RDS CPU Utilization"]),
        Namespace="AWS/RDS",
        MetricName="CPUUtilization",
        Dimensions=[
            MetricDimension(
                Name="DBInstanceIdentifier",
                Value=Ref(r['rds_database'])
            )
        ],
        Statistic="Average",
        EvaluationPeriods="1",
        Period="300",
        Threshold="50",    # 50% or higher cpu
        ComparisonOperator="GreaterThanThreshold",
        AlarmActions=[r['notify_topic']],
        InsufficientDataActions=[r['notify_topic']]
    ))

    r['rds_free_space_alarm'] = t.add_resource(Alarm(
        "RDSFreeSpaceAlarm",
        AlarmDescription=Join("", [stackname, " LOW free storage space"]),
        Namespace="AWS/RDS",
        MetricName="FreeStorageSpace",
        Dimensions=[
            MetricDimension(
                Name="DBInstanceIdentifier",
                Value=Ref(r['rds_database'])
            )
        ],
        Statistic="Average",
        EvaluationPeriods="1",
        Period="300",
        Threshold="{}".format(1000 * 1000 * 1000),    # less than 1G of space free
        ComparisonOperator="LessThanThreshold",
        AlarmActions=[r['notify_topic']],
        InsufficientDataActions=[r['notify_topic']]
    ))

    r['rds_read_latency_alarm'] = t.add_resource(Alarm(
        "RDSReadLatencyAlarm",
        AlarmDescription=Join("", [stackname, " HIGH read latency"]),
        Namespace="AWS/RDS",
        MetricName="ReadLatency",
        Dimensions=[
            MetricDimension(
                Name="DBInstanceIdentifier",
                Value=Ref(r['rds_database'])
            )
        ],
        Statistic="Average",
        EvaluationPeriods="1",
        Period="300",
        Threshold="0.1",    # 100ms
        ComparisonOperator="GreaterThanThreshold",
        AlarmActions=[r['notify_topic']],
        InsufficientDataActions=[r['notify_topic']]
    ))

    r['rds_write_latency_alarm'] = t.add_resource(Alarm(
        "RDSWriteLatencyAlarm",
        AlarmDescription=Join("", [stackname, " HIGH write latency"]),
        Namespace="AWS/RDS",
        MetricName="WriteLatency",
        Dimensions=[
            MetricDimension(
                Name="DBInstanceIdentifier",
                Value=Ref(r['rds_database'])
            )
        ],
        Statistic="Average",
        EvaluationPeriods="1",
        Period="300",
        Threshold="0.1",    # 100ms
        ComparisonOperator="GreaterThanThreshold",
        AlarmActions=[r['notify_topic']],
        InsufficientDataActions=[r['notify_topic']]
    ))
