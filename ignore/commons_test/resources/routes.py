from application.resources.contexts import *
from flask import Blueprint, request, jsonify

dummy_bp = Blueprint('dbresource', __name__, url_prefix='/resources')


@dummy_bp.post('/<username>/<wname>/')
@dummy_bp.post('/<username>/<wname>')
def add_new_resource(username, wname):
    resource_ctx = UserWorkspaceResourceContext(
        username, wname,
        region='eu_south_1', country='Italy'
    )
    data = request.get_json()
    ctp: MongoResourceConfig = t.cast(ReferrableDataType, DataType.get_type(data['type'])).config_type()
    resource_doc = ctp.create(data, resource_ctx)
    return jsonify({'message': f"Successfully created resource of type {data['type']}!"})


@dummy_bp.get('/<username>/<wname>/<typename>/<name>/')
@dummy_bp.get('/<username>/<wname>/<typename>/<name>')
def build_resource(username, wname, typename, name):
    """
    :param username:
    :param wname:
    :param typename:
    :param name:
    :return:
    """
    resource_ctx = UserWorkspaceResourceContext(
        username, wname,
        region='eu_south_1', country='Italy'
    )
    ctp: t.Type[MongoResourceConfig] = t.cast(ReferrableDataType, DataType.get_type(typename)).config_type()
    uri = ctp.dfl_uri_builder(resource_ctx, name)
    resource_doc = ctp.get_by_uri(uri)
    resource = resource_doc.build(resource_ctx)
    if resource is not None:
        return jsonify({"message": f"Successfully built resource '{name}'."})
    else:
        raise RuntimeError(f"Failed to build resource '{name}'.")


@dummy_bp.delete('/<username>/<wname>/<typename>/<name>/')
@dummy_bp.delete('/<username>/<wname>/<typename>/<name>')
def delete_resource(username, wname, typename, name):
    """
    :param username:
    :param wname:
    :param typename:
    :param name:
    :return:
    """
    resource_ctx = UserWorkspaceResourceContext(
        username, wname,
        region='eu_south_1', country='Italy'
    )
    ctp: MongoResourceConfig = t.cast(ReferrableDataType, DataType.get_type(typename)).config_type()
    uri = ctp.dfl_uri_builder(resource_ctx, name)
    resource_doc = ctp.get_by_uri(uri)
    resource_doc.delete(resource_ctx)
    return jsonify({"message": f"Successfully deleted resource '{name}'."})