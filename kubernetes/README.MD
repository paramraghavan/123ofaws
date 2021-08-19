Kubernetes aka k8s
----------------------------

VM-Ware vs Docker
-------------------
-------------------
![image](https://user-images.githubusercontent.com/52529498/129439177-542d37b7-75b9-4823-a276-9df80b56ccd7.png)

- If your applications runs on k8s,  then it can run on cloud or for that matter any flavor of cloud or off cloud(meaning on-premise) with no changes to your code.
Basically decouples application from underlying cloud. k8s is kind of a *conductor* of a container orchestra
- https://kubernetes.io/docs/concepts/overview/components


# K8s


## Kubernetes Clusters
Kubernetes coordinates a highly available cluster of computers that are connected to work as a single unit. The abstractions in Kubernetes allow you to deploy containerized applications to a cluster without tying them specifically to individual machines. To make use of this new model of deployment, applications need to be packaged in a way that decouples them from individual hosts: they need to be containerized.**Containerized** applications are more flexible and available than in past deployment models, where applications were installed directly onto specific machines as packages deeply integrated into the host. Kubernetes automates the distribution and scheduling of application containers across a cluster in a more efficient way. 

- A Kubernetes cluster consists of two types of resources:
    - The Control Plane coordinates the cluster
    - Nodes/worker nodes are the workers that run applications

## Cluster Diagram
![image](https://user-images.githubusercontent.com/52529498/129478836-6ed6c799-dfdd-4d3a-8460-72f2e93f0b63.png)

## Control Plane Image
![image](https://user-images.githubusercontent.com/52529498/129500383-8515dacf-a0e5-4ff6-8b6b-90819acfdd2f.png)
<!--![image](https://user-images.githubusercontent.com/52529498/129479478-976b1da1-38f6-4a55-a16a-ee3bd9c30e82.png)-->
- **The Control Plane** is responsible for managing the cluster. The Control Plane coordinates all activities in your cluster, such as scheduling applications(Scheduler), maintaining applications' desired state(Cluster store), scaling applications, and rolling out new updates (Controller) and apiserver to interface with Nodes

## Node Image
![image](https://user-images.githubusercontent.com/52529498/129479774-e5a4b480-70cf-4a17-982a-9455f20f1d4b.png)

- **A node also called pod**, a single POD could runmore than one container.  Nodes can be linux or windows and serves as a worker machine in a Kubernetes cluster. Each node has a Kubelet, which is an agent for managing the node and communicating with the Kubernetes control plane. The node should also have tools for handling container operations, such as containerd or Docker. A Kubernetes cluster that handles production traffic should have a minimum of three nodes. So there's basically three components that we care about:
  - kubelet,
  - the container runtime
  - the kube proxy. 

- Control Planes manage the cluster and the nodes that are used to host the running applications.

When you deploy applications on Kubernetes, you tell the control plane to start the application containers. The control plane schedules the containers to run on the cluster's nodes. The nodes communicate with the control plane using the Kubernetes API, which the control plane exposes. End users can also use the Kubernetes API directly to interact with the cluster.

A Kubernetes cluster can be deployed on either physical or virtual machines. To get started with Kubernetes development, you can use [Minikube](https://github.com/paramraghavan/123ofaws/blob/main/kubernetes/README.MD#steps-to-install-minikube-deploy-and-execute-apps) 

# Amazon EKS 
Amazon EKS is a managed service that makes it easy for you to use Kubernetes on AWS without needing to install 
and operate your own Kubernetes control plane. Amazon EKS exposes a Kubernetes API endpoint. Your existing 
Kubernetes tooling can connect directly to EKS managed control plane. Worker nodes run as EC2 instances in 
your account. 
- https://console.aws.amazon.com/eks/home?region=us-east-1#
- https://kubernetes.io/docs/tutorials/kubernetes-basics/create-cluster/cluster-intro/

# minikube vs kubernetes

Minikube is a lightweight Kubernetes implementation that creates a VM on your local machine and deploys a simple cluster containing only one node. Minikube is available for Linux, macOS, and Windows systems. The Minikube CLI provides basic bootstrapping operations for working with your cluster, including start, stop, status, and delete.

## Steps to install Minikube, deploy and execute apps
- [Install docker desktop](https://desktop.docker.com/win/stable/amd64/Docker%20Desktop%20Installer.exe)
- Start docker desktop
- [Install minikube](https://minikube.sigs.k8s.io/docs/start/)  
- Run the following with docker option especially for Windows 10 Home edition
> minikube start --driver=docker

minikube kubectl -- get po -A

minikube status
>output:
> 
    type: Control Plane
    host: Running
    kubelet: Running -> runs on the worker node
    apiserver: Running
    kubeconfig: Configured
kubectl get nodes

kubectl cluster-info

minikube dashboard --url
>output:
>
    http://127.0.0.1:55002/api/v1/namespaces/kubernetes-dashboard/services/http:kubernetes-dashboard:/proxy/
    use the above url to connect to k8s dashboard ui

minikube pause

minikube unpause

minikube delete --all

minikube ssh

## Deploy docker image to minikube
- Start minikube, if it is not already started
minikube start
  
- Steps to use the docker daemon running inside minikube to build image and deploy this image onto minikube. **Important note:** You have to run eval $(minikube docker-env) on each terminal you want to use, since it only sets the environment variables for the current shell session.
<pre>
eval $(minikube docker-env)             # unix shells
& minikube -p minikube docker-env | Invoke-Expression # PowerShell
docker images  
</pre>
- pyflask using it's default port 5000, change directory to folder having the Dockerfile and then build th docker inage as follows:

docker build -t pyflask-docker .

docker images <-- u should now see pyflask-docker

- Check pods running

kubectl get pods
  
kubectl get services pyflask

- The yaml file you create can then be deployed with the following command, uses the image in docker daemon

kubectl apply -f pyflask-deploy.yml

kubectl get deployments

kubectl expose deployment pyflask-deploy --type=LoadBalancer --port=5000

>Note that without minikube tunnel, kubernetes would be showing external IP as “pending
> 
minikube start --extra-config=apiserver.service-node-port-range=1-65535

minikube tunnel

kubectl get svc
<pre>
NAME             TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
kubernetes       ClusterIP      10.96.0.1       <none>        443/TCP          14h
pyflask-deploy   LoadBalancer   10.103.81.119   127.0.0.1     5000:35362/TCP   11s
</pre>

- delete service

kubectl delete svc pyflask-deploy

Note
----
- https://github.com/kubernetes/minikube
- [mimi cube install](https://minikube.sigs.k8s.io/docs/start/)  
- [Install and start minikube](https://minikube.sigs.k8s.io/docs/start/
- https://minikube.sigs.k8s.io/docs/handbook/dashboard/
- https://github.com/kubernetes/minikube/issues/9040
- https://minikube.sigs.k8s.io/docs/drivers/docker/
- https://minikube.sigs.k8s.io/docs/handbook/accessing/
- https://medium.com/bb-tutorials-and-thoughts/how-to-use-own-local-doker-images-with-minikube-2c1ed0b0968

# docker + flask webserver
- https://docs.docker.com/language/python/build-images/

# Install the Kubeless CLI tool
Kubeless is an application designed to be deployed on top of a Kubernetes cluster. It accepts commands 
to register, delete, and list functions that you would like to run. Once Kubeless is running, all of the
hassles of setting up containers and pods, disappear.


Notes:
- https://kubeless.io/
- https://github.com/kubernetes/minikube 
- [mini cube install](https://minikube.sigs.k8s.io/docs/start/)  
- https://github.com/kubeless/kubeless/blob/master/README.md
