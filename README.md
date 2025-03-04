# Serverless-comfy

## Requirements

To use this project, ensure you have the following:

- **Python 3.8** installed on your machine.
- A **Modal.com account**.
- **Modal.com CLI** installed.
- **Firebase Access**:
  - Access to the Firebase project.
  - A Firebase **service account key** in JSON format.

---

## Getting Started

Follow the steps below to set up and deploy the application.

### **1. Clone the Repository**

If you have not cloned the repository yet, do so by running:

```bash
git clone https://github.com/WeSmileBooth/serverless-comfyui.git
cd serverless-comfyui
```

### **2. Create a Virtual Environment**

It's recommended to use a virtual environment to manage dependencies and avoid conflicts.

#### **On macOS and Linux:**

1. **Create the virtual environment:**

   ```bash
   python3.8 -m venv venv
   ```

2. **Activate the virtual environment:**

   ```bash
   source venv/bin/activate
   ```

#### **On Windows:**

1. **Create the virtual environment:**

   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment:**

   ```cmd
   venv\Scripts\activate
   ```

### **3. Upgrade pip (Optional but Recommended)**

Ensure you have the latest version of pip:

```bash
pip install --upgrade pip
```

### **4. Install Modal Client**

With the virtual environment activated, install the Modal client:

```bash
pip install modal
```

Verify the installation by running:

```bash
modal --help
```

You should see a list of Modal commands if the installation was successful.

### **5. Set Up Modal**

Authenticate with your Modal account:

```bash
modal setup
```

This command will open a browser window for you to log in and generate an API token.

### **6. Obtain Firebase Service Account Key**

The application requires access to Firebase services. You'll need to provide a Firebase service account key.

#### **Steps to Obtain the Firebase Service Account Key:**

1. **Access the Firebase Console:**

   - Go to [Firebase Console](https://console.firebase.google.com/).
   - Log in with your Google account that has access to the project.

2. **Select Your Project:**

   - Choose the project (e.g., `wesmile-photobooth`).

3. **Navigate to Project Settings:**

   - Click the **Settings Gear** icon next to **Project Overview**.
   - Select **Project settings**.

4. **Go to Service Accounts:**

   - Click on the **Service Accounts** tab.

5. **Generate a New Private Key:**

   - Click **Generate new private key**.
   - Confirm by clicking **Generate key**.
   - A JSON file will be downloaded to your computer. **Keep this file secure**.

### **7. Add the Secret to Modal**

Now, you'll create a secret in Modal.com to securely store these credentials.

#### **Create a Secret in Modal.com:**

1. **Log In to Modal.com:**

   - Go to [Modal.com](https://modal.com/) and sign in.

2. **Navigate to Secrets:**

   - From your dashboard, click on **Secrets**.

3. **Create a New Secret:**

   - Click **+ New Secret**.
   - Click **Google Cloud** for secret type
   - **Add Secret Content:**

     - Open the downloaded JSON file in a text editor.
     - Copy the entire content.
     - In the secret creation form, add a key-value pair:
       - **Key:** `SERVICE_ACCOUNT_JSON`
       - **Value:** Paste the JSON content.

   - **Secret Name:** Enter `googlecloud-secret`.

4. **Save the Secret:**

   - Review and click **Create Secret**.

### **8. Deploy the Application**

With the virtual environment activated and the Modal client installed, you can deploy the application.

1. **Navigate to the Project Directory:**

   ```bash
   cd serverless-comfyui
   ```

2. **Deploy the Application:**

   ```bash
   modal deploy comfy-api
   ```

   - The first deployment may take some time as it builds the container and downloads models.
   - Subsequent deployments will be faster.

## Customizing the Workflow

### Adding New Models

To add a new model, follow these steps:

1. **Locate the MODELS array**:
   Open the `comfy-api/models.py` file and look for the `MODELS` array at the top. This array defines the models to be used in the workflow. Example:

```python
MODELS = [
    {
        "url": "https://huggingface.co/Yabo/SDXL_LoRA/resolve/main/dreamshaperXL_alpha2Xl10.safetensors",
        "directory": "/root/models/checkpoints",
    },
    {
        "url": "https://huggingface.co/datasets/Gourieff/ReActor/resolve/main/models/inswapper_128.onnx",
        "directory": "/root/models/insightface",
    }
]
```

2. **Add a new model**:

- Ensure that the model URL is a valid HuggingFace link.
- Specify the directory where the model should be stored (starting with `/root/models`).

3. **Deploy the updated configuration**:
   After updating the models, redeploy the project:

```bash
modal deploy comfy-api
```

### Adding New Nodes

To add a new node to the workflow, follow similar steps as with models:

1. **Locate the NODES array**
   Open the `comfy-api/nodes.py` file and look for the `NODES` array. Example:

```python
NODES = [
    "https://github.com/Gourieff/comfyui-reactor-node",
    "https://github.com/ltdrdata/ComfyUI-Manager",
]
```

2. **Add a new node**
   Add the GitHub URL of the node you want to include.

3. **Deploy the updated configuration**
   Run the following command to rebuild the container and update the nodes:

```bash
modal deploy comfy-api
```

### Modifying the Workflow

#### Updating the Workflow Configuration

You can modify the workflow by either tweaking existing values or replacing the workflow file.

1.  **Modify values**
    If you need to update values like model names or parameters, modify the workflow_api.json file located in `comfy-api/workflow_api.json`.

        For example, to change the checkpoint used:

```json
{
  "5": {
    "inputs": {
      "ckpt_name": "dreamshaperXL_alpha2Xl10.safetensors"
    },
    "class_type": "CheckpointLoaderSimple",
    "_meta": {
      "title": "Load Checkpoint"
    }
  }
}
```

2. **Replace the workflow file**
   If you have a new workflow, export it from ComfyUI with developer mode enabled. Save the exported file as `workflow_api.json` and replace the existing one under `comfy-api/workflow_api.json`.

Make sure the structure of the new workflow file aligns with the expected format.
Example structure:

```json
{
  "1": {
    "inputs": {
      "image": "test.png",
      "upload": "image"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "11": {
    "inputs": {
      "seed": 671311003833018,
      "steps": 25,
      "cfg": 6,
      "sampler_name": "dpmpp_2m",
      "model": ["65", 0]
    },
    "class_type": "KSampler",
    "_meta": {
      "title": "KSampler"
    }
  }
}
```

Adjust input keys: The workflow file references keys like `11` for seeds, `1` for images, and `9` for text. These might differ in your new workflow, so update them in the `comfy-api/__init__.py` file.

Example:

```python
workflow["11"]["inputs"]["seed"] = random.randint(1, 2**64)
workflow["1"]["inputs"]["image"] = input.session_id
workflow["9"]["inputs"]["text"] += input.prompt
```

Ensure that the new key mappings align with your updated workflow structure.

### Removing Models or Nodes

If you wish to remove a model or node:
After removing the entries, redeploy the project.

### Removing Models

Simply remove the corresponding entry from the `MODELS` array in `comfy-api/models.py`.

### Removing Nodes

Remove the desired node from the `NODES` array in `comfy-api/nodes.py`.
