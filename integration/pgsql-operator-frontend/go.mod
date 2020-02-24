module github.com/jiphex/kpgfrontend

go 1.13

replace github.com/jiphex/kpgthing => /Users/jameshannah/src/shefhack/kpgthing

require (
	github.com/go-logr/logr v0.1.0
	github.com/go-logr/zapr v0.1.0
	github.com/jiphex/kpgthing v0.0.0-00010101000000-000000000000
	github.com/mgutz/logxi v0.0.0-20161027140823-aebf8a7d67ab
	github.com/onsi/ginkgo v1.8.0
	github.com/onsi/gomega v1.5.0
	go.uber.org/zap v1.9.1
	k8s.io/api v0.0.0-20190918155943-95b840bb6a1f
	k8s.io/apimachinery v0.0.0-20190913080033-27d36303b655
	k8s.io/client-go v0.0.0-20190918160344-1fbdaa4c8d90
	sigs.k8s.io/controller-runtime v0.4.0
)
