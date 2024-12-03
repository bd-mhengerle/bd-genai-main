# build environment
FROM node:21 as builder
WORKDIR /app
COPY . .
RUN npm install && npm run build

# server environment
FROM nginx:alpine
WORKDIR /usr/share/nginx/html
RUN rm -rf ./*
COPY --from=builder /app/build .
WORKDIR /etc/nginx/conf.d
RUN rm default.conf
COPY nginx.conf /etc/nginx/conf.d/configfile.template
WORKDIR /usr/share/nginx/html
ENV PORT 8080
ENV HOST 0.0.0.0
EXPOSE 8080
RUN pwd

# Start Server
CMD sh -c "envsubst '\$PORT' < /etc/nginx/conf.d/configfile.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"



