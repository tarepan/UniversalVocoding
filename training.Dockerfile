# CUDA support status: [my blog](https://tarepan.hatenablog.com/entry/2020/10/24/035916)
# Python==3.8.3 (checked by myself in Docker container)
# FROM pytorch/pytorch:1.7.0-cuda11.0-cudnn8-runtime

# Python==3.7.7 (checked by myself in Docker container)
FROM pytorch/pytorch:1.6.0-cuda10.1-cudnn7-runtime

# For pip install through git
RUN apt-get update && apt-get install -y git

RUN pip install git+https://github.com/tarepan/UniversalVocoding

# For Torch==1.6.0
RUN pip uninstall -y torchaudio
RUN pip install torchaudio==0.6.0

# For TorchAudio
RUN apt-get install -y libsndfile1
# RUN pip install SoundFile

ENTRYPOINT ["python", "-m", "rnnms.main_train"]
# use `CMD` override for arguments.
#   c.f. [Understand how CMD and ENTRYPOINT interact](https://docs.docker.com/engine/reference/builder/#understand-how-cmd-and-entrypoint-interact)