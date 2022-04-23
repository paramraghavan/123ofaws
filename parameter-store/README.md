# Parameter Store


## Default Encryption on AWS
One simple thing you can do to increase the security of items stored in your S3 buckets, and that's to turn 
on default encryption for the bucket. Navigate to AWS console-->S3, it's one little radio button to **set the 
default encryption at rest** for new items uploaded to the bucket, and you can enable or disable this at any time. Now 
it won't retroactively encrypt any data that's already in the bucket, but it will automatically encrypt anything you 
upload to the bucket from that point forward after you enable it.

This default encryption can be done with either an AWS S3 managed key, which is referred to as **SSE for server‑side encryption**, S3,
or a key you manage yourself within the AWS Key Management Service, or **SSE‑KMS**. Beyond these two encryption 
options that you get with default encryption SSE‑S3 and SSE‑KMS, there are a couple of other ways you could encrypt 
data at rest in S3. One is to use server‑side encryption with customer‑provided keys or **SSE‑C**, and the other is 
**client‑side** encryption. 

And there's an important distinction here between SSE‑KMS and SSE‑C. With SSE‑C, you, 
the customer, are still managing the key yourself, but completely outside of AWS. So this is useful if you already have
keys that you're using outside of AWS. Or maybe there are compliance requirements that prevent you from storing your
keys in AWS. When you use SSE‑C, you have to provide your key in the request header every time you upload or download 
an object because that key isn't stored in AWS at all. But AWS still needs the key in order to encrypt or decrypt the 
data on its end. And this is important. Keep in mind that AWS is still doing the encryption and decryption operations
with your key. It just isn't storing the key anywhere.

With client‑side encryption, and you'll notice it doesn't have an SSE acronym because the encryption doesn't happen 
server side. Instead, you manage your own keys and encrypt the 
data yourself before you upload it into S3. Similarly, this means that you also decrypt the data yourself after you
download it from S3. With client‑side encryption, AWS never knows anything about the key or the encryption algorithm you
choose because you are performing your own encryption and decryption. So there may be some instances where security 
policy dictates that you do client‑side encryption so that AWS can't see your key at all.

## Encryption Options across AWS Services
Obviously, S3 isn't the only place we can store data in AWS, and S3 is a little unique because you can enable default
encryption or change the encryption of an individual object anytime you'd like. But that isn't how most AWS services
handle encryption. Most of other AWS services require you to enable encryption at the time a resource is created 
like - EBS volumes and the EFS file systems, as well as DynamoDB tables and Redshift clusters.

S3
--
default encryption, SSE‑S3 - AES‑256 

EB/EFS
-------
AWS Console, AWS services, go to EC2, creating new EBS volume, click Create Volume, here on the first screen,
you'll see a checkbox for encryption. And if I check that box and hit the dropdown, you'll see the default option
here is the aws/ebs key, which is an AWS managed
key. Important information here regarding the encryption status of new EBS volumes based on encrypted
versus unencrypted snapshots. What this is basically saying is if you're creating a new EBS volume from an existing
snapshot, it will inherit the encryption status of that snapshot. If you're creating a new volume, you can decide
whether or not to encrypt it. But you have to m**ake this decision at the time you create the volume**. You can only change
it down the road by creating a new snapshot and then creating a new volume based on that snapshot.

AWS Console, AWS services, go to EFS and then click Create file system, go to the
next step here and scroll down. And you'll see again, have the option to enable encryption of data at rest. And there
is an important note you see here, encryption of data at rest can only be enabled during file system creation. But
encryption of data in transit is configured when mounting the file system from an EC2 instance. **So keep in mind that
there is not just encryption at rest, but also encryption in transit here with EFS with data going across the network to
be stored on the network file system**. And again, if I check the box here, just like with EBS, I can choose which KMS
master key to use.

dynamodb
---------
you can create a new DynamoDB table, you'll see the settings include encryption at rest enabled by default. If I uncheck this
quickly, you'll see I can also choose encryption with KMS using a customer‑managed CMK or an AWS‑managed CMK.

Redshift
---------
When you create a new Redshift cluster, if you scroll down and canturn off the
default configuration, scroll down to Database configurations. And here you'll see similar options, so use an AWS
KMS key, which could be the default AWS‑managed Redshift key or a CMK you manage from this account or from another
account.

## Key Management Service (KMS)
AWS gives us the Key Management Service, or KMS, to enable us to create and manage **customer master keys, or CMKs**.
And KMS integrates with almost every other service in AWS that can encrypt data. CMKs, what we really care about is the
key material or the cryptographic material that consists of the actual bits that make your key uniquely yours. It's this
material that performs the actual encryption and decryption operations on your data. And by default, when you create a
CMK, AWS will generate the key material for it. As you might expect, this is called AWS‑generated key material. But you
may have compliance requirements that dictate how you must generate your own key material. Or maybe you'd like to
maintain your key material outside of AWS for additional redundancy. KMS allows you to do this. But keep in mind, the
decision you make will impact how and when you can rotate your keys, which is really just changing out the backing key
material for your CMK. And rotating your keys is important because you always want to minimize the scope of damage that
can be done if a key somehow gets compromised.

Key rotation
-------------
Key rotation is what happens when we update a key's backing material, and AWS saves the old key material so you will
always be able to decrypt information that was previously encrypted with an old backing key. Now for the standard AWS
managed keys, and these are, of course, the default keys you see for each service in each region, the key material is
automatically rotated every three years. You can't change or disable this, and this rotation happens in a way that is
completely transparent to you, and when a key is automatically rotated, you don't actually need to update any references
to keys in your application, because it's only the **keys backing material that has changed, not its ID or alias**.

Open AWS Console let's hop over to the KMS console, steps create new customer master keys. I'll go to kms, and you may
not have any keys
yet, so go over here and click Create key. By default, keys you create in KMS are what are called symmetric keys.
These keys never leave AWS unencrypted, which is obviously a best practice. Now you could choose asymmetric here, but
I'll leave this as symmetric, and then show you the advanced options here, which is where I choose between KMS for the
key material origin, which is AWS‑managed key material, or external, which means I would import my own key material. 

