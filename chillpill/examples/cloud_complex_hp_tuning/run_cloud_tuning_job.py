"""This module runs a distributed hyperparameter tuning job on Google Cloud AI Platform."""
import subprocess
from pathlib import Path
import time

import numpy as np

from chillpill import params
from chillpill import search
from chillpill.examples.cloud_complex_hp_tuning import train

if __name__ == '__main__':
    GCLOUD_PROJECT_NAME = 'kb-experiment'
    CONTAINER_IMAGE_URI = f'gcr.io/{GCLOUD_PROJECT_NAME}/chillpill:cloud_hp_tuning_example'
    GCLOUD_BUCKET_NAME = 'kb-bucket'

    # Create a Cloud AI Platform Hyperparameter Search object
    search = search.HyperparamSearchSpec(
        max_trials=10,
        max_parallel_trials=5,
        max_failed_trials=2,
        hyperparameter_metric_tag='val_acc',
    )

    # Add parameter search ranges for this problem.
    my_param_ranges = train.MyParams(
        activation=params.Categorical(['relu', 'tanh']),
        num_layers=params.Integer(min_value=1, max_value=3),
        num_neurons=params.Discrete(np.logspace(2, 8, num=7, base=2)),
        dropout_rate=params.Double(min_value=-0.1, max_value=0.9),
        learning_rate=params.Discrete(np.logspace(-6, 2, 17, base=10)),
        batch_size=params.Integer(min_value=1, max_value=128),
    )
    search.add_parameters(my_param_ranges)

    this_dir = Path(__file__).resolve().parent

    # Dump search spec and parameter ranges to a yaml file.
    search.to_training_input_yaml(this_dir / 'hps.yaml')

    # Call a bash script to build a docker image for this repo, submit it to the docker registry defined in the script
    # and run a training job on the Cloud AI Platform using this container and these hyperparameter ranges.
    subprocess.call([this_dir / 'build_submit.sh'])

    search.run_job(
        job_name=f'sample_cmle_job_{str(int(time.time()))}',
        gcloud_project_name=GCLOUD_PROJECT_NAME,
        container_image_uri=CONTAINER_IMAGE_URI,
        static_args={'bucket_id': GCLOUD_BUCKET_NAME},
    )
