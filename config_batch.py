import boto3
import logging
import pandas as pd
import argparse

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
required = parser.add_argument_group('required arguments')
required.add_argument('--project', help='choose the project you want to config', type=str,
                    choices=['gluon-nlp', 'gluon-cv'], required=True)
args = parser.parse_args()
project = args.project

client = boto3.client('batch', region_name='us-east-1')

instance_info_mapping = {
    # P2 Instance
    'p2.xlarge': {'vcpus': 4, 'memory': 50000, 'num_gpu': 1},
    'p2.8xlarge': {'vcpus': 32, 'memory': 450000, 'num_gpu': 8},
    'p2.16xlarge': {'vcpus': 64, 'memory': 700000, 'num_gpu': 16},

    # G4 Instance
    'g4dn.xlarge': {'vcpus': 4, 'memory': 13000, 'num_gpu': 1},
    'g4dn.2xlarge': {'vcpus': 8, 'memory': 27000, 'num_gpu': 1},
    'g4dn.4xlarge': {'vcpus': 16, 'memory': 55000, 'num_gpu': 1},
    'g4dn.8xlarge': {'vcpus': 32, 'memory': 118000, 'num_gpu': 1},
    'g4dn.12xlarge': {'vcpus': 48, 'memory': 180000, 'num_gpu': 4},

    # P3 Instance
    'p3.2xlarge': {'vcpus': 8, 'memory': 55000, 'num_gpu': 1},
    'p3.8xlarge': {'vcpus': 32, 'memory': 220000, 'num_gpu': 4},
    'p3.16xlarge': {'vcpus': 64, 'memory': 450000, 'num_gpu': 8},
    'p3.24xlarge': {'vcpus': 96, 'memory': 700000, 'num_gpu': 8},

    # C4 Instance
    'c4.2xlarge': {'vcpus': 8, 'memory': 12000, 'num_gpu': 0},
    'c4.4xlarge': {'vcpus': 16, 'memory': 25000, 'num_gpu': 0},
    'c4.8xlarge': {'vcpus': 36, 'memory': 50000, 'num_gpu': 0},

    # C5 Instance
    'c5.2xlarge': {'vcpus': 8, 'memory': 13000, 'num_gpu': 0},
    'c5.4xlarge': {'vcpus': 16, 'memory': 25000, 'num_gpu': 0},
    'c5.9xlarge': {'vcpus': 36, 'memory': 62000, 'num_gpu': 0},
    'c5.12xlarge': {'vcpus': 48, 'memory': 86000, 'num_gpu': 0},
    'c5.18xlarge': {'vcpus': 72, 'memory': 124000, 'num_gpu': 0},
    'c5.24xlarge': {'vcpus': 96, 'memory': 170000, 'num_gpu': 0},
}

image_tag_mapping = {
    'gluon-nlp-gpu': 'gluon-nlp-1:gpu-ci-latest',
    'gluon-nlp-cpu': 'gluon-nlp-1:cpu-ci-latest',
    'gluon-cv-gpu': 'gluon-cv-1:latest',
    'gluon-cv-cpu': 'gluon-cv-1:cpu-latest',
}

image_base_mapping = {
    'gluon-nlp': '747303060528.dkr.ecr.us-east-1.amazonaws.com',
    'gluon-cv': '985964311364.dkr.ecr.us-east-1.amazonaws.com'
}


def generate_job_definition(instance_type):
    instance_info = instance_info_mapping[instance_type]
    is_gpu = instance_info['num_gpu'] > 0
    device_type = 'gpu' if is_gpu else 'cpu'
    image_tag = image_tag_mapping[f'{project}-gpu'] if is_gpu else image_tag_mapping[f'{project}-cpu']
    image_base = image_base_mapping[f'{project}']
    resource_requirements = [{
        "type": "GPU",
        "value": str(instance_info['num_gpu'])
    }] if is_gpu else []
    config = dict()
    config['jobDefinitionName'] = f'{project}-{instance_type}'.replace('.', '_')
    config['type'] = 'container'
    if project == 'gluon-nlp':
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
        'jobRoleArn': 'arn:aws:iam::747303060528:role/ECSContainerPowerUser',
        "resourceRequirements": resource_requirements,
        "privileged": True
        # Issue: https://forums.aws.amazon.com/thread.jspa?messageID=953912
        # "linuxParameters": {
        #     'sharedMemorySize': 2000
        # }
    }
    elif project == 'gluon-cv':
        config['containerProperties'] = {
        'image': image_base + '/' + image_tag,
        'vcpus': instance_info['vcpus'],
        'memory': instance_info['memory'],
        'command': ["./gluon_cv_job.sh",
                    "Ref::SOURCE_REF",
                    "Ref::WORK_DIR",
                    "Ref::COMMAND",
                    "Ref::SAVED_OUTPUT",
                    "Ref::SAVE_PATH",
                    "Ref::REMOTE",
                    device_type],
        "resourceRequirements": resource_requirements,
        "privileged": True
        # Issue: https://forums.aws.amazon.com/thread.jspa?messageID=953912
        # "linuxParameters": {
        #     'sharedMemorySize': 2000
        # }
    }
    return config

def deregister_old_revision(job_name, revision):
    old_definitions = client.describe_job_definitions(jobDefinitionName=job_name, status='ACTIVE')['jobDefinitions']
    for od in old_definitions:
        if od['revision'] < revision:
            rp = client.deregister_job_definition(jobDefinition=f'{job_name}:{od}')
            if rp['ResponseMetadata']['HTTPStatusCode'] == 200:
                print(f'Deregistered {job_name}:{od}')
            else:
                print(f'Failed to deregister {job_name}:{od}')

job_definition_info = []
for instance_type in instance_info_mapping.keys():
    response = client.register_job_definition(**generate_job_definition(instance_type))
    print(response)
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        job_name = response['jobDefinitionName']
        revision = response['revision']
        job_definition_info.append((instance_type, job_name, revision))
        deregister_old_revision(job_name, revision)
    else:
        raise RuntimeError("Fail to register the job definition")
df = pd.DataFrame(job_definition_info, columns=['Instance Type', 'Name', 'Revision'])
df.to_csv(f'{project}-job-definitions.csv')
