package main

import (
	"io"
	"net/http"
	"os"
)

func check(rw http.ResponseWriter, req *http.Request) {
	_, err := os.Stat("/tmp/done")
	if err != nil {
		rw.WriteHeader(500)
	} else {
		x, _ := os.Open("/tmp/done")
		io.Copy(rw, x)
		x.Close()
	}
}

func main() {
	http.HandleFunc("/", check)
	http.ListenAndServe(":5000", nil)
}
