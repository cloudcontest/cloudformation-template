#!/usr/bin/env python
from troposphere import Ref, Join
from troposphere.dynamodb2 import (KeySchema, AttributeDefinition,
                                   ProvisionedThroughput, Table)
from troposphere.cloudwatch import Alarm, MetricDimension


def init(t, r):
    stackname = Ref('AWS::StackName')

    dynamodb_capacity = Ref(r['dynamodb_capacity'])
    # Create the DynamoDB Session Table
    r['sessiontable'] = t.add_resource(Table(
        "SessionTable",
        AttributeDefinitions=[
            AttributeDefinition(
                AttributeName="id",
                AttributeType="S"
            )
        ],
        KeySchema=[
            KeySchema(
                AttributeName="id",
                KeyType="HASH"
            )
        ],
        ProvisionedThroughput=ProvisionedThroughput(
            ReadCapacityUnits=dynamodb_capacity,
            WriteCapacityUnits=dynamodb_capacity
        )
    ))

    # Read and Write Capacity alarms
    for x in "Read", 'Write':
        r['sessiontable_{}alarm'.format(x.lower())] = t.add_resource(Alarm(
            "SessionTable{}CapacityAlarm".format(x),
            AlarmDescription=Join("", [stackname, "{} capacity limit on the session table".format(x)]),
            Namespace="AWS/DynamoDB",
            MetricName="Consumed{}CapacityUnits".format(x),
            Dimensions=[
                MetricDimension(
                    Name="TableName",
                    Value=Ref(r['sessiontable'])
                )
            ],
            Statistic="Sum",
            Period="300",
            EvaluationPeriods="1",
            Threshold="{}".format(240),    # 80% of capacity. TODO: this needs to scale with dynamodb_capacity
            ComparisonOperator="GreaterThanThreshold",
            AlarmActions=[r['notify_topic']],
            InsufficientDataActions=[r['notify_topic']]
        ))
    # throttled requests alarm
    r['sessiontable_throttlealarm'] = t.add_resource(Alarm(
        "SessionTableThrottledRequestAlarm",
        AlarmDescription=Join("", [stackname, "requests are being throttled on the session table"]),
        Namespace="AWS/DynamoDB",
        MetricName="ThrottledRequests",
        Dimensions=[
            MetricDimension(
                Name="TableName",
                Value=Ref(r['sessiontable'])
            )
        ],
        Statistic="Sum",
        Period="300",
        EvaluationPeriods="1",
        Threshold="1",    # warn about any errors
        ComparisonOperator="GreaterThanOrEqualToThreshold",
        AlarmActions=[r['notify_topic']],
        InsufficientDataActions=[r['notify_topic']]
    ))
