# Modeling
This folder contains scripts for modeling. This folder contains three files: a training script for training the model, a training submit script to submit the training to Azure Machine Learning and a script for model scoring, that we need when we deploy the model

*  `train.py`

    In this file we will do the model training. This file is set up to do 3 types of model trainig. In the parameters on the top of the script, we can change the types of models that we are training, as well as the data that we want to use for training. In this example we will see how we can easily switch from local to remote datasets and compute as well as switch between types of datasets, as we might want to train a heavy model in the experimentation phase only on a subsample of the data.

    In this file you can find models for:

    * random forest

        If we set the parameter of `--models` to `randomforest`, we train script will fit a random forest from sklearn over the data. We will log different metrics and plots to Azure Machine Learning inlcuding the confusion matrix, AUC curve and accuracy metrics. The output in Azure Machine learning will look similair to this. (Note that I am using old experience of the studio here as in my opion this give a better overview of my runs).
        ![An example of Random Forest](images/attributesrandomforest.PNG)
        ![An example of Random Forest](images/metricsrandomforest.PNG)

        We can caputure the results from our run and log the result to Azure Machine Learning. This way we can keep track of the performance of our models while we are experimenting with different models, parameters, data transformations or feature selections. We can specify for ourselfves what is important to track and log number, graphs and tables to Azure ML, including confusion matrices from SKlearn. For a full overview check the [avaiable metrics to track](https://docs.microsoft.com/en-us/azure/machine-learning/how-to-track-experiments#available-metrics-to-track)

        For a full example on how to run a random forest on Azure Machine Learning and how to log metrics, follow the labs [HERE]

        
    * 15 different sklearn models

        If we set the parameters of `--models` to `sklearnmodels`, we will train 15 different models from the sklearn packages, including randomforeser, naive bayes and Ridge classifier. A full overview of the models being trained, can be founs in the `class Model_choice` on the `sklearn.py` package under `packages`. Comparing different algorithms is possible is different ways. We could submit a new experiment for every algorithm that we try. However, Azure ML offers a better, easier way to manage the exploration of multiple models. This concept is called child runs.  We are going to make use of these child runs. The expiriment will perform a parent run that is going to execute `explore/code/train_15models.py`. Within this file we are going to create child runs. For every of the 15 algoritms that we have we want to create a sub run and log the metrics seprately. Whihin the child run we are going to log the performane and the model .pkl files. This way we can easily track and compare our experiment in Azure ML. If we run this file, the output will look like the following:
        ![An example of tracking accuracy across multiple models](images/manymodels.PNG)
        (Note that in this case I am using the new experience, as I believe the new experience is better in tracking child run metrics.)

        For a full example on how to run a multiple model on Azure Machine Learning and how to log metrics and create child runs follow the labs [HERE]

    * Deep Learning

        In this pat we are going to build a Deep Neural Network using Pytorch. If we set the parameters of `--models` to `deeplearning`, we will train this network. The output will look like this:

        ![An example of tracking accuracy across multiple models](images/deeplearning.PNG)

*   `train_submit.py`

    This file we use to submit the train script to Azure Machine Learning. This file is created to sumbit different jobs of the training script. At the top of the file, the following paramters we can set to perform training on Azure ML:

    ```python
    # Define comfigs
    # allowed arguments are: randomforest, sklearn, deeplearning
    # randomforest will perform 1 run of randomforest fit
    # sklearnmodels will fit 15 models from sklearn
    # deeplearning will fit a neural network with pytorch
    models = 'sklearnmodels'
    data_local = True
    # if data_local is true, subset is alwats true
    subset = True
    # hyperdrive only works with deeplearning   
    hyperdrive = False
    ```

    Note here the comments. f the set the  `data_local` parameter to `True`, then we need to net the `subset` parameter also to true, because we only have our subset data locally. If you have your full data also available locally, you can of course set this variable to `False`. Nor that we also have a parameter for `hyperdrive`. 

* `score.py`

    The `score.py` file we use when deploying our trained model. The scoring file consist of 3 steps: preprocessing, scoring and postporcoessing.
