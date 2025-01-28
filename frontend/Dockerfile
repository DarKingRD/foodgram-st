# build env
FROM node:21.7.1-alpine
WORKDIR /app
COPY package*.json ./

RUN npm i
COPY . ./
RUN npm run build
CMD cp -r build result_build
