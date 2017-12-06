#!bin/bash
zip package.zip check_trans.py
zip -r package.zip yahoo_creds.pkl config.yml
cd ./AWS_Lambda/lib/python2.7/site-packages/
zip -r ../../../../package.zip *