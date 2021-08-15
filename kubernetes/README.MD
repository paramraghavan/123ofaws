Kubernetes aka k8s
----------------------------

VM-Ware vs Docker
-------------------
-------------------
![image](https://user-images.githubusercontent.com/52529498/129439177-542d37b7-75b9-4823-a276-9df80b56ccd7.png)

- If your applications runs on k8s,  then it can run on cloud or for that matter any flavor of cloud or off cloud - meaning on-premise with no changes to code.
Basically decouples application from underlying cloud. k8s is kind of a *conductor* of a container orchestra
- https://kubernetes.io/docs/concepts/overview/components


K8s
----------------------

# Kubernetes Clusters
Kubernetes coordinates a highly available cluster of computers that are connected to work as a single unit. The abstractions in Kubernetes allow you to deploy containerized applications to a cluster without tying them specifically to individual machines. To make use of this new model of deployment, applications need to be packaged in a way that decouples them from individual hosts: they need to be containerized. Containerized applications are more flexible and available than in past deployment models, where applications were installed directly onto specific machines as packages deeply integrated into the host. Kubernetes automates the distribution and scheduling of application containers across a cluster in a more efficient way. Kubernetes is an open-source platform and is production-ready.

A Kubernetes cluster consists of two types of resources:

The Control Plane coordinates the cluster
Nodes are the workers that run applications
Summary:
Kubernetes cluster
Minikube
Kubernetes is a production-grade, open-source platform that orchestrates the placement (scheduling) and execution of application containers within and across computer clusters.


# Cluster Diagram

![image](https://user-images.githubusercontent.com/52529498/129478836-6ed6c799-dfdd-4d3a-8460-72f2e93f0b63.png)


- The Control Plane is responsible for managing the cluster. The Control Plane coordinates all activities in your cluster, such as scheduling applications, maintaining applications' desired state, scaling applications, and rolling out new updates.

- A node is a VM or a physical computer that serves as a worker machine in a Kubernetes cluster. Each node has a Kubelet, which is an agent for managing the node and communicating with the Kubernetes control plane. The node should also have tools for handling container operations, such as containerd or Docker. A Kubernetes cluster that handles production traffic should have a minimum of three nodes.

Control Planes manage the cluster and the nodes that are used to host the running applications.

When you deploy applications on Kubernetes, you tell the control plane to start the application containers. The control plane schedules the containers to run on the cluster's nodes. The nodes communicate with the control plane using the Kubernetes API, which the control plane exposes. End users can also use the Kubernetes API directly to interact with the cluster.

A Kubernetes cluster can be deployed on either physical or virtual machines. To get started with Kubernetes development, you can use Minikube. Minikube is a lightweight Kubernetes implementation that creates a VM on your local machine and deploys a simple cluster containing only one node. Minikube is available for Linux, macOS, and Windows systems. The Minikube CLI provides basic bootstrapping operations for working with your cluster, including start, stop, status, and delete. For this tutorial, however, you'll use a provided online terminal with Minikube pre-installed.

Now that you know what Kubernetes is, let's go to the online tutorial and start our first cluster!

**ref**: https://kubernetes.io/docs/tutorials/kubernetes-basics/create-cluster/cluster-intro/

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
