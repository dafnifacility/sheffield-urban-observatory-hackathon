FROM golang:1 AS build
COPY main.go main.go
RUN go build -o /siggy ./main.go
FROM gcr.io/distroless/base
COPY --from=build /siggy /siggy
ENTRYPOINT ["/siggy"]
