sudo yum update -y && sudo yum install -y gcc openssl-devel bzip2-devel libffi-devel zlib-devel make wget
sudo yum install sqlite-devel
wget https://www.python.org/ftp/python/3.13.0/Python-3.13.0.tgz
tar xzf Python-3.13.0.tgz
cd Python-3.13.0
./configure --enable-optimizations --enable-loadable-sqlite-extensions
make -j $(nproc)
sudo make altinstall

python -m venv ~/.agents
source ~/.agents/bin/activate
# deactivate