# quick fastapi package 

[fastapi specifications](https://pypi.org/project/fastapi/)

pip install "fastapi[all]" --break-system-packages  (incase python is installed via homebrew)
lsof -i :8000 (show the process using the port)
kill -9 <pid>

docker build -t your_image_name .
docker stop <container_id>
docker rm <container_id>

start: docker run -d -p 80:80 your_image_name
to use local file in image: docker run -d -p 8000:8000 -v $(pwd):/code your_image_name
login to docker:  docker login  <container_registry_server_name> -u  <container_user_name> -p <pwd>
docker build with build tag:docker build -t ragcontainter.azurecr.io/<container_name>:<build-tag-Oct302024> . 

run app local: 
1. source .venv/bin/activate
2. uvicorn app.main:app --port 8001 (default port is 8000)
3. http://localhost:8000 