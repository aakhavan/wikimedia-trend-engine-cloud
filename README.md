# Wikimedia Trends Engine (Cloud-Native on AWS)

This repository contains the complete infrastructure and application code for a modern, cloud-native data platform built on Amazon Web Services. The project demonstrates an end-to-end solution for ingesting, processing, and storing data using parallel streaming and batch pipelines.

The entire platform is defined using Infrastructure as Code (IaC) with Terraform, making it reproducible, modular, and easy to manage.

## Guiding Principles

* **Infrastructure as Code First:** All AWS resources are provisioned and managed through Terraform. There is no manual setup required in the AWS Console.
* **Serverless & Managed:** The architecture prioritizes AWS managed services (MSK, EMR Serverless, Glue) to reduce operational overhead and improve scalability.
* **Cost-Effective by Design:** By leveraging serverless components, the AWS Free Tier, and the ability to destroy the entire stack on demand, the project is designed to run at a minimal cost.
* **Modular & Reproducible:** The codebase is structured to be easily understood, deployed, and torn down.

## Architecture Overview

The platform consists of two distinct data pipelines that run in parallel, feeding into a unified data lakehouse built with Apache Iceberg.

*(A proper architecture diagram would be placed here)*

### Shared Infrastructure

* **Networking:** A dedicated VPC with public and private subnets to securely host our resources.
* **Storage (S3):** A central S3 bucket acts as the data lake, storing raw data, Spark application code, and the Apache Iceberg tables.
* **Data Catalog (AWS Glue):** The AWS Glue Data Catalog is used as the metastore for Apache Iceberg, making tables discoverable.
* **Orchestration (Airflow on EC2):** A `t2.micro` EC2 instance hosts a Dockerized Apache Airflow for scheduling and monitoring the batch pipeline.

### Pipeline 1: Real-Time Streaming

1.  **Ingestion:** A Python producer script connects to the live Wikimedia SSE stream and pushes events into an **Amazon MSK Serverless** (Managed Kafka) topic.
2.  **Processing:** An **Amazon EMR Serverless** Spark application consumes these events in a structured stream, performs transformations, and prepares the data for storage.
3.  **Storage:** The processed real-time data is written continuously into the `wikimedia.recent_changes_stream` Iceberg table.

### Pipeline 2: Scheduled Batch

1.  **Orchestration:** An **Apache Airflow DAG** triggers the batch job on a defined schedule (e.g., hourly).
2.  **Processing:** The DAG submits a job to **Amazon EMR Serverless**. This Spark application reads a batch of raw JSON files from S3 and performs the same transformations as the streaming job.
3.  **Storage:** The processed batch data is appended to the `wikimedia.recent_changes_batch` Iceberg table.

## Technology Stack

* **Cloud Provider:** AWS
* **IaC:** Terraform
* **Compute:** Amazon EMR Serverless (for Spark), Amazon EC2 (for Airflow)
* **Messaging:** Amazon MSK Serverless (for Kafka)
* **Storage:** Amazon S3
* **Data Catalog:** AWS Glue Data Catalog
* **Table Format:** Apache Iceberg
* **Orchestration:** Apache Airflow
* **Containerization:** Docker
* **Language:** Python, PySpark

---

## Deployment and Execution

### Prerequisites

1.  An AWS Account.
2.  AWS CLI installed and configured with credentials (`aws configure`).
3.  Terraform installed locally.
4.  Docker installed locally (for running Airflow).

### Step 1: Deploy the Infrastructure

First, deploy all the required AWS resources using Terraform.

```bash
# Navigate to the terraform directory
cd terraform/

# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Apply the configuration to create the resources
terraform apply
```

This command will provision the VPC, S3 bucket, MSK Cluster, EMR Serverless Application, EC2 instance, and all necessary IAM roles. Note the outputs from Terraform, as you will need them (e.g., the MSK Bootstrap Servers and EC2 public IP).

### Step 2: Set Up and Run Airflow

1.  SSH into the EC2 instance created by Terraform.
2.  Follow a standard guide to set up a Dockerized Airflow instance.
3.  Place the `wikimedia_batch_dag.py` file into the `dags` folder of your Airflow setup.
4.  Unpause the DAG in the Airflow UI to begin the scheduled batch runs.

### Step 3: Run the Kafka Producer

To start feeding the streaming pipeline, run the producer script from your local machine or another EC2 instance. You will need to configure it with the MSK Bootstrap Server URL provided by the Terraform output.

```bash
# Install dependencies
pip install -r requirements.txt

# Run the producer
python scripts/producer.py
```

### Step 4: Monitor the Pipelines

* **Streaming Job:** Monitor the logs and status in the Amazon EMR Serverless UI in the AWS Console.
* **Batch Job:** Monitor the DAG runs, task statuses, and logs directly within the Airflow UI.

### Step 5: Destroy All Resources

**This is the most important step for cost control.** When you are finished working, tear down the entire infrastructure with a single command.

```bash
# From the terraform/ directory
terraform destroy
```

This will remove all the resources you created, ensuring you do not incur any further costs.
