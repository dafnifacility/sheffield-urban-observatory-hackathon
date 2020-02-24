/*

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package controllers

import (
	"context"
	"encoding/json"
	"fmt"
	"math/rand"
	"time"

	"github.com/go-logr/logr"
	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/util/intstr"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"

	sheffieldv1alpha1 "github.com/jiphex/kpgthing/api/v1alpha1"
)

// DatabaseReconciler reconciles a Database object
type DatabaseReconciler struct {
	client.Client
	Log    logr.Logger
	Scheme *runtime.Scheme

	Clock
}

// +kubebuilder:rbac:groups=sheffield.dafni.ac.uk,resources=databases,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=sheffield.dafni.ac.uk,resources=databases/status,verbs=get;update;patch
var (
	jobOwnerKey = ".metadata.controller"
	apiGVStr    = sheffieldv1alpha1.GroupVersion.String()
)

func (r *DatabaseReconciler) Reconcile(req ctrl.Request) (ctrl.Result, error) {
	ctx := context.Background()
	log := r.Log.WithValues("database", req.NamespacedName)
	res := ctrl.Result{}

	var db sheffieldv1alpha1.Database
	if err := r.Get(ctx, req.NamespacedName, &db); err != nil {
		if client.IgnoreNotFound(err) != nil {
			log.Error(err, "unable to fetch uodatabase")
		}
		// we'll ignore not-found errors, since they can't be fixed by an immediate
		// requeue (we'll need to wait for a new notification), and we can get them
		// on deleted requests.
		return ctrl.Result{}, client.IgnoreNotFound(err)
	}

	var deps appsv1.DeploymentList
	if err := r.List(ctx, &deps, client.InNamespace(req.Namespace), client.MatchingFields{jobOwnerKey: req.Name}); err != nil {
		log.Error(err, "unable to list child Jobs")
		return ctrl.Result{}, err
	}
	log.V(10).Info("listed deployments", "count", len(deps.Items))

	if len(deps.Items) == 0 {
		cmname, err := r.createConfigMap(ctx, log, &db)
		if err != nil {
			log.Error(err, "unable to create configmap")
			return ctrl.Result{}, err
		}
		err = r.createService(ctx, log, &db, cmname)
		if err != nil {
			log.Error(err, "unable to create svc")
			return ctrl.Result{}, err
		}
		if err := r.createDeploymentForDatabase(ctx, log, &db, cmname); err != nil {
			log.Error(err, "unable to create database")
			return ctrl.Result{}, err
		}
		log.Info("successfully created database deployment")
		db.Status.State = "DEPLOYING"
		res.RequeueAfter = 30 * time.Second
	} else {
		log.V(8).Info("found existing database deployment")
		dep := deps.Items[0]
		if dep.Status.AvailableReplicas == 0 {
			db.Status.State = "LOADING"
			res.RequeueAfter = 10 * time.Second
		} else {
			if db.Spec.ConnectionString == "" {
				// need to get the loadbalancer details then update the db
				var svcs corev1.ServiceList
				if err := r.List(ctx, &svcs, client.InNamespace(req.Namespace), client.MatchingFields{jobOwnerKey: req.Name}); err != nil {
					log.Error(err, "unable to list services")
					return ctrl.Result{}, err
				}
				if len(svcs.Items) == 0 {
					err := fmt.Errorf("no matching services")
					log.Error(err, "cant find services")
					return ctrl.Result{}, err
				}
				svc := svcs.Items[0]
				var xh string
				if len(svc.Status.LoadBalancer.Ingress) > 0 {
					xh = svc.Status.LoadBalancer.Ingress[0].Hostname
					if xh == "" {
						xh = svc.Status.LoadBalancer.Ingress[0].IP
					}
					db.Spec.ConnectionString = fmt.Sprintf("host=%s port=%d dbname=postgres user=postgres password=postgres", xh, svc.Spec.Ports[0].Port)
					err := r.Update(ctx, &db)
					if err != nil {
						log.Error(err, "unable to update database with connection string", "connStr", db.Spec.ConnectionString)
						return ctrl.Result{}, err
					}
					db.Status.State = "FINISHED"
				} else {
					log.Info("no external ingress yet")
					res.RequeueAfter = 10 * time.Second
					db.Status.State = "LBWAIT"
				}
			} else {
				log.Info("no reconcile needed")
			}
		}
	}
	if err := r.Status().Update(ctx, &db); err != nil {
		log.Error(err, "unable to update status")
		return ctrl.Result{}, err
	}
	return res, nil

}

func (r *DatabaseReconciler) createConfigMap(ctx context.Context, log logr.Logger, db *sheffieldv1alpha1.Database) (string, error) {
	cmLabels := map[string]string{
		"app":      "uo-postgresql",
		"instance": db.Name,
	}
	xmdata := make(map[string]interface{})
	xmdata["params"] = db.Spec
	xmdata["url"] = "http://dataserver.default.svc.cluster.local:5000/data"
	xmdata["table"] = "sensor_data"
	xmdata["dsn"] = "host=localhost dbname=postgres user=postgres port=5432"
	dbcmj, _ := json.Marshal(xmdata)
	newcm := corev1.ConfigMap{
		ObjectMeta: metav1.ObjectMeta{
			GenerateName: fmt.Sprintf("%s-database-", db.Name),
			Namespace:    db.Namespace,
			Labels:       cmLabels,
			Annotations:  make(map[string]string),
		},
		Data: map[string]string{
			"params.json": string(dbcmj),
		},
	}
	if err := ctrl.SetControllerReference(db, &newcm, r.Scheme); err != nil {
		return "", err
	}
	if err := r.Create(ctx, &newcm); err != nil {
		return "", err
	}
	log.Info("created database", "name", newcm.Name)
	return newcm.Name, nil
}

func (r *DatabaseReconciler) createService(ctx context.Context, log logr.Logger, db *sheffieldv1alpha1.Database, name string) error {
	svLabels := map[string]string{
		"app":      "uo-postgresql",
		"instance": db.Name,
	}
	newsvc := corev1.Service{
		ObjectMeta: metav1.ObjectMeta{
			Name:        name,
			Namespace:   db.Namespace,
			Labels:      svLabels,
			Annotations: make(map[string]string),
		},
		Spec: corev1.ServiceSpec{
			Ports: []corev1.ServicePort{
				corev1.ServicePort{
					Port:       rand.Int31n(1000) + 31000,
					TargetPort: intstr.FromInt(5432),
				},
			},
			Type:     "LoadBalancer",
			Selector: svLabels,
		},
	}
	if err := ctrl.SetControllerReference(db, &newsvc, r.Scheme); err != nil {
		return err
	}
	if err := r.Create(ctx, &newsvc); err != nil {
		return err
	}
	log.Info("created svc", "name", newsvc.Name)
	return nil
}

func (r *DatabaseReconciler) createDeploymentForDatabase(ctx context.Context, log logr.Logger, db *sheffieldv1alpha1.Database, name string) error {
	depLabels := map[string]string{
		"app":      "uo-postgresql",
		"instance": db.Name,
	}
	pfalse := false
	// assume not found
	newdep := appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:        name,
			Namespace:   db.Namespace,
			Labels:      depLabels,
			Annotations: make(map[string]string),
		},
		Spec: appsv1.DeploymentSpec{
			Selector: &metav1.LabelSelector{
				MatchLabels: depLabels,
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: depLabels,
				},
				Spec: corev1.PodSpec{
					Volumes: []corev1.Volume{
						corev1.Volume{
							Name: "config",
							VolumeSource: corev1.VolumeSource{
								ConfigMap: &corev1.ConfigMapVolumeSource{
									LocalObjectReference: corev1.LocalObjectReference{
										Name: name,
									},
									Optional: &pfalse,
								},
							},
						},
						corev1.Volume{
							Name: "signal",
							VolumeSource: corev1.VolumeSource{
								EmptyDir: &corev1.EmptyDirVolumeSource{},
							},
						},
						corev1.Volume{
							Name: "pgsock",
							VolumeSource: corev1.VolumeSource{
								EmptyDir: &corev1.EmptyDirVolumeSource{},
							},
						},
					},
					Containers: []corev1.Container{
						corev1.Container{
							Name:  "loader",
							Image: "jiphex/shefdb:latest",
							VolumeMounts: []corev1.VolumeMount{
								corev1.VolumeMount{
									Name:      "config",
									MountPath: "/etc/uo",
									ReadOnly:  true,
								},
								corev1.VolumeMount{
									Name:      "signal",
									MountPath: "/tmp",
									ReadOnly:  false,
								},
								corev1.VolumeMount{
									Name:      "pgsock",
									MountPath: "/run/postgresql",
									ReadOnly:  false,
								},
							},
							Args: []string{"loader"},
						},
						corev1.Container{
							Name:  "pg",
							Image: "mdillon/postgis",
							VolumeMounts: []corev1.VolumeMount{
								corev1.VolumeMount{
									Name:      "config",
									MountPath: "/docker-entrypoint-initdb.d",
									ReadOnly:  true,
								},
								corev1.VolumeMount{
									Name:      "signal",
									MountPath: "/tmp",
									ReadOnly:  true,
								},
								corev1.VolumeMount{
									Name:      "pgsock",
									MountPath: "/run/postgresql",
									ReadOnly:  false,
								},
							},
							ReadinessProbe: &corev1.Probe{
								Handler: corev1.Handler{
									TCPSocket: &corev1.TCPSocketAction{
										Port: intstr.FromInt(5432),
									},
								},
							},
						},
						corev1.Container{
							Name:  "siggy",
							Image: "jiphex/siggy",
							ReadinessProbe: &corev1.Probe{
								Handler: corev1.Handler{
									HTTPGet: &corev1.HTTPGetAction{
										Port: intstr.FromInt(5000),
									},
								},
								InitialDelaySeconds: 20,
								FailureThreshold:    7,
								// basically it gets 90 seconds I think
							},
							VolumeMounts: []corev1.VolumeMount{
								corev1.VolumeMount{
									Name:      "signal",
									MountPath: "/tmp",
									ReadOnly:  true,
								},
							},
						},
					},
				},
			},
		},
	}
	if err := ctrl.SetControllerReference(db, &newdep, r.Scheme); err != nil {
		return err
	}
	if err := r.Create(ctx, &newdep); err != nil {
		return err
	}
	log.Info("created database", "name", newdep.Name)
	return nil
}

type realClock struct{}

func (_ realClock) Now() time.Time { return time.Now() }

// clock knows how to get the current time.
// It can be used to fake out timing for testing.
type Clock interface {
	Now() time.Time
}

func (r *DatabaseReconciler) SetupWithManager(mgr ctrl.Manager) error {
	// set up a real clock, since we're not in a test
	if r.Clock == nil {
		r.Clock = realClock{}
	}
	rand.Seed(r.Clock.Now().UnixNano())
	if err := mgr.GetFieldIndexer().IndexField(&appsv1.Deployment{}, jobOwnerKey, func(rawObj runtime.Object) []string {
		// grab the job object, extract the owner...
		job := rawObj.(*appsv1.Deployment)
		owner := metav1.GetControllerOf(job)
		if owner == nil {
			return nil
		}
		// ...make sure it's a CronJob...
		if owner.APIVersion != apiGVStr || owner.Kind != "Database" {
			return nil
		}

		// ...and if so, return it
		return []string{owner.Name}
	}); err != nil {
		return err
	}
	if err := mgr.GetFieldIndexer().IndexField(&corev1.Service{}, jobOwnerKey, func(rawObj runtime.Object) []string {
		// grab the job object, extract the owner...
		job := rawObj.(*corev1.Service)
		owner := metav1.GetControllerOf(job)
		if owner == nil {
			return nil
		}
		// ...make sure it's a CronJob...
		if owner.APIVersion != apiGVStr || owner.Kind != "Database" {
			return nil
		}

		// ...and if so, return it
		return []string{owner.Name}
	}); err != nil {
		return err
	}
	return ctrl.NewControllerManagedBy(mgr).
		For(&sheffieldv1alpha1.Database{}).
		Complete(r)
}
