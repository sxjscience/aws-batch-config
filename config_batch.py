import boto3
import logging


def basic_configuration():
    ret = dict()
    ret['jobDefinitionName'] = 'gluon-nlp-g4-12dn'
    ret['type'] = 'container'
    ret['containerProperties'] = {
        'image': '747303060528.dkr.ecr.us-east-1.amazonaws.com/gluon-nlp-1:gpu-ci-latest',
        'vcpus': 48,
        'memory': 180000,
        'command': ["./gluon_nlp_job.sh",
                    "Ref::SOURCE_REF",
                    "Ref::WORK_DIR",
                    "Ref::COMMAND",
                    "Ref::SAVED_OUTPUT",
                    "Ref::SAVE_PATH",
                    "Ref::REMOTE"],
        "resourceRequirements": [
            {
                "type": "GPU",
                "value": "4"
            }
        ],
        # Issue: https://forums.aws.amazon.com/thread.jspa?messageID=953912
        # "linuxParameters": {
        #     'sharedMemorySize': 2000
        # }
    }
    return ret


client = boto3.client('batch', region_name='us-east-1')
response = client.register_job_definition(**basic_configuration())
print(response)
