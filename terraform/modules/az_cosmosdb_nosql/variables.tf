variable "name" {
  type = string
}

variable "location" {
  type = string
}

variable "resource_group" {
  type = string
}

variable "total_throughput_limit" {
  type = number
}

variable "enable_free_tier" {
  type = bool
}

variable "geo_location" {
  type    = list(string)
  default = null
}

variable "subnet_id" {
  type = string
}

variable "enable_multiple_write_locations" {
  type = bool
}

variable "enable_serverless" {
  type = bool
}

variable "key_vault_key_id" {
  type    = string
  default = ""
}

variable "backup_type" {
  type = string
}

variable "interval_in_minutes" {
  type    = number
  default = 60
}

variable "retention_in_hours" {
  type    = number
  default = 8
}

variable "storage_redundancy" {
  type = string
}


variable "ip_range_filter" {
  type = string
}

variable "identity_type" {
  type = string
}

variable "identity_ids" {
  type    = list(string)
  default = []
}

variable "database_name" {
  type = string
}

variable "containers" {
  description = "A list of containers be created."
  type = list(object({
    container_name = string
    partition_key  = string
    unique_key     = string
  }))
  default = null
}

