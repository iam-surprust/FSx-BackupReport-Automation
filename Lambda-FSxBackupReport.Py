import boto3
import csv
import io
from datetime import datetime

# Required constants
BUCKET_NAME = 'fsx-Backup-report' #replace with your Bucket name
OBJECT_KEY_PREFIX = 'FSx_backup_report/'
TOPIC_ARN = 'arn:aws:sns:ap-south-1:*****:***'


def lambda_handler(event, context):
    fsx = boto3.client('fsx')
    s3 = boto3.client('s3')
    sns = boto3.client('sns')

    # --- 1. Get all FSx backups ---
    backups = []
    next_token = None
    while True:
        if next_token:
            response = fsx.describe_backups(NextToken=next_token)
        else:
            response = fsx.describe_backups()
        backups.extend(response['Backups'])
        next_token = response.get('NextToken')
        if not next_token:
            break

    # --- 2. Prepare CSV file ---
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Backup Id',
        'Resource Type',
        'FileSystem / Volume Id',
        'Lifecycle',
        'Type',
        'Creation Time',
        'Backup Name',
        'Storage Capacity (GiB)',
        'ResourceARN',
        'KmsKeyId'
    ])

    # --- 3. Process each backup safely ---
    for backup in backups:
        resource_type = backup.get('ResourceType', 'FILE_SYSTEM')
        storage_capacity = 'N/A'
        fs_id = ''
        backup_name = ''

        # Handle FileSystem backups
        if resource_type == 'FILE_SYSTEM' and 'FileSystem' in backup:
            fs_id = backup['FileSystem'].get('FileSystemId', '')
            try:
                fs_details = fsx.describe_file_systems(FileSystemIds=[fs_id])
                fs_data = fs_details['FileSystems'][0]
                storage_capacity = fs_data.get('StorageCapacity', 'N/A')
            except Exception as e:
                print(f"Warning: Could not get FSx FileSystem details for {fs_id}: {e}")

        # Handle Volume backups
        elif resource_type == 'VOLUME' and 'Volume' in backup:
            fs_id = backup['Volume'].get('VolumeId', '')
            storage_capacity = backup['Volume'].get('Capacity', 'N/A')

        # Extract backup name safely
        if 'Tags' in backup and backup['Tags']:
            for tag in backup['Tags']:
                if tag.get('Key', '').lower() in ['name', 'backupname']:
                    backup_name = tag.get('Value', '')
                    break

        writer.writerow([
            backup.get('BackupId', ''),
            resource_type,
            fs_id,
            backup.get('Lifecycle', ''),
            backup.get('Type', ''),
            str(backup.get('CreationTime', '')),
            backup_name,
            storage_capacity,
            backup.get('ResourceARN', ''),
            backup.get('KmsKeyId', '')
        ])

    # --- 4. Upload CSV to S3 ---
    current_timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    s3_key = f"{OBJECT_KEY_PREFIX}fsx_backup_{current_timestamp}_IND.csv"
    s3.put_object(Bucket=BUCKET_NAME, Key=s3_key, Body=output.getvalue())

    # --- 5. Generate pre-signed URL ---
    url = s3.generate_presigned_url(
        ClientMethod='get_object',
        Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
        ExpiresIn=3600
    )

    # --- 6. Compose and send SNS message ---
    message = (
        f"Hello Everyone,\n\n"
        f"Please find the FSx backup Report IND Region attached to this mail.\n\n {current_timestamp}.\n\n"
        f"Download link (valid for 1 hour):\n{url}\n\n"
        f"Thanks & Regards,\nCIMIC-AWS"
    )

    sns.publish(
        TopicArn=TOPIC_ARN,
        Message=message,
        Subject='FSx Backup Report IND Region'
    )

    return {
        'statusCode': 200,
        'body': 'FSx backup details exported to S3 and Pre-signed URL shared successfully.'
    }
