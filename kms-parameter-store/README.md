# Encrypting and Storing Passwords


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

Key Policies and grants
------------------------
When we created our CMK, see above, we got to select which users and
roles were key administrators, as well as the users, roles, and AWS accounts that have access to use the key for
encryption and decryption. And all of these selections were reflected in the default key policy that was created for the
key. 

Policy file is a JSON document And when we decipher these
policies, we want to look at three things, the effect, the action, and the resource. So this first one here says Enable
IAM User Permissions. And what it's doing is allowing, so that's the effect, the action of all operations within KMS, so
that's the asterisk there, on all resources, so again you see the asterisk. And this applies to the root account within
our AWS account with this number here. So this statement gives the root account full access to this key, which is
important because no matter what else we do with permissions here, we will always have the ability to use our root
account to get access to this key and then use IAM policies to grant access to other users, roles, and accounts to be
able to also access this key. And although it looks like this statement is only allowing access to the root account, it
does also mean that other IAM users and roles in the account might have access to the CMK even though they don't show up
directly here.
<pre>
        {
            "Sid": "Enable IAM User Permissions",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::111111111111:root"
            },
            "Action": "kms:*",
            "Resource": "*"
        }
</pre>


Now this next statement is granting administrative access to our **myapp** account, and you see again
the effect of allow, the action of this list of administrative operations within KMS, so things like create, update,
revoke, disable, and the asterisk here again denoting all resources. 
<pre>
        {
            "Sid": "Allow access for Key Administrators",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::111111111111:user/myapp"
            },
            "Action": [
                "kms:Create*",
                "kms:Describe*",
                "kms:Enable*",
                "kms:List*",
                "kms:Put*",
                "kms:Update*",
                "kms:Revoke*",
                "kms:Disable*",
                "kms:Get*",
                "kms:Delete*",
                "kms:TagResource",
                "kms:UntagResource",
                "kms:ScheduleKeyDeletion",
                "kms:CancelKeyDeletion"
            ],
            "Resource": "*"
        }
</pre>

The next statement is for the key usage permissions
where again we just chose the AWS myapp account. But here again, the effect is allow. The list of actions this time are
just the actions of actually using the key to encrypt and decrypt data and, importantly, to generate data keys as well.
And as you'll remember, generating data keys here is the basis of envelope encryption. And
again, this applies to all resources. Now here's how instead of a user being specified as a principal, we can actually
give these permissions to any user with the IAM role myapp using principal :
<pre>   "AWS": "arn:aws:iam::111111111111:role/myapprole"</pre>. So this could apply to any user who has this role.
And IAM best practice is always to use roles whenever possible.
<pre>
        {
            "Sid": "Allow use of the key",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::111111111111:user/myapp"
            },
            "Action": [
                "kms:Encrypt",
                "kms:Decrypt",
                "kms:ReEncrypt*",
                "kms:GenerateDataKey*",
                "kms:DescribeKey"
            ],
            "Resource": "*"
        }
</pre>

 And in this
example, we're allowing access to a user, a role, and another AWS account. example:
<pre>
"Principal": {
        "AWS": [
            "arn:aws:iam::111111111111:user/myapp",
            "arn:aws:iam::111111111111:role/myapprole",
            "arn:aws:iam::222222222222:root"
        ]
    }
</pre> 

Now we have this statement allowing
attachment of persistent resources. So what we mean by that is the ability to create and revoke grants, which allow you
to programmatically allow access to your CMK to other principles. So in this case again, the effect is allow, the list
of actions this time is creating, listing, and revoking grants on all resources with the condition that the grant is for
an AWS resource that uses grants. So notice this condition here. It's pretty straightforward to read and understand what
this is saying, but just know that you can always attach conditions to these policies. Just like we used a condition in
the S3 bucket policy to enforce encryption in transit, we can always use conditions in conjunction with our policies. So
grants are especially useful when you need to grant temporary access to a CMK, and this is usually done programmatically
in code. You can just call CreateGrant, specify the CMK, the principal to which you are granting access and the allowed
operation or set of operations. And when you're done, you can call RevokeGrant, and the access goes away. 
<pre>
        {
            "Sid": "Allow attachment of persistent resources",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::111111111111:user/myapp"
            },
            "Action": [
                "kms:CreateGrant",
                "kms:ListGrants",
                "kms:RevokeGrant"
            ],
            "Resource": "*",
            "Condition": {
                "Bool": {
                    "kms:GrantIsForAWSResource": "true"
                }
            }
        }
</pre>

## Persistent Store

AWS Systems Manager Parameter Store provides secrets management. You can store data such as passwords, database strings,
and license codes as parameter values. You can store values as plain text or encrypted data. You can then reference
values by using the unique name that you specified when you created the parameter.

The AWS Systems Manager Parameter Store, which you'll sometimes see referred to as the SSM Parameter Store (and SSM
stands for **Simple Systems Manager**, that's an old name for the AWS Systems Manager, but the acronym still lives on),
offers a centralized place to store and manage your secrets. So instead of hardcoding your parameter value - such as 
passwords, database strings, and license codes, your  application will call Parameter Store to get that value instead. 
You can store values as plain text or encrypted data. You can then reference values by using the unique name that you
specified when you created the parameter.
**Note** that Parameter Store is just one small offering within AWS Systems Manager

You can store up to 10,000 secrets per region, each one up to 4 KB in size within its standard tier. There is also an
advanced tier that scales up to 100,000 secrets up to 8 KB each. But there is a per‑parameter cost associated with that.
Access to Parameter Store is controlled through IAM. So it's important that you configure the proper IAM roles within
your account for EC2 or Lambda, for instance, depending on where your application is running so that you will be able to
access these parameters. Parameter Store allows you to store secrets as plaintext strings or lists of strings, and these
are good for secrets that you don't want to store in your code but maybe aren't too sensitive in nature. But for more
sensitive secrets, so maybe for something like a privileged account password or something that requires an additional
layer of protection, we can use something called a SecureString parameter. And SecureString parameters are actually
encrypted using keys managed in KMS

Sample AWS Cli command
----------------------
- aws ssm get-parameter - name “/dev/dbconnectionstring”
- aws ssm get-parameter - name “/dev/dbconnectionstring” --with-decryption(KMS key encrypted), this should have the role to 
access kms keys so the value can be decrypted.

**Note:** IAM role will require ssm:GetParameters permissions (optionally, also kms:Decrypt if you use SecureString params).

Useful links:
-----------
- https://github.com/alexcasalboni/ssm-cache-python
- https://medium.com/@whaleberry/tips-for-storing-secrets-with-aws-ssm-parameter-store-d70a4a42c64