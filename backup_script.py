import os
import paramiko
import time

# Install paramiko first:
# pip install paramiko
# Make sure the user on your VPS has write permissions to the target folder.


# How to run the script:
# cd to the file directory

# and run 
# python3 backup_script.py

# (Optional) Make it directly executable
# You can also make it so you just type ./backup.py:

# so still in your file directory just type :

# chmod +x backup_script.py

# Then run:

# ./backup_script.py

def backup_folder(local_folder, remote_base_folder, hostname, port, username, password, max_backups=3):
    """
    Backup local_folder to a timestamped folder inside remote_base_folder on VPS.
    Keeps only the latest `max_backups` backups.
    """
    # Connect to VPS
    transport = paramiko.Transport((hostname, port))
    transport.connect(username=username, password=password)
    sftp = paramiko.SFTPClient.from_transport(transport)

    # Create a timestamped backup folder
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    remote_backup_folder = os.path.join(remote_base_folder, timestamp).replace("\\", "/")
    try:
        sftp.mkdir(remote_backup_folder)
    except IOError:
        pass  # If already exists

    # Upload all files
    for root, dirs, files in os.walk(local_folder):
        relative_path = os.path.relpath(root, local_folder)
        remote_path = os.path.join(remote_backup_folder, relative_path).replace("\\", "/")

        # Ensure remote directory exists
        try:
            sftp.stat(remote_path)
        except FileNotFoundError:
            sftp.mkdir(remote_path)

        # Upload files
        for file in files:
            local_file = os.path.join(root, file)
            remote_file = remote_path + "/" + file
            print(f"Uploading {local_file} → {remote_file}")
            sftp.put(local_file, remote_file)

    # Backup rotation: keep only last `max_backups`
    backups = []
    try:
        backups = sorted(sftp.listdir(remote_base_folder))
    except IOError:
        pass

    if len(backups) > max_backups:
        old_backups = backups[:-max_backups]
        for old in old_backups:
            old_path = os.path.join(remote_base_folder, old).replace("\\", "/")
            print(f"Deleting old backup: {old_path}")
            delete_remote_folder(sftp, old_path)

    sftp.close()
    transport.close()
    print("Backup completed successfully.")

def delete_remote_folder(sftp, remote_path):
    """
    Recursively delete a folder on the remote server.
    """
    for entry in sftp.listdir_attr(remote_path):
        entry_path = remote_path + "/" + entry.filename
        if paramiko.S_ISDIR(entry.st_mode):
            delete_remote_folder(sftp, entry_path)
        else:
            sftp.remove(entry_path)
    sftp.rmdir(remote_path)


if __name__ == "__main__":
    # === CONFIGURE HERE ===
    local_folder = "/path/to/local/folder"
    remote_base_folder = "/path/to/remote/backups"
    hostname = "your.vps.ip"
    port = 22
    username = "your_username"
    password = "your_password"

    backup_folder(local_folder, remote_base_folder, hostname, port, username, password, max_backups=3)
