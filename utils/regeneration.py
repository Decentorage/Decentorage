import yaml
import os
import app
from argo.workflows.client import ( ApiClient,
									WorkflowServiceApi,
									Configuration,
									V1alpha1WorkflowCreateRequest)
import requests

def start_regeneration_job(file_id, seg_no, test=False):
	seg_no = int(seg_no)
	host = os.environ["ARGO_URI"]
	if not test:
		database = app.database
		if not database:
			print("database error")
			return
		files = database["files"]
		print(file_id,seg_no)
		query = {"_id": file_id}
		file = files.find_one(query)
		if not file:
			print("No file exist.")
			return
		segment = file["segments"][seg_no]
		regeneration_count = segment["regeneration_count"]
	else:
		regeneration_count = 23
	config = Configuration(host=host)
	client = ApiClient(configuration=config)
	service = WorkflowServiceApi(api_client=client)
	with open("regeneration-workflow.yaml") as f:
			manifest: dict = yaml.safe_load(f)
	manifest["metadata"]["name"]= str(file_id).lower() + "decentorage" + str(seg_no) + "decentorage" + str(regeneration_count)
	manifest["spec"]["templates"][0]["inputs"]["parameters"][0]["value"] = str(file_id)
	manifest["spec"]["templates"][0]["inputs"]["parameters"][1]["value"] = str(seg_no)
	try:
		service.create_workflow('argo', V1alpha1WorkflowCreateRequest(workflow=manifest))
	except Exception as e:
		print(e)
		return
	return
