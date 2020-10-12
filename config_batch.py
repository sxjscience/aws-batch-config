import boto3
import logging

instance_info_mapping = {
    # P2 Instance
    'p2.xlarge': {'vcpus': 4, 'memory': 15000, 'num_gpu': 1},
    'p2.8xlarge': {'vcpus': 32, 'memory': 30000, 'num_gpu': 8},
    'p2.16xlarge': {'vcpus': 64, 'memory': 62000, 'num_gpu': 16},

    # G4 Instance
    'g4dn.xlarge': {'vcpus': 4, 'memory': 15000, 'num_gpu': 1},
    'g4dn.2xlarge': {'vcpus': 8, 'memory': 30000, 'num_gpu': 1},
    'g4dn.4xlarge': {'vcpus': 16, 'memory': 62000, 'num_gpu': 1},
    'g4dn.8xlarge': {'vcpus': 32, 'memory': 126000, 'num_gpu': 1},
    'g4dn.12xlarge': {'vcpus': 48, 'memory': 190000, 'num_gpu': 4},

    # P3 Instance
    'p3.2xlarge': {'vcpus': 8, 'memory': 59000, 'num_gpu': 1},
    'p3.8xlarge': {'vcpus': 32, 'memory': 240000, 'num_gpu': 4},
    'p3.16xlarge': {'vcpus': 64, 'memory': 485000, 'num_gpu': 8},
    'p3.24xlarge': {'vcpus': 96, 'memory': 768000, 'num_gpu': 8},

    # C4 Instance
    'c4.2xlarge': {'vcpus': 8, 'memory': 13000, 'num_gpu': 0},
    'c4.4xlarge': {'vcpus': 16, 'memory': 28000, 'num_gpu': 0},
    'c4.8xlarge': {'vcpus': 36, 'memory': 130000, 'num_gpu': 0},

    # C5 Instance
    'c5.2xlarge': {'vcpus': 8, 'memory': 14000, 'num_gpu': 0},
    'c5.4xlarge': {'vcpus': 16, 'memory': 30000, 'num_gpu': 0},
    'c5.9xlarge': {'vcpus': 36, 'memory': 70000, 'num_gpu': 0},
    'c5.12xlarge': {'vcpus': 48, 'memory': 94000, 'num_gpu': 0},
    'c5.18xlarge': {'vcpus': 72, 'memory': 142000, 'num_gpu': 0},
    'c5.24xlarge': {'vcpus': 96, 'memory': 190000, 'num_gpu': 0},
}


def generate_job_definition():
    config = dict()
    name = 'gluon-nlp-g4-12dn'
    config['jobDefinitionName'] = name
    config['type'] = 'container'
    config['containerProperties'] = {
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
        "privileged": True
        # Issue: https://forums.aws.amazon.com/thread.jspa?messageID=953912
        # "linuxParameters": {
        #     'sharedMemorySize': 2000
        # }
    }
    return config


client = boto3.client('batch', region_name='us-east-1')
response = client.register_job_definition(**generate_job_definition())
print(response)
if response['HTTPStatusCode'] == 200:
    job_name = response['jobDefinitionName']
    revision = response['revision']
else:
    raise RuntimeError("Fail to register the job definition")
