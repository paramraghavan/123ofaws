Kubernetes aka k8s
----------------------------

VM-Ware vs Docker
-------------------
-------------------
![image](https://user-images.githubusercontent.com/52529498/129439177-542d37b7-75b9-4823-a276-9df80b56ccd7.png)

- If your applications runs on k8s,  then it can run on cloud or for that matter any flavor of cloud or off cloud - meaning on-premise with no changes to code.
Basically decouples out app from underlying cloud. k8s is kind of a *conductor* of a container orchestra
- https://kubernetes.io/docs/concepts/overview/components


# Minikube install
- https://github.com/kubernetes/minikube
- [mimi cube install](https://minikube.sigs.k8s.io/docs/start/)  
- [Install aand start minikube](https://minikube.sigs.k8s.io/docs/start/
<pre>
start docker application
run --> minikube start --driver=docker
minikube kubectl -- get po -A
minikube status
    type: Control Plane
    host: Running
    kubelet: Running -> runs on the worker node
    apiserver: Running
    kubeconfig: Configured

minikube pause
minikube unpause
minikube delete --all
minikube start --driver=docker

ref:
https://github.com/kubernetes/minikube/issues/9040
https://minikube.sigs.k8s.io/docs/drivers/docker/
</pre>


# coding begins deploy code on minikube
- [serverless-and-kubernetes-via-kubeless](https://www.serverless.com/blog/serverless-and-kubernetes-via-kubeless)



Notes:
- https://kubeless.io/
- https://github.com/kubernetes/minikube 
- [mimi cube install](https://minikube.sigs.k8s.io/docs/start/)  
- https://github.com/kubeless/kubeless/blob/master/README.md
