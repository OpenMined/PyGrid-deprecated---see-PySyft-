heroku create $GRID_NAME
heroku addons:create rediscloud
git commit -am "init"
git push heroku master