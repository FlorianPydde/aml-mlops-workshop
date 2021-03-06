# Defines a tabular dataset on top of an Azure ML datastore
from azureml.core import Workspace, Datastore, Dataset
from datetime import date
from azureml.core.authentication import AzureCliAuthentication
from azureml.core import Run
from azureml.exceptions._azureml_exception import UserErrorException

run = Run.get_context()

startWeek = 19  # put here the current week for the first time
weekNumber = (date.today().isocalendar()[1]+7)

# Retrieve a datastore from a ML workspace
try:
    ws = Workspace.from_config(auth=AzureCliAuthentication())
except UserErrorException:
    ws = run.experiment.workspace

datastore_name = 'workspaceblobstore'
datastore = Datastore.get(ws, datastore_name)
# Register dataset and sebset version for each data split
for data_split in ['train', 'test']:
    for set in ['', 'subset_']:
        # Create a TabularDataset from paths in datastore in split folder
        datastore_paths = []
        for i in range(startWeek, (weekNumber+1)):
            datastore_path = (
                datastore,
                '{}/*.csv'.format('raw_' + set + data_split + '/' + str(i))
             )
            datastore_paths.insert(0, datastore_path)
        # Create a File from paths in datastore
        dataset = Dataset.File.from_files(
            path=datastore_paths
        )

        # Register the defined dataset for later use
        dataset.register(
            workspace=ws,
            name=('newsgroups_''raw_' + set + data_split),
            description='newsgroups data',
            create_new_version=True
        )
