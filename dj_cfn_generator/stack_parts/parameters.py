from troposphere import Ref, Equals, Parameter


def init(t, r):
    r['envtype'] = t.add_parameter(Parameter(
        "EnvironmentType",
        Description='Environment Type',
        Type='String',
        AllowedValues=['stage', 'prod'],
        Default='stage',
        ConstraintDescription='Must specify stage or prod'
    ))
    r['is_staging'] = t.add_condition(
        "IsStaging",
        Equals(Ref(r['envtype']), 'stage')
    )
    r['is_producton'] = t.add_condition(
        "IsProduction",
        Equals(Ref(r['envtype']), 'prod')
    )

    r['contestsize'] = t.add_parameter(Parameter(
        "ContestSize",
        Description='Contest Size',
        Type='String',
        AllowedValues=['nano', 'small', 'medium', 'large'],
        Default='small',
        ConstraintDescription='Must specify one of nano, small, medium, or large'
    ))

    r['dynamodb_capacity'] = t.add_parameter(Parameter(
        "DynamoDBCapacity",
        Description='DynamoDB Initial Capacity',
        Type='Number',
        Default='10',
    ))

    # r['route53domain'] = t.add_parameter(Parameter(
    #     "Route53Domain",
    #     Description='Route53 domain to create the subdomain in(Make sure it has a trailing .)',
    #     Type='String',
    #     Default="cloudcontest.org."
    # ))

    r['s3_bucket'] = t.add_parameter(Parameter(
        "S3DeployBucket",
        Description='S3 Deployment Bucket',
        Type='String',
        Default='domserver-archives',
    ))
    r['s3_region'] = t.add_parameter(Parameter(
        "S3DeployRegion",
        Description='S3 Deployment Region',
        Type='String',
        Default='us-east-1',
    ))
    r['s3_archive'] = t.add_parameter(Parameter(
        "S3DeployArchive",
        Description='S3 Deployment Archive',
        Type='String',
        Default='latest',
    ))

    r['web_ami'] = t.add_parameter(Parameter(
        "WebserverAMI",
        Description='AMI for the webserver to use',
        Type='String',
        Default='ami-6797a60d'
    ))
    r['judgehost_ami'] = t.add_parameter(Parameter(
        "JudgehostAMI",
        Description='AMI for the judgehost to use',
        Type='String',
        Default='ami-f098c19a'
    ))
    r['judge_instance_type'] = t.add_parameter(Parameter(
        "JudgehostInstanceType",
        Description='Instance type to use for JudgeHosts',
        Type='String',
        Default='t2.micro'
    ))

    r['enable_judgehosts'] = t.add_parameter(Parameter(
        "EnableJudgehosts",
        Description='Whether to enable the running of Judgehosts on AWS',
        Type='String',
        Default='true',
        AllowedValues=['true', 'false'],
        ConstraintDescription='Must be either "true" or "false"'
    ))
    r['create_judgehosts'] = t.add_condition(
        "CreateJudgehosts",
        Equals(Ref(r['enable_judgehosts']), 'true')
    )

    # Database settings
    r['db_name'] = t.add_parameter(Parameter(
        "DatabaseName",
        Description='Database Name',
        Type='String',
        Default='domjudge'
    ))
    r['db_user'] = t.add_parameter(Parameter(
        "DatabaseUser",
        Description='Database User',
        Type='String',
        Default='domjudge'
    ))
    r['db_pass'] = t.add_parameter(Parameter(
        "DatabasePassword",
        Description='Database Password',
        Type='String',
        NoEcho=True,
    ))

    r['rds_maintenancewindow'] = t.add_parameter(Parameter(
        "RDSMaintenanceWindow",
        Description='RDS Maintenance Window(e.g. "Tue:04:00-Tue:04:30")',
        Type='String'
    ))

    # Passwords for DOMjudge accounts
    r['admin_pass'] = t.add_parameter(Parameter(
        "AdminPassword",
        Description='Admin Password',
        Type='String',
        NoEcho=True,
    ))
    r['judgehost_pass'] = t.add_parameter(Parameter(
        "JudgehostPassword",
        Description='Judgehost Password',
        Type='String',
        NoEcho=True,
    ))

    # misc things
    r['aws_keypair'] = t.add_parameter(Parameter(
        "AWSKeyPair",
        Description='Amazon EC2 Key Pair',
        Type='AWS::EC2::KeyPair::KeyName'
    ))
