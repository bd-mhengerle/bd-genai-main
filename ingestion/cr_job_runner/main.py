import json

from google.cloud import run_v2
from google.cloud.run_v2 import JobsClient 
from google.cloud.run_v2.types import RunJobRequest, Job, GetJobRequest

import functions_framework
from flask.wrappers import Request 


JOB_MAPPER = {
    'gh-service': 'projects/bd-genai-internal/locations/us-central1/jobs/gh-service',
}

def _main(
    job_name: str,
    args: list[str],
    jobs_client: JobsClient
):
    container_overrides = {
        'container_overrides': [
            {
                'args': args
            }
        ]
    }
    run_req = RunJobRequest(name=JOB_MAPPER[job_name], overrides=container_overrides)
    result = jobs_client.run_job(run_req)
    return result
    

def main(request: Request):
    data = json.loads(request.data.decode('utf-8'))

    client = JobsClient()

    job_name = data['job_name']
    args = data['args']

    _main(
        job_name=job_name,
        args=args,
        jobs_client=client
    )

    return 'OK'


if __name__ == '__main__':
    
    # example invocation
    JOB_NAME = 'gh-service'
    ARGS = ['convert.py', '--repo_url', 'https://github.com/boston-dynamics/spot-sdk', '--bucket', 'bd-gh-data-spot-sdk']

    jobs_client = JobsClient()
    _main(JOB_NAME, ARGS, jobs_client)