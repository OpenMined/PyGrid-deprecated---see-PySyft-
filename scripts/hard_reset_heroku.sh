cd app;
heroku apps:destroy --confirm $GRID_NAME
sh ../scripts/launch_heroku_app.sh
cd ../
