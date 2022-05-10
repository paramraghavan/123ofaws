# Terraform

Terraform Object Types
----------------------
1. Providers - in our case AWS, could be Azure or GCP
2. Resources - ec2 instances, database etc
3. Data sources - are based are on provider - could be a list of AZ’s in a region, AMI’s that can be used, etc


Terraform Block syntax
- JSON like syntax with provision to add comments, where label name is provider specific and name_label is the alias. ￼
<pre>
   block_type "label"  "name_label" {
        key = "value"
        nested_block {
              key = "value"
        }
   }
</pre>

 - Build/Deploy Steps
--------------------
- terraform init —> pulls provider plugin If need be, get current state info of the resources
- terraform plan —> prepares the plan to update the target
- terraform apply —> applies terraform plan, resources created and state data updated - creates or updates the target environment.
- terraform destroy —>  destroys target env
- only run for one particular resource, terraform plan -target=resource_label.resource_name_label, [ref](https://jhooq.com/terraform-run-specific-resource/).
  "terraform plan" will print a list of modules on  run completion.

Input Output Variables
----------------------
- [input variable](https://www.terraform.io/language/values/variables). Input variables are like function arguments. You
can add validation rule for input variables.
- input variable example: 
 <pre>
    variable "image_id" {
      type = string
    }
    
    variable "availability_zone_names" {
      type    = list(string)
      default = ["us-west-1a"]
    }
    
    variable "docker_ports" {
      type = list(object({
        internal = number
        external = number
        protocol = string
      }))
      default = [
        {
          internal = 8300
          external = 8300
          protocol = "tcp"
        }
      ]
    }
<</pre>
- [output variables](https://www.terraform.io/language/values/outputs). Output values are like function return values. Outputs are only rendered when Terraform applies your plan. Running terraform plan will not render outputs. 
- example : 
<pre>
    output "instance_ip_addr" {
      value = aws_instance.server.private_ip
    }
</pre>

- [local variables](https://www.terraform.io/language/values/locals). Local values are like a function's temporary local
  variables. A set of related local values can be declared together in a single locals block.
  Local values can be helpful to avoid repeating the same values or expressions multiple times in a configuration, but
  if overused they can also make a configuration hard to read by future maintainers by hiding the actual values used.
  Use local values only in moderation, in situations where a single value or result is used in many places and that
  value is likely to be changed in future. The ability to easily change the value in a central place is the key
  advantage of local values.
- example 
<pre>
locals {
  service_name = "forum"
  owner        = "Community Team"
  # Ids for multiple sets of EC2 instances, merged together
  instance_ids = concat(aws_instance.blue.*.id, aws_instance.green.*.id)
  # Common tags to be assigned to all resources
  common_tags = {
    Service = local.service_name
    Owner   = local.owner
  }
}

</pre>



Useful Links
--------------
- https://registry.terraform.io/providers/hashicorp/aws/latest/docs
- https://github.com/ned1313/Getting-Started-Terraform
