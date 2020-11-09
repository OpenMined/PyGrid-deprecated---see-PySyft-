base_setup = f'''
#!/bin/bash

## For debugging
# redirect stdout/stderr to a file
exec &> log.out


echo "Simple Web Server for testing the deployment"
sudo apt update -y
sudo apt install apache2 -y
sudo systemctl start apache2
echo """
<h1 style='color:#f09764; text-align:center'>
    OpenMined First Server Deployed via Terraform
</h1>
""" | sudo tee /var/www/html/index.html

echo "Setup Miniconda environment"

sudo wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
sudo bash miniconda.sh -b -p miniconda
sudo rm miniconda.sh
export PATH=/miniconda/bin:$PATH > ~/.bashrc
conda init bash
source ~/.bashrc
conda create -y -n pygrid python=3.7
conda activate pygrid

echo "Install poetry..."
pip install poetry

echo "Install GCC"
sudo apt-get install python3-dev -y
sudo apt-get install libevent-dev -y
sudo apt-get install gcc -y

echo "Cloning PyGrid"
git clone https://github.com/OpenMined/PyGrid

'''


aws_lambda_vpc_execution_role_policy = """{
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                        "ec2:CreateNetworkInterface",
                        "ec2:DescribeNetworkInterfaces",
                        "ec2:DeleteNetworkInterface"
                    ],
                    "Resource": "*"
                }
            ]
        }"""


cloud_watch_logs_full_access_policy = """{
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": [
                        "logs:*"
                    ],
                    "Effect": "Allow",
                    "Resource": "*"
                }
            ]
        }
        """


amazon_rds_data_full_access_policy = """{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "SecretsManagerDbCredentialsAccess",
                "Effect": "Allow",
                "Action": [
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:PutResourcePolicy",
                    "secretsmanager:PutSecretValue",
                    "secretsmanager:DeleteSecret",
                    "secretsmanager:DescribeSecret",
                    "secretsmanager:TagResource"
                ],
                "Resource": "*"
            },
            {
                "Sid": "RDSDataServiceAccess",
                "Effect": "Allow",
                "Action": [
                    "dbqms:CreateFavoriteQuery",
                    "dbqms:DescribeFavoriteQueries",
                    "dbqms:UpdateFavoriteQuery",
                    "dbqms:DeleteFavoriteQueries",
                    "dbqms:GetQueryString",
                    "dbqms:CreateQueryHistory",
                    "dbqms:DescribeQueryHistory",
                    "dbqms:UpdateQueryHistory",
                    "dbqms:DeleteQueryHistory",
                    "rds-data:ExecuteSql",
                    "rds-data:ExecuteStatement",
                    "rds-data:BatchExecuteStatement",
                    "rds-data:BeginTransaction",
                    "rds-data:CommitTransaction",
                    "rds-data:RollbackTransaction",
                    "secretsmanager:CreateSecret",
                    "secretsmanager:ListSecrets",
                    "secretsmanager:GetRandomPassword",
                    "tag:GetResources"
                ],
                "Resource": "*"
            }
        ]
     }
     """
