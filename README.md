# FSx-BackupReport-Automation

# 📦 AWS FSx Backup Report Automation – Lambda + S3 + SNS

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/9b409f23-5cbf-4263-8ec9-3c3c20e9f709" />


## 📘 Overview

This project provides an **AWS Lambda** automation that generates FSx backup inventory reports, stores them as **CSV files in S3**, and sends a **pre-signed download link** via **SNS email notification**.

The Lambda function:

✔ Fetches **all FSx backups** (FSx Lustre / Windows / ONTAP / OpenZFS)
✔ Extracts filesystem/volume metadata
✔ Generates a detailed **CSV inventory report**
✔ Uploads to **Amazon S3**
✔ Creates a **1-hour pre-signed download URL**
✔ Sends notification via **Amazon SNS**

Ideal use cases:

* Backup compliance auditing
* DR readiness & periodic reporting
* Storage usage analysis
* Daily/weekly automated reporting

---

## ⚙️ AWS Services Involved

| AWS Service                | Purpose                                              |
| -------------------------- | ---------------------------------------------------- |
| **Lambda**                 | Runs the automation script (Python + boto3)          |
| **FSx**                    | Source of backup, filesystem, and volume metadata    |
| **S3**                     | Stores generated CSV reports                         |
| **SNS**                    | Sends report notification & pre-signed download link |
| **EventBridge (optional)** | Schedules daily/weekly/monthly execution             |
| **CloudWatch Logs**        | Logs lambda execution for debugging                  |

---

## 🏗️ Architecture Diagram (ASCII)

```
             ┌───────────────────────────┐
             │  Amazon EventBridge       │
             │ (Daily / Weekly / Monthly)│
             └──────────────┬────────────┘
                            ▼
                    ┌──────────────┐
                    │ AWS Lambda   │
                    │ Python+boto3 │
                    └──────┬───────┘
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐
  │ FSx Backups │  │ FileSystems │  │   Volume Info    │
  └──────┬──────┘  └──────┬──────┘  └─────────┬────────┘
         ▼                 ▼                   ▼
       Generate CSV Report (In Memory)
                            ▼
                    ┌──────────────┐
                    │ Amazon S3    │
                    │ fsx_backup_*.csv │
                    └──────┬───────┘
                            ▼
                 Generate Pre-signed URL
                            ▼
                    ┌──────────────┐
                    │ Amazon SNS   │
                    │ Email Report │
                    └──────────────┘
```

---

## 📂 Project Structure

```
fsx-backup-report/
│
├── lambda/
│   ├── lambda_function.py     # Main Lambda logic
│   ├── requirements.txt       # Dependencies (if using layers)
│   └── README.md              # This README
│
├── infrastructure/ (optional)
│   ├── terraform/             # IaC deployment
│   └── cloudformation/
│
└── docs/
    ├── architecture-diagram.png (optional)
    └── usage-guide.md
```

---

## 📊 CSV Report Fields

Each report includes:

| Column                 | Description                       |
| ---------------------- | --------------------------------- |
| Backup Id              | Unique FSx backup ID              |
| Resource Type          | FILE_SYSTEM / VOLUME              |
| FileSystem / Volume ID | Associated resource               |
| Lifecycle              | AVAILABLE / CREATING / DELETED    |
| Type                   | USER_INITIATED / AUTOMATIC        |
| Creation Time          | Timestamp                         |
| Backup Name            | From “Name” tag                   |
| Storage Capacity       | Filesystem size / Volume capacity |
| ResourceARN            | ARN for traceability              |
| KmsKeyId               | If encrypted                      |

---

## 🧠 How the Lambda Works (Step-by-Step)

### 1. Fetch FSx backups

Uses `describe_backups()` with pagination.

### 2. For every backup, extract:

* FileSystem / Volume ID
* Storage capacity
* Tags (`Name`, `BackupName`)
* Lifecycle, type, timestamp, ARN

### 3. Generate CSV in memory using `io.StringIO`

### 4. Upload CSV to S3

File name format:

```
fsx_backup_YYYY-MM-DD_HH-MM-SS_IND.csv
```

### 5. Generate 1-hour pre-signed URL

### 6. Publish SNS email notification

---

## 🔐 IAM Permissions Required

Lambda role must include:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "fsx:DescribeBackups",
        "fsx:DescribeFileSystems",
        "s3:PutObject",
        "s3:GetObject",
        "sns:Publish"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## 🚀 Deployment Instructions

### Option 1 — Console Deployment

1. Create AWS Lambda → Python 3.x
2. Paste the script into `lambda_function.py`
3. Add correct environment variables:

   * `BUCKET_NAME`
   * `TOPIC_ARN`
4. Attach IAM role with permissions above
5. Deploy
6. Test manually

---

### Option 2 — EventBridge Scheduling

To run daily at 9 AM:

```
cron(0 9 * * ? *)
```

---

## ✔ Example SNS Message Output

```
Hello Everyone,

Please find the FSx backup Report IND Region attached to this mail.

2025-02-13_10-30-55.

Download link (valid for 1 hour):
https://s3-presigned-link....

Thanks & Regards,
CIMIC-AWS
```

---

## 🧩 Future Enhancements

* Integrate with AWS Backup API
* Upload to Athena-compatible parquet for querying
* Add dashboard using QuickSight
* Automatic cleanup of old reports (S3 lifecycle)
* Multi-region scanning

Just tell me!
