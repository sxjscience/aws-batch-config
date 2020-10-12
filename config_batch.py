import boto3
import logging
import pandas as pd

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
    'p3.24xlarge': {'vcpus': 96, 'memory': 766000, 'num_gpu': 8},

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


def generate_job_definition(instance_type):
    instance_info = instance_info_mapping[instance_type]
    is_gpu = instance_info['num_gpu'] > 0
    device_type = 'gpu' if is_gpu else 'cpu'
    image_tag = 'gluon-nlp-1:gpu-ci-latest' if is_gpu else 'gluon-nlp-1:cpu-ci-latest'
    image_base = '747303060528.dkr.ecr.us-east-1.amazonaws.com'
    config = dict()
    config['jobDefinitionName'] = f'gluon-nlp-{instance_type}'
    config['type'] = 'container'
    config['containerProperties'] = {
        'image': image_base + '/' + image_tag,
        'vcpus': instance_info['vcpus'],
        'memory': instance_info['memory'],
        'command': ["./gluon_nlp_job.sh",
                    "Ref::SOURCE_REF",
                    "Ref::WORK_DIR",
                    "Ref::COMMAND",
                    "Ref::SAVED_OUTPUT",
                    "Ref::SAVE_PATH",
                    "Ref::REMOTE",
                    device_type],
        "resourceRequirements": [
            {
                "type": "GPU",
                "value": str(instance_info['num_gpu'])
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
job_definition_info = []
for instance_type in instance_info_mapping.keys():
    response = client.register_job_definition(**generate_job_definition(instance_type))
    print(response)
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        job_name = response['jobDefinitionName']
        revision = response['revision']
        job_definition_info.append((instance_type, job_name, revision))
    else:
        raise RuntimeError("Fail to register the job definition")
df = pd.DataFrame(job_definition_info, columns=['Instance Type', 'Name', 'Revision'])
df.to_csv('gluon-nlp-job-definitions.csv')
