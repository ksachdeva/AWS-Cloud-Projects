import argparse
import mimetypes
import subprocess
from pathlib import Path

import boto3
from jinja2 import Environment, FileSystemLoader


def _update_aws_exports(
    project_region: str,
    user_pool_id: str,
    user_pool_web_client_id: str,
):
    env = Environment(loader=FileSystemLoader("configs"))
    template = env.get_template("aws-exports.ts.j2")
    context = {
        "aws_project_region": project_region,
        "aws_cognito_region": project_region,
        "aws_user_pools_id": user_pool_id,
        "aws_user_pools_web_client_id": user_pool_web_client_id,
    }
    rendered_code = template.render(context)

    Path.write_text(
        Path("../code/frontend/src/configs/aws-exports.ts"),
        rendered_code,
    )


def _update_config_tsx(
    api_url: str,
):
    env = Environment(loader=FileSystemLoader("./configs"))
    template = env.get_template("config.tsx.j2")
    context = {"api_url": api_url}
    rendered_code = template.render(context)

    Path.write_text(
        Path("../code/frontend/src/configs/configs.tsx"),
        rendered_code,
    )


def _build_frontend():
    subprocess.run(["npm", "install"], cwd="../code/frontend", check=True)
    subprocess.run(["npm", "run", "build"], cwd="../code/frontend", check=True)


def _upload_files_to_s3(bucket_name: str):

    def _get_extra_args(file_name: str):
        if file_name.endswith("html"):
            return {"ContentType": "text/html"}

        if file_name.endswith("css"):
            return {"ContentType": "text/css"}

        if file_name.endswith("js"):
            return {"ContentType": "text/javascript"}

        if file_name.endswith("png"):
            return {"ContentType": "image/png"}

        if file_name.endswith("jpeg") or file_name.endswith("jpg"):
            return {"ContentType": "image/jpeg"}

    # expecting the credentials to be set in the environment
    s3 = boto3.client("s3")

    # below is specific to this application
    # normally one should write a generic function to upload files
    # with automatic discovery of files & folders to upload

    for p in Path("../code/frontend/dist").glob("*"):
        if p.is_file():
            m_type, _ = mimetypes.guess_type(p)
            print("Uploading ", p, " with mimetype - ", m_type)
            s3.upload_file(
                str(p),
                bucket_name,
                p.name,
                ExtraArgs={"ContentType": m_type},
            )

    for p in Path("../code/frontend/dist/assets").glob("*"):
        if p.is_file():
            m_type, _ = mimetypes.guess_type(p)
            print("Uploading ", p, " with mimetype - ", m_type)
            s3.upload_file(
                str(p),
                bucket_name,
                f"assets/{p.name}",
                ExtraArgs={"ContentType": m_type},
            )


def main(args):
    _update_aws_exports(
        project_region=args.project_region,
        user_pool_id=args.user_pool_id,
        user_pool_web_client_id=args.user_pool_web_client_id,
    )

    _update_config_tsx(
        api_url=args.api_url,
    )

    _build_frontend()

    _upload_files_to_s3(args.bucket_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--user-pool-id", required=True)
    parser.add_argument("--user-pool-web-client-id", required=True)
    parser.add_argument("--project-region", required=True)
    parser.add_argument("--api-url", required=True)
    parser.add_argument("--bucket-name", required=True)

    args = parser.parse_args()
    main(args)
