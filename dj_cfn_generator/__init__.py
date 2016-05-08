from troposphere import Ref, Template, Select
from stack_parts import parameters, dynamodb, iam, webserver, securitygroups, rds, judgehost


def generate_json():
    r = {}
    t = Template()
    # t.add_description(Join('', ["DOMjudge Cluster - ", Ref('AWS::StackName')]))
    t.add_description("DOMjudge Cluster")

    r['notify_topic'] = Select(0, Ref("AWS::NotificationARNs"))

    t.add_mapping('SizeMap', {
        'nano': {
            'RDSInstanceType': 'db.t2.micro',
            'WebInstanceType': 't2.micro',
            'WebASGMinSize': 1,
            'WebASGMaxSize': 4,
            'JudgeASGMinSize': 1,
            'JudgeASGMaxSize': 4,
        },
        'small': {
            'RDSInstanceType': 'db.t2.micro',
            'WebInstanceType': 't2.micro',
            'WebASGMinSize': 1,
            'WebASGMaxSize': 4,
            'JudgeASGMinSize': 1,
            'JudgeASGMaxSize': 4,
        },
        'medium': {
            'RDSInstanceType': 'db.t2.micro',
            'WebInstanceType': 't2.micro',
            'WebASGMinSize': 1,
            'WebASGMaxSize': 4,
            'JudgeASGMinSize': 1,
            'JudgeASGMaxSize': 4,
        },
        'large': {
            'RDSInstanceType': 'db.t2.micro',
            'WebInstanceType': 't2.micro',
            'WebASGMinSize': 1,
            'WebASGMaxSize': 4,
            'JudgeASGMinSize': 1,
            'JudgeASGMaxSize': 4,
        },
    })

    parameters.init(t, r)
    dynamodb.init(t, r)
    iam.init(t, r)
    securitygroups.init(t, r)
    rds.init(t, r)
    webserver.init(t, r)
    judgehost.init(t, r)

    return t.to_json()
