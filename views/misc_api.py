from flask import Blueprint, request, Response, jsonify
from utils import init_dpapi, exceptions
from utils.response_utils import success_response, handle_error
from config.secrets import gitlab_private_token, gitlab_project_id
import gitlab

misc_api = Blueprint('misc_api', __name__)
misc_api.register_error_handler(exceptions.ApiError, handle_error)

@misc_api.route("/api/misc/uploadfile", methods=['post'])
def upload_file_to_gitlab_repo():
    try:
        filename = request.headers.get("filename")
        if filename:
            gl = gitlab.Gitlab('https://gitlab.com', private_token=gitlab_private_token)
            gl.auth()
            schemas_project = gl.projects.get(gitlab_project_id)
            branch_name = "uploading_" + filename
            branch = schemas_project.branches.create({'branch': branch_name, 'ref': 'master'})
            data = request.get_data()
            print(data)
            commit_data = {
                'branch': branch_name,
                'commit_message': 'uploading ' + filename,
                'actions': [
                    {
                        'action': 'create',
                        'file_path': filename,
                        'content': data
                    }
                ]
            }
            commit = schemas_project.commits.create(commit_data)
            mr = schemas_project.mergerequests.create({'source_branch': branch_name, 'target_branch': 'master', 'title': 'Merging {} to master'.format(branch_name)})
            mr.merge()
            return success_response("File uploaded successfully")
        return (jsonify({"message": "no filename header was provided"}), 400)
    except Exception as e:
        return (jsonify(e.response_body), e.response_code)

