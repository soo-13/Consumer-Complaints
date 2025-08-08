#!/bin/bash
#SBATCH -p mit_normal_gpu
#SBATCH -n 1 # number of tasks
#SBATCH -t 6:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=5
#SBATCH --mem=44G
#SBATCH -e /home/yeonsoo/consumer_complaints/build/temp/narrative_classification/error_narr.txt
#SBATCH -o /home/yeonsoo/consumer_complaints/build/temp/narrative_classification/output_narr.txt

export CUDA_LAUNCH_BLOCKING=1 

module load cuda/12.4.0
module load cudnn/9.8.0.87-cuda12
module load deprecated-modules
module load anaconda3/2022.05-x86_64
echo "all modules loaded"

path="/home/yeonsoo/consumer_complaints/build"
ENV_NAME=llama_env

source $(conda info --base)/etc/profile.d/conda.sh

#conda deactivate
#conda remove --name $ENV_NAME --all -y

if conda info --envs | grep -q "$ENV_NAME"; then
    echo "Activating existing conda env: $ENV_NAME"
    conda activate $ENV_NAME
else
    echo "Creating new conda env: $ENV_NAME with python 3.10"
    conda create -n $ENV_NAME python=3.10 numpy pandas -y
    conda activate $ENV_NAME
    conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia -y
    pip install transformers==4.43.2 tqdm numpy pandas accelerate scikit-learn
fi

which python
pip show transformers

python $path/code/narrative_classification.py 


  