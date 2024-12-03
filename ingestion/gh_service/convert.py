from pathlib import Path
import time 
import shutil
import subprocess
from datetime import datetime

import git 
from google.cloud import storage

import constants as c 
from log import get_logger, CloudLogger

logger: CloudLogger = get_logger(c.LOGGER_NAME, c.PROJECT)

def clone_repo(repo_url: str, clone_dir: Path):
    return git.Repo.clone_from(repo_url, clone_dir)

def clean_directory(dir_path: Path):

    if not dir_path.exists():
        create_empty_directory(dir_path)
        return

    for item in dir_path.iterdir():
        if item.is_file() or item.is_symlink():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)
 
    timeout = 0
    while any(dir_path.iterdir()):
        timeout += 1
        if timeout > 10:
            raise Exception('Failed to clean directory')
        time.sleep(1)

def create_empty_directory(dir_path: Path):
    if dir_path.exists():
        shutil.rmtree(dir_path)
    dir_path.mkdir(parents=True, exist_ok=True)

    timeout = 0
    while not dir_path.exists():
        timeout += 1
        if timeout > 10:
            raise Exception('Failed to create directory')
        time.sleep(1)

def remove_html(dir_path: Path):
    for item in dir_path.iterdir():
        if item.is_file() and item.suffix == '.html':
            item.unlink()

def convert_to_pdf(
    input_path: Path,
) -> Path | None:
        output_path = Path('output/' + '/'.join(input_path.parts[1:])).with_suffix('.pdf')
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
        try:
            result = subprocess.run(
                ['gh-md-to-html', f'{str(input_path)}', '-p', f'{str(output_path)}'],
                check=True,
                capture_output=True
            )
            return output_path

        except Exception as e:
            raise Exception(f'Failed to convert {input_path} to PDF: {e}')

def get_object_metadata(
    gcs_client: storage.Client,
    bucket_name: str,
    object_prefix: str
) -> dict | None:
    bucket = gcs_client.get_bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=object_prefix)
    for blob in blobs:
        return blob.metadata
    return None
    
def get_repo_metadata(
    repo: git.Repo
) -> dict:
    
    repo.git.checkout('master')
    all_files = [item.path for item in repo.tree().traverse()]
    md_files = [file for file in all_files if file.endswith('.md')]

    metadata = {}
    for fpath in md_files:
        commits = list(repo.iter_commits(rev='master', paths=fpath, max_count=1))
        latest_commit = commits[0]
        metadata[fpath] = {
            'latest_commit': latest_commit.hexsha,
            'latest_commit_ts': datetime.fromtimestamp(latest_commit.committed_date)
        }
        
    return metadata
        
def get_gcs_metadata(
    gcs_client: storage.Client,
    bucket_name: str 
):
    bucket = gcs_client.get_bucket(bucket_name)
    blobs = bucket.list_blobs(prefix='pdf')
    metadata = {}
    for blob in blobs:
        blob.reload()
        fname = '/'.join(blob.name.split('/')[1:])
        metadata[fname] = blob.metadata or {}
    return metadata

def compare_metadata(
    repo_meta: dict,
    gcs_meta: dict
):
    directives = {}
    for fpath, meta in repo_meta.items():
        
        fpath_pdf = fpath.replace('.md', '.pdf')

        if fpath_pdf not in gcs_meta:
            directives[fpath] = 'convert'
        elif any([
            k not in gcs_meta[fpath_pdf].keys()
            for k in ['latest_commit', 'latest_commit_ts']
        ]):
            directives[fpath] = 'convert'
        else:
            latest_commit_ts_str = gcs_meta[fpath_pdf]['latest_commit_ts']
            latest_commit_ts = datetime.strptime(latest_commit_ts_str, '%Y-%m-%d %H:%M:%S')
            if meta['latest_commit_ts'] > latest_commit_ts:
                directives[fpath] = 'convert'
    
    for fpath in gcs_meta.keys():
        fpath_md = fpath.replace('.pdf', '.md')
        if fpath_md not in repo_meta:
            directives[fpath] = 'delete'

    return directives

def write_to_gcs(
    gcs_client: storage.Client,
    bucket: str,
    pdf_path: Path,
    metadata: dict
):
    bucket = gcs_client.get_bucket(bucket)
    prefix = 'pdf/' + '/'.join(pdf_path.parts[1:])
    blob = bucket.blob(prefix)
    if blob.exists():
        blob.reload()
    blob.metadata = metadata
    blob.upload_from_filename(pdf_path)
    return blob

def remove_from_gcs(
    gcs_client: storage.Client,
    bucket: str,
    pdf_path: Path
):
    bucket = gcs_client.get_bucket(bucket)
    prefix = 'pdf/' + '/'.join(pdf_path.parts)
    blob = bucket.blob(prefix)
    blob.delete()
    return blob
    
    
def main(
        repo_url: str,
        target_bucket: str
):
    logger.info(
        f'Received request for repo: `{repo_url}` and target bucket: `{target_bucket}`'
    )

    gcs = storage.Client(project=c.PROJECT)

    create_empty_directory(c.CLONE_DIR)
    logger.info(f'Cloning repo: `{repo_url}`')
    repo = clone_repo(repo_url, c.CLONE_DIR)
    
    repo_meta = get_repo_metadata(repo=repo)
    gcs_meta = get_gcs_metadata(
        gcs_client=gcs,
        bucket_name=target_bucket
    )
    directives = compare_metadata(repo_meta, gcs_meta)
    logger.log_struct(
        'Conversion directives',
        directives=directives
    )

    clean_directory(c.OUTPUT_DIR)
    for fpath, directive in directives.items():
        remove_html(Path('/app'))
        clean_directory(Path('images')) 
        if directive == 'convert':
            logger.info(f'Converting: `{fpath}`')
            input_path = c.CLONE_DIR / fpath
            try:
                output_path = convert_to_pdf(input_path)
            except Exception as e:
                logger.warning(f'Failed to convert `{fpath}`: {e}')
                output_path = None
            if output_path:
                write_to_gcs(
                    gcs_client=gcs,
                    bucket=target_bucket,
                    pdf_path=output_path,
                    metadata=repo_meta[fpath]
                )
        else:
            logger.info(f'Deleting: `{fpath}`')
            remove_from_gcs(
                gcs_client=gcs,
                bucket=target_bucket,
                pdf_path=Path(fpath)
            )



if __name__ == '__main__':
    from argparse import ArgumentParser
    import traceback

    parser = ArgumentParser()
    parser.add_argument('--repo_url', type=str, required=True)
    parser.add_argument('--bucket', type=str, required=True)
    args = parser.parse_args()

    repo_url = args.repo_url
    bucket = args.bucket
    logger.set_label('repo_url', repo_url)
    logger.set_label('bucket', bucket)

    try:
        main(repo_url, bucket)
    except Exception as e:
        logger.log_struct(
            message=f'Failed to process repo: {e}',
            severity='ERROR',
            traceback=traceback.format_exc()
        )





