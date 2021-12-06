""""""
"""
   Copyright (c) 2021 Olivier Sprangers as part of Airlab Amsterdam

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.


"""
#%% Import packages
import torch
import torch.optim as optim
import numpy as np
from joblib import Parallel, delayed
from lib.utils import fix_seed, instantiate_model, count_parameters, read_table, get_emb
from lib.train import loop
from data.datasets import timeseries_dataset
import pandas as pd
import time
import datetime
torch.backends.cudnn.benchmark = False
num_cores = 2
torch.set_num_threads(2)
#%% Initialize parameters for datasets
datasets = ['uci_electricity','uci_traffic','kaggle_favorita','kaggle_webtraffic']
dim_inputseqlens = [168, 168, 90, 90]
dim_outputseqlens = [24, 24, 28, 30]
dim_maxseqlens = [500, 500, 150, 150]
#%% Initiate experiment
dataset_id = 0
cuda = 0
seed = 0
fix_seed(seed)
num_samples_train = 500000
scaling = True
epochs = 5
#%% Load data
dataset_name = datasets[dataset_id]
experiment_dir = 'experiments/'+dataset_name
dim_inputseqlen = dim_inputseqlens[dataset_id] # Input sequence length
dim_outputseqlen = dim_outputseqlens[dataset_id]  # Output prediction length
dim_maxseqlen = dim_maxseqlens[dataset_id]
# Import data
dset = timeseries_dataset(dataset_name, dim_inputseqlen, dim_outputseqlen, dim_maxseqlen)
training_set = dset.load('train')
# Initialize sample sets
id_samples_train = torch.randperm(len(training_set))[:num_samples_train]
#%% Algorithm parameters
file_experiments = experiment_dir + f'/experiments_{dataset_name}.csv'
table = read_table(file_experiments)
d_emb = get_emb(dataset_name)
t_epochs = np.zeros((epochs))

for idx in range(len(table)):
    # Read experiment table, set hyperparameters
    algorithm = table.loc[idx, 'algorithm']
    learning_rate = table.loc[idx, 'learning_rate']
    batch_size = int(table.loc[idx, 'batch_size'])
    d_hidden = int(table.loc[idx, 'd_hidden'])
    # Following paper of TransformerConv, hidden dimension is defined by covariates, lags and embedding dims
    if algorithm == 'transformer_conv':
        d_hidden = training_set.d_cov + training_set.d_lag + d_emb[:, 1].sum()
    kernel_size = int(table.loc[idx, 'kernel_size'])
    N = int(table.loc[idx, 'N'])
    dropout = table.loc[idx, 'dropout']
    seed = table.loc[idx, 'seed']
    params = eval(table.loc[idx, 'params_train'])
    # Training loop
    if 'model' in locals(): del model
    model = instantiate_model(algorithm)(*params)
    filename = f'{experiment_dir}/{algorithm}/{algorithm}_seed={seed}_hidden={d_hidden}_lr={learning_rate}_bs={batch_size}'
    checkpoint = torch.load(filename)
    model.load_state_dict(checkpoint['model_state_dict'])
    no_params = count_parameters(model)
    print(f'{algorithm}: {no_params}')