Kubernetes aka k8s
----------------------------

VM-Ware vs Docker
-------------------
-------------------
![image](https://user-images.githubusercontent.com/52529498/129439177-542d37b7-75b9-4823-a276-9df80b56ccd7.png)

- If your applications runs on k8s,  then it can run on cloud or for that matter any flavor of cloud or off cloud - meaning on-premise with no changes to your code.
Basically decouples application from underlying cloud. k8s is kind of a *conductor* of a container orchestra
- https://kubernetes.io/docs/concepts/overview/components


K8s
----------------------

# Kubernetes Clusters
Kubernetes coordinates a highly available cluster of computers that are connected to work as a single unit. The abstractions in Kubernetes allow you to deploy containerized applications to a cluster without tying them specifically to individual machines. To make use of this new model of deployment, applications need to be packaged in a way that decouples them from individual hosts: they need to be containerized.**Containerized** applications are more flexible and available than in past deployment models, where applications were installed directly onto specific machines as packages deeply integrated into the host. Kubernetes automates the distribution and scheduling of application containers across a cluster in a more efficient way. 

- A Kubernetes cluster consists of two types of resources:
    - The Control Plane coordinates the cluster
    - Nodes/worker nodes are the workers that run applications

# Cluster Diagram
![image](https://user-images.githubusercontent.com/52529498/129478836-6ed6c799-dfdd-4d3a-8460-72f2e93f0b63.png)

# Control Plane Image
![image](https://user-images.githubusercontent.com/52529498/129500383-8515dacf-a0e5-4ff6-8b6b-90819acfdd2f.png)
<!--![image](https://user-images.githubusercontent.com/52529498/129479478-976b1da1-38f6-4a55-a16a-ee3bd9c30e82.png)-->
- **The Control Plane** is responsible for managing the cluster. The Control Plane coordinates all activities in your cluster, such as scheduling applications(Scheduler), maintaining applications' desired state(Cluster store), scaling applications, and rolling out new updates (Controller) and apiserver to interface with Nodes

# Node Image
![image](https://user-images.githubusercontent.com/52529498/129479774-e5a4b480-70cf-4a17-982a-9455f20f1d4b.png)

- **A node also called pod**, a single POD could runmore than one container.  Nodes can be linux or windows and serves as a worker machine in a Kubernetes cluster. Each node has a Kubelet, which is an agent for managing the node and communicating with the Kubernetes control plane. The node should also have tools for handling container operations, such as containerd or Docker. A Kubernetes cluster that handles production traffic should have a minimum of three nodes. So there's basically three components that we care about:
  - kubelet,
  - the container runtime
  - the kube proxy. 

- Control Planes manage the cluster and the nodes that are used to host the running applications.

When you deploy applications on Kubernetes, you tell the control plane to start the application containers. The control plane schedules the containers to run on the cluster's nodes. The nodes communicate with the control plane using the Kubernetes API, which the control plane exposes. End users can also use the Kubernetes API directly to interact with the cluster.

A Kubernetes cluster can be deployed on either physical or virtual machines. To get started with Kubernetes development, you can use Minikube. Minikube is a lightweight Kubernetes implementation that creates a VM on your local machine and deploys a simple cluster containing only one node. Minikube is available for Linux, macOS, and Windows systems. The Minikube CLI provides basic bootstrapping operations for working with your cluster, including start, stop, status, and delete. For this tutorial, however, you'll use a provided online terminal with Minikube pre-installed.

# Amazon EKS 
Amazon EKS is a managed service that makes it easy for you to use Kubernetes on AWS without needing to install 
and operate your own Kubernetes control plane. Amazon EKS exposes a Kubernetes API endpoint. Your existing 
Kubernetes tooling can connect directly to EKS managed control plane. Worker nodes run as EC2 instances in 
your account. Ref: https://console.aws.amazon.com/eks/home?region=us-east-1#


**ref**: https://kubernetes.io/docs/tutorials/kubernetes-basics/create-cluster/cluster-intro/

# Minikube install
- https://github.com/kubernetes/minikube
- [mimi cube install](https://minikube.sigs.k8s.io/docs/start/)  
- [Install aand start minikube](https://minikube.sigs.k8s.io/docs/start/
- https://www.oreilly.com/library/view/kubernetes-for-serverless/9781788620376/a24ee8be-d8b0-45cb-8b2d-a12a26e29db7.xhtml
<pre>
start docker application
run --> minikube start --driver=docker
minikube kubectl -- get po -A
minikube status
output:
    type: Control Plane
    host: Running
    kubelet: Running -> runs on the worker node
    apiserver: Running
    kubeconfig: Configured
ref: https://minikube.sigs.k8s.io/docs/handbook/dashboard/

kubectl get nodes
kubectl cluster-info
Start the Kubernetes Dashboard on port 8080
kubectl proxy --port=8080
http://localhost:8080/ui

ref: https://docs.bitnami.com/tutorials/get-started-serverless-computing-kubeless/

minikube dashboard --url
output:
http://127.0.0.1:55002/api/v1/namespaces/kubernetes-dashboard/services/http:kubernetes-dashboard:/proxy/


minikube pause
minikube unpause
minikube delete --all
minikube start --driver=docker

ref:
https://github.com/kubernetes/minikube/issues/9040
https://minikube.sigs.k8s.io/docs/drivers/docker/
</pre>

# Install the Kubeless CLI tool
Kubeless is an application designed to be deployed on top of a Kubernetes cluster. It accepts commands 
to register, delete, and list functions that you would like to run. Once Kubeless is running, all of the
hassles of setting up containers and pods, disappear.


<!--curl -L https://github.com/kubeless/kubeless/releases/download/v1.0.8/kubeless_windows-amd64.zip > kubeless.zip -->
wget https://github.com/kubeless/kubeless/releases/download/v1.0.8/kubeless_windows-amd64.zip  -o kubeless.zip
<!-- unzip kubeless.zip--> used 7-zip ui to unzip
copy .\kuberless\bundles\kubeless_windows-amd64\kubeless.exe c:\minikube

ref: https://github.com/kubeless/kubeless/releases/tag/v1.0.8

# coding begins deploy code on minikube
- [serverless-and-kubernetes-via-kubeless](https://www.serverless.com/blog/serverless-and-kubernetes-via-kubeless)
<pre>
# Create a new Serverless Service/Project
$ serverless create --template kubeless-python --path C:\Users\padma\github\123ofaws\kubernetes\k8s_serverless
# Change into the newly created directory
$ cd new-project
# Install npm dependencies
$ npm install
https://github.com/kubernetes/minikube
</pre>


Notes:
- https://kubeless.io/
- https://github.com/kubernetes/minikube 
- [mimi cube install](https://minikube.sigs.k8s.io/docs/start/)  
- https://github.com/kubeless/kubeless/blob/master/README.md
