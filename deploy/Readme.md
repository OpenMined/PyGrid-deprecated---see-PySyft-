1. `cd` to this directory.
2. Run `terraform init`.
3. Create an AWS account.
4. Login to AWS console. Go to `My Security Credentials` and create a new pair of `Access keys`.
5. `cd ~ && mkdir .aws`.
6. `touch ~/.aws/credentials` to create a file named `credentials` inside `~/.aws`.
7. Copy and paste your credentials from AWS console into `~/.aws/credentials`
    > aws_access_key_id=AKIAIOSFODNN7EXAMPLE
    > aws_secret_access_key=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
7. cd to this directory and run `terraform apply`.
8. To use a different region other than the default one use `terraform apply -var 'region=<region-name>'`. Example `terraform apply -var 'region=us-east-1'`.
9. Upon successful creation of resources, above command will output an ip address to the hosted apache server.
10. To terminate the resources run `terraform destroy` in this directory.