echo "------------------"
echo "MongoDB Setup"
echo "------------------"


NAME="mymongodb"
PORT="27017"

docker pull mongo
docker run -d -p 27017:$PORT --name $NAME mongo
docker ps

#docker exec -it mymongodb mongo
#https://medium.com/@analyticscodeexplained/seamless-development-a-step-by-step-guide-to-installing-mongodb-with-docker-20eb6649b8dc
