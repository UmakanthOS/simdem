## Prerequisites
First we need to check you are logged in to the Azure in the CLI. The following command will check to see if you are logged in. If not it will open a browser and take you through the login steps.
`
az login
`

```
env | grep MY_
```

# Create a resource group

A resource group is a container for related resources. All resources must be placed in a resource group. We will create one for this tutorial. 

This command used two environment variables, `MY_RESOURCE_GROUP_NAME` is the name of the resource group and will be commonly using in other commands. `MY_LOCATION` is the data center that the resource group will be created in. When this command has completed it will return a JSON file. You can see what the values are set at for this tutorial in that output.

```
az group create --name $MY_RESOURCE_GROUP_NAME --location $MY_LOCATION
```

## Create an AKS Cluster 
The next step is to create an AKS Cluster. This can be done with the following command - 
```
az aks create --resource-group $MY_RESOURCE_GROUP_NAME --name $MY_AKS_CLUSTER_NAME --node-count 1 --enable-addons monitoring --generate-ssh-keys
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
az aks get-credentials --resource-group $MY_RESOURCE_GROUP_NAME --name $MY_AKS_CLUSTER_NAME --overwrite-existing
```

Verify connectivity to cluster
#Verify the connection to your cluster using the kubectl get command. This command returns a list of the cluster nodes.
```
kubectl get nodes
```

Add Chaos mesh via helm repo
## Add Chaos mesh via helm repo
```
helm repo add chaos-mesh https://charts.chaos-mesh.org
```

Update helm Repo
```
helm repo update
```

Create a Kubernetes namespace 
```
kubectl create ns chaos-testing
```

Install chaos-mesh
```
helm install chaos-mesh chaos-mesh/chaos-mesh --namespace=chaos-testing --set chaosDaemon.runtime=containerd --set chaosDaemon.socketPath=/run/containerd/containerd.sock
```

Verify that the Chaos Mesh pods are installed by running the following command:
```
kubectl get po -n chaos-testing
```

Get resource id for AKS cluster
```
export MY_AKS_RESOURCE_ID=$(cut -d/ -f2-9 <<< $(az aks show --name myAKSCluster -g myAKSResourceGroup | grep 'id.*Microsoft.Container\|Microsoft.Container.*id') | sed 's/..$//')
```
```
echo $MY_AKS_RESOURCE_ID
```

Delete any older experiment scripts
```
if [ -f experiment.json ]; then rm experiment.json; fi
```

Make a copy of the provided sample.json .
```
cp sample.json experiment.json
```

Update AKS Cluster info
```
sed -i 's|TargetAKSCluster|'$MY_AKS_RESOURCE_ID'|g' experiment.json
```

Get Azure subscription id
```
export MY_AZURE_SUB_ID=$(az account show --query id --output tsv)
echo $MY_AZURE_SUB_ID
```

Register Chaos Resource Provider for your Azure subscription
```
az provider register --namespace "Microsoft.Chaos" --subscription $MY_AZURE_SUB_ID
```

Create a target for the AKS cluster
```
az rest --method put --url "https://management.azure.com/$MY_AKS_RESOURCE_ID/providers/Microsoft.Chaos/targets/Microsoft-AzureKubernetesServiceChaosMesh?api-version=2021-09-15-preview" --body "{\"properties\":{}}"
```

Create capability on the target
```
az rest --method put --url "https://management.azure.com/$MY_AKS_RESOURCE_ID/providers/Microsoft.Chaos/targets/Microsoft-AzureKubernetesServiceChaosMesh/capabilities/$MY_CHAOS_CAPABILITY?api-version=2021-09-15-preview" --body "{\"properties\":{}}"
```

Your AKS cluster is now onboarded. Time to create your Chaos experiment
```
export MY_PRINCIPAL_ID=$(az rest --method put --uri https://management.azure.com/subscriptions/f7a60fca-9977-4899-b907-005a076adbb6/resourceGroups/myAKSResourceGroup/providers/Microsoft.Chaos/experiments/myExperiment?api-version=2021-09-15-preview --body @experiment.json | grep 'principalId' | awk '{print $2}' | sed -e 's/^.//' -e 's/..$//')
echo $MY_PRINCIPAL_ID
```

Give this experiment permission to your AKS cluster
```
az role assignment create --role "Azure Kubernetes Service Cluster Admin Role" --assignee-object-id $MY_PRINCIPAL_ID --scope $MY_AKS_RESOURCE_ID
```

Run your experiment
```
export MY_EXPERIMENT_STATUS=$(az rest --method post --uri https://management.azure.com/subscriptions/$MY_AZURE_SUB_ID/resourceGroups/$MY_RESOURCE_GROUP_NAME/providers/Microsoft.Chaos/experiments/$MY_CHAOS_EXPERIMENT/start?api-version=2021-09-15-preview |  grep 'principalId' | awk '{print $2}' | sed -e 's/^.//' -e 's/..$//')
echo $MY_EXPERIMENT_STATUS
```

Get experiment status
```
az rest --method get --uri $MY_EXPERIMENT_STATUS
```