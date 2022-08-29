Welcome to this tutorial where we will take you step by step in creating an AKS Application with a custom domain that is secured via https. This tutorial assumes you are logged into Azure CLI already and have selected a subscription to use with the CLI. It also assumes that you have helm installed (Instructions ca be found here https://helm.sh/docs/intro/install/). If you have not done this already. Press b and hit ctl c to exit the program.

To Login to Az CLI and select a subscription 
'az login' followed by 'az account list --output table' and 'az account set --subscription "name of subscription to use"'

To Install Az CLI
If you need to install Azure CLI run the following command - curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash


Assuming the pre requisites are met press enter to proceed

## Define Command Line Variables 
Most of these variables should be set to a smart default. However, if you want to change them
press b and run the command export VARIABLE_NAME="new variable value"

```
echo $RESOURCE_GROUP_NAME
echo $RESOURCE_LOCATION
echo $AKS_CLUSTER_NAME
echo $PUBLIC_IP_NAME
echo $VNET_NAME
echo $SUBNET_NAME
echo $APPLICATION_GATEWAY_NAME
echo $OSM_VERSION
echo $OSM_ARCH
echo $RELEASE_BRANCH
```

## Download Open Service Mesh CLI 
```
curl -sL "https://github.com/openservicemesh/osm/releases/download/v1.1.1/osm-v1.1.1-linux-amd64.tar.gz" | tar -vxzf -
export $OSM_PATH=`pwd`"/"$OSM_ARCH"/"osm
```

## Create A Resource Group
The first step is to create a resource group.

Validate that ResourceGroup does not already exist 

```
if [ "$(az group exists --name $RESOURCE_GROUP_NAME)" = 'true' ]; then export RAND=$RANDOM; export RESOURCE_GROUP_NAME="$RESOURCE_GROUP_NAME$RAND"; echo "Your new Resource Group Name is $RESOURCE_GROUP_NAME"; fi
```

Create Resource Group
```
az group create --name $RESOURCE_GROUP_NAME --location $RESOURCE_LOCATION
```

## Create an AKS Cluster 
The next step is to create an AKS Cluster. This can be done with the following command - 

This will take a few minutes
```
az aks create --resource-group $RESOURCE_GROUP_NAME --name $AKS_CLUSTER_NAME --node-count 1 --enable-addons monitoring --generate-ssh-keys  --enable-addons open-service-mesh
```

## Install az aks CLI locally using the az aks install-cli command
To manage a Kubernetes cluster, use the Kubernetes command-line client, kubectl. kubectl is already installed if you use Azure Cloud Shell.

```
if ! [ -x "$(command -v kubectl)" ]; then az aks install-cli; fi
```
## Download AKS Credentials
Configure kubectl to connect to your Kubernetes cluster using the az aks get-credentials command. The following command:

Downloads credentials and configures the Kubernetes CLI to use them.
Uses ~/.kube/config, the default location for the Kubernetes configuration file. Specify a different location for your Kubernetes configuration file using --file argument. WARNING - This will overwrite any existing credentials with the same entry

```
az aks get-credentials --resource-group $RESOURCE_GROUP_NAME --name $AKS_CLUSTER_NAME --overwrite-existing
```

Verify that the OSM add-on is installed on your cluster
```
az aks show --resource-group myResourceGroup --name myAKSCluster  --query 'addonProfiles.openServiceMesh.enabled'
```

Verify that the OSM mesh is running on your cluster
```
kubectl get deployment -n kube-system osm-controller -o=jsonpath='{$.spec.template.spec.containers[:1].image}'
```

Verify configuration of OSM mesh
```
kubectl get meshconfig osm-mesh-config -n kube-system -o yaml
```

Verify Connection
Verify the connection to your cluster using the kubectl get command. This command returns a list of the cluster nodes.

```
kubectl get nodes
```

Create a namespace for application service
```
kubectl create ns httpbin
```

# Add the namespace to the mesh
```
$OSM_PATH namespace add httpbin
```

# Deploy application service
```
kubectl apply -f https://raw.githubusercontent.com/openservicemesh/osm-docs/$RELEASE_BRANCH/manifests/samples/httpbin/httpbin.yaml -n httpbin
```

Verify that the pods are up and running, and have the envoy sidecar injected:
```
kubectl get pods -n httpbin
kubectl get svc -n httpbin
```

Deploy Ingress and IngressBackend configurations to allow external access on port 14001
```
kubectl apply -f azure-httpbin-ingress.yml
```

Ensure that both the Ingress and IngressBackend objects have ::wbeen successfully deployed
```
kubectl get ingress -n httpbin
kubectl get ingressbackend -n httpbin
```

Display external IP address of the ingress service
```
kubectl get ingress -n httpbin
```

# To do: 1. Print the curl command to verify application end point: "curl -sI http://<external-ip>/get" 2. Cleanup 