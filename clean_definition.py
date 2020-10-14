import boto3

client = boto3.client('batch', region_name='us-east-1')

def deregister_old_revision():
    response = client.describe_job_definitions(status='ACTIVE')['jobDefinitions']
    jobDefinitionMapping = {}
    for res in response:
        jobDefinitionName, jobRevision = res['jobDefinitionName'], res['revision']
        if jobDefinitionName in jobDefinitionMapping:
            jobDefinitionMapping[jobDefinitionName].append(jobRevision)
        else:
            jobDefinitionMapping[jobDefinitionName] = [jobRevision]
    for jobDefinition in jobDefinitionMapping:
        revisions = jobDefinitionMapping[jobDefinition]
        revisions.sort()
        for oldRevision in revisions[:-1]: # The last one is the newest revision
            response = client.deregister_job_definition(jobDefinition=f'{jobDefinition}:{oldRevision}') 
            print(response)
            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                print(f'Successfully deregistered {jobDefinition}:{oldRevision}')
            else:
                raise RuntimeError(f'Fail to deregister {jobDefinition}:{oldRevision}')
    print("Job definition has been cleaned")

deregister_old_revision()
