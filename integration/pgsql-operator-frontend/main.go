package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os/exec"
	"strings"
	"time"

	"github.com/go-logr/logr"
	"github.com/go-logr/zapr"
	"go.uber.org/zap"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/dynamic"
	"k8s.io/client-go/kubernetes"

	sheffieldv1alpha1 "github.com/jiphex/kpgthing/api/v1alpha1"
)

var log logr.Logger

type DBRequest struct {
	Params      []string
	From, Until time.Time
}

func makeResource(ctx context.Context, req DBRequest) error {
	db := &sheffieldv1alpha1.Database{
		TypeMeta: metav1.TypeMeta{
			Kind:       "Database",
			APIVersion: "sheffield.dafni.ac.uk/v1alpha1",
		},
		ObjectMeta: metav1.ObjectMeta{
			GenerateName: "uo-database-",
			Namespace:    "shef",
		},
		Spec: sheffieldv1alpha1.DatabaseSpec{
			DataTypes: req.Params,
			Period: sheffieldv1alpha1.DatabasePeriodSpec{
				From: metav1.Time{
					Time: req.From,
				},
				Until: metav1.Time{
					Time: req.Until,
				},
			},
		},
	}
	jdb, _ := json.Marshal(db)
	cc := exec.CommandContext(ctx, "/usr/local/bin/kubectl", "create", "-f", "-")
	cc.Stdin = bytes.NewReader(jdb)
	o, err := cc.CombinedOutput()
	log.Info(string(o))
	return err
}

func getParams(src *http.Request) []string {
	ss := bufio.NewScanner(strings.NewReader(src.FormValue("params")))
	l := make([]string, 0)
	for ss.Scan() {
		t := ss.Text()
		if len(t) > 0 {
			l = append(l, t)
		}
	}
	if ss.Err() != nil {
		return []string{}
	}
	return l
}

func doCreate(rw http.ResponseWriter, req *http.Request) {
	params := getParams(req)
	sfrom := req.FormValue("from")
	if sfrom == "" {
		sfrom = "2015-01-01"
	}
	from, _ := time.Parse("2006-01-02", sfrom)
	suntil := req.FormValue("until")
	if suntil == "" {
		suntil = "2020-02-12"
	}
	until, _ := time.Parse("2006-01-02", suntil)
	log.Info("got request",
		"params", params,
		"from", from,
		"until", until,
	)
	err := makeResource(req.Context(), DBRequest{
		Params: params,
		From:   from,
		Until:  until,
	})
	if err != nil {
		log.Error(err, "cant create")
		rw.WriteHeader(500)
		fmt.Fprintf(rw, err.Error())
	} else {
		rw.Header().Add("Location", "/list")
		rw.WriteHeader(302)
		fmt.Fprintf(rw, "Created")
	}
}

func doList(rw http.ResponseWriter, req *http.Request) {
	rw.Header().Add("Refresh", "5")
	kb := exec.CommandContext(req.Context(), "/usr/local/bin/kubectl", "-n", "shef", "get", "databases", "-o", "json")
	out, err := kb.Output()
	if err != nil {
		rw.WriteHeader(500)
		log.Error(err, "kubectl fail")
		fmt.Fprintf(rw, err.Error())
	}
	// jd := json.NewDecoder(kb.Stdout)
	// var l sheffieldv1alpha1.DatabaseList
	// jd.Decode(&l)
	// jl := l.Encode()
	// nb, err := io.Copy(rw, out)
	nb, err := rw.Write(out)
	if err != nil {
		log.Error(err, "unable to copy list out")
	} else {
		log.Info("wrote out", "bytes", nb)
	}
}

const (
	httpListen = "[::]:3333"
)

var clientset *kubernetes.Clientset
var xd dynamic.Interface

func main() {
	zapLog, err := zap.NewDevelopment()
	if err != nil {
		panic(err)
	}
	log = zapr.NewLogger(zapLog)

	http.HandleFunc("/create", doCreate)
	http.HandleFunc("/list", doList)
	http.Handle("/", http.FileServer(http.Dir("./static")))
	log.Info("about to listen", "listenInterface", httpListen)
	http.ListenAndServe(httpListen, nil)
}
