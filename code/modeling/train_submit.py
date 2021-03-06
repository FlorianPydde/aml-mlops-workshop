"""
Training submitter

Facilitates (remote) training execution through the Azure ML service.
"""
import os
from azureml.core import Workspace, Experiment, ScriptRunConfig
from azureml.train.estimator import Estimator
from azureml.core.authentication import AzureCliAuthentication
from azureml.core.dataset import Dataset
from azureml.core.runconfig import RunConfiguration, MpiConfiguration
from azureml.train.hyperdrive.parameter_expressions import uniform, choice
from azureml.train.hyperdrive import (
    BayesianParameterSampling,
    HyperDriveConfig,
    PrimaryMetricGoal
)
from azureml.train.dnn import PyTorch

# Define comfigs
# allowed arguments are: randomforest, sklearn, deeplearning
# randomforest will perform 1 run of randomforest fit
# sklearnmodels will fit 15 models from sklearn
# deeplearning will fit a neural network with pytorch
models = 'randomforest'
data_local = False
# if data_local is true, subset is alwats true
subset = False
# hyperdrive only works with deeplearning
hyperdrive = False


# If deep learning define hyperparameters
# Set parameters for search
param_sampling = BayesianParameterSampling({
    "learning_rate": uniform(0.05, 0.1),
    "num_epochs": choice(5, 10, 15),
    "batch_size": choice(150, 200),
    "hidden_size": choice(50, 100)
})

# load Azure ML workspace
workspace = Workspace.from_config(auth=AzureCliAuthentication())

if subset is True:
    # define data set names
    input_name_train = 'newsgroups_subset_train'
    input_name_test = 'newsgroups_subset_test'
    filepath = "environments/sklearn_subset/RunConfig/runconfig_subset.yml"
else:
    input_name_train = 'newsgroups_train'
    input_name_test = 'newsgroups_test'
    filepath = "environments/sklearn_full/RunConfig/runconfig_full.yml"


if models != 'deeplearning':
    if data_local is True:
        # define script parameters
        script_params = {
            '--models': models,
            '--data_folder_train':
            os.path.join(os.path.join(
                    os.path.dirname(os.path.realpath(__file__)),
                    "../..",
                    "outputs/prepared_data/subset_train.csv",
                    )),
            '--data_folder_test':
            os.path.join(os.path.join(
                    os.path.dirname(os.path.realpath(__file__)),
                    "../..",
                    "outputs/prepared_data/subset_test.csv",
                    ))
            }

        # Define Run Configuration
        est = Estimator(
            entry_script='train.py',
            script_params=script_params,
            source_directory=os.path.dirname(os.path.realpath(__file__)),
            compute_target='local',
            user_managed=True,
            use_docker=False
        )

    if data_local is False:
        dataset_train = Dataset.get_by_name(
            workspace,
            name=input_name_train
        )
        dataset_test = Dataset.get_by_name(
            workspace,
            name=input_name_test
        )

        # Load run Config
        run_config = RunConfiguration.load(
            path=os.path.join(os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                "../..",
                filepath,
                )),
            name="sklearn"
        )

        est = ScriptRunConfig(
            source_directory=os.path.dirname(os.path.realpath(__file__)),
            arguments=[
                "--models", models,
                '--data_folder_train',
                'DatasetConsumptionConfig:{}'.format(input_name_train),
                '--data_folder_test',
                'DatasetConsumptionConfig:{}'.format(input_name_test),
                '--local', 'no'
            ],
            run_config=run_config
        )

    # Define the ML experiment
    experiment = Experiment(workspace, "explore_" + models)
    # Submit experiment run, if compute is idle, this may take some time')
    run = experiment.submit(est)

if models == 'deeplearning':
    dataset_train = Dataset.get_by_name(workspace, name=input_name_train)
    dataset_test = Dataset.get_by_name(workspace, name=input_name_test)

    # define script parameters
    script_params_3 = {
        '--models': models,
        '--data_folder_train':
        dataset_train.as_named_input('train').as_mount(),
        '--data_folder_test':
        dataset_test.as_named_input('test').as_mount(),
        '--local': 'no'
        }

    estimator = PyTorch(
        entry_script='train.py',
        script_params=script_params_3,
        source_directory=os.path.dirname(os.path.realpath(__file__)),
        compute_target=workspace.compute_targets["alwaysoncluster"],
        distributed_training=MpiConfiguration(),
        framework_version='1.4',
        use_gpu=True,
        pip_packages=[
            'numpy==1.15.4',
            'pandas==0.23.4',
            'scikit-learn==0.20.1',
            'scipy==1.0.0',
            'matplotlib==3.0.2',
            'utils==0.9.0',
            'onnxruntime==1.2.0',
            'onnx==1.6.0'
            ]
    )

    experiment = Experiment(workspace=workspace, name="deeplearning")
    run = experiment.submit(estimator)

    if hyperdrive is True:
        # Define multi-run configuration
        hyperdrive_run_config = HyperDriveConfig(
            estimator=estimator,
            hyperparameter_sampling=param_sampling,
            policy=None,
            primary_metric_name="accuracy",
            primary_metric_goal=PrimaryMetricGoal.MAXIMIZE,
            max_total_runs=10,
            max_concurrent_runs=None
        )

        # Define the ML experiment
        experiment = Experiment(workspace=workspace, name="hyperdrive")
        # Submit the experiment
        run = experiment.submit(hyperdrive_run_config)
